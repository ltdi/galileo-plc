// Capa de hardware de OpenPLC para la Galileo Gen1 (FAB-D) -- version 2: 8 entradas y 4 salidas.
// Misma interfaz que hardware_layers/blank.cpp de OpenPLC v3 (4 funciones).
// Pensada para la placa de expansion del proyecto (8 entradas aisladas + 4 salidas a rele).
//
//   %IX0.0..%IX0.7  entradas  D2 D3 D4 D5 D6 D7 D12 D13   (TRUE = nivel bajo en el pin: contacto/opto a GND)
//   %QX0.0..%QX0.3  salidas   D8 D9 D10 D11               (activas en nivel ALTO)
//
// Se evitan D0/D1 (puerto serie) y A0-A5 (analogicas). Cada pin se traduce a su GPIO de Linux segun
// variant.cpp de la Galileo FAB-D: D4..D9 son GPIO directos del SoC; D2/D3 hay que enrutarlos al SoC
// (gpio31/gpio30 en bajo) y activar su pull-up (gpio0/gpio1 en alto); D10..D13 comparten pin con el
// SPI y se pasan a GPIO con un mux (gpio42/43/54/55 en alto).
// Todo con sysfs y descriptores abiertos (pread/pwrite), idempotente.
#include "ladder.h"
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>


struct Pin { int gpio; int mux; int mux_nivel; int pullup; };   // mux/pullup = -1 si no hay
//                 gpio  mux  nivel  pullup
static const Pin ENT[8] = {
    { 14, 31, 0,  0 },   // D2   %IX0.0
    { 15, 30, 0,  1 },   // D3   %IX0.1
    { 28, -1, 0, -1 },   // D4   %IX0.2
    { 17, -1, 0, -1 },   // D5   %IX0.3
    { 24, -1, 0, -1 },   // D6   %IX0.4
    { 27, -1, 0, -1 },   // D7   %IX0.5
    { 38, 54, 1, -1 },   // D12  %IX0.6
    { 39, 55, 1, -1 },   // D13  %IX0.7
};
static const Pin SAL[4] = {
    { 26, -1, 0, -1 },   // D8   %QX0.0
    { 19, -1, 0, -1 },   // D9   %QX0.1
    { 16, 42, 1, -1 },   // D10  %QX0.2
    { 25, 43, 1, -1 },   // D11  %QX0.3
};
// ---- Forzado de entradas y salidas desde el panel en vivo ------------------------------------------------
// Cuatro registros Modbus reservados (holding registers 2024..2027 = %MW1000..%MW1003): mascara y valor de las 8 entradas
// y mascara y valor de las 4 salidas. Un bit en la mascara fuerza ese punto al valor indicado, haga lo que haga el
// programa. Se limpian en los primeros segundos tras arrancar (la memoria retentiva podria restaurar un forzado viejo).
extern IEC_UINT mb_holding_regs[];
#define REG_FORZ      2024
#define F_ENT_MASC    (mb_holding_regs[REG_FORZ + 0])
#define F_ENT_VAL     (mb_holding_regs[REG_FORZ + 1])
#define F_SAL_MASC    (mb_holding_regs[REG_FORZ + 2])
#define F_SAL_VAL     (mb_holding_regs[REG_FORZ + 3])
static time_t t_arranque = 0;
static void forzado_limpiar_si_reciente(void)
{
    if (t_arranque == 0) t_arranque = time(NULL);
    if (time(NULL) - t_arranque < 8) { F_ENT_MASC = F_ENT_VAL = F_SAL_MASC = F_SAL_VAL = 0; }
}
static int fd_ent[8], fd_sal[4];
static int sal_actual[4] = { -1, -1, -1, -1 };

static int escribir_archivo(const char *ruta, const char *valor)
{
    int fd = open(ruta, O_WRONLY);
    if (fd < 0) return -1;
    int r = write(fd, valor, strlen(valor));
    close(fd);
    return r < 0 ? -1 : 0;
}

static void gpio_exportar(int n)
{
    char ruta[64], num[12];
    snprintf(ruta, sizeof(ruta), "/sys/class/gpio/gpio%d", n);
    struct stat st;
    if (stat(ruta, &st) != 0) {
        snprintf(num, sizeof(num), "%d", n);
        escribir_archivo("/sys/class/gpio/export", num);
    }
}

// dir: "in" o "out"
static void gpio_direccion(int n, const char *dir)
{
    char ruta[64];
    gpio_exportar(n);
    snprintf(ruta, sizeof(ruta), "/sys/class/gpio/gpio%d/direction", n);
    if (escribir_archivo(ruta, dir) != 0)
        printf("Galileo: no se pudo poner gpio%d en '%s' (%s)\n", n, dir, strerror(errno));
}

// Salida con nivel inicial explicito: en esta placa echo low/high > direction NO fija el nivel,
// hay que poner direction=out y escribir value aparte (igual que el core de Arduino).
static void gpio_salida(int n, int nivel)
{
    char ruta[64];
    gpio_direccion(n, "out");
    snprintf(ruta, sizeof(ruta), "/sys/class/gpio/gpio%d/value", n);
    escribir_archivo(ruta, nivel ? "1" : "0");
}

static int gpio_abrir_valor(int n, int flags)
{
    char ruta[64];
    snprintf(ruta, sizeof(ruta), "/sys/class/gpio/gpio%d/value", n);
    int fd = open(ruta, flags);
    if (fd < 0) printf("Galileo: no se pudo abrir %s (%s)\n", ruta, strerror(errno));
    return fd;
}

static int gpio_leer(int fd)
{
    char c = '1';
    if (fd < 0) return 1;
    if (pread(fd, &c, 1, 0) != 1) return 1;
    return c == '1';
}

// --- Instrumentacion del scan: periodo real entre dos llamadas a updateBuffersIn() y tiempo de E/S.
// Cada 60 s escribe una linea "SCAN ..." en el log (con fflush) y reinicia los contadores.
static struct timespec t_ant;
static int  primera = 1;
static long n_per = 0, sum_per = 0, min_per = 1L << 30, max_per = 0, sobre25 = 0, sobre30 = 0;
static long max_es = 0;
static time_t t_rep = 0;

static long dif_us(const struct timespec &a, const struct timespec &b)
{
    return (a.tv_sec - b.tv_sec) * 1000000L + (a.tv_nsec - b.tv_nsec) / 1000L;
}

static void estad_scan_entrada()
{
    struct timespec ahora;
    clock_gettime(CLOCK_MONOTONIC, &ahora);
    if (!primera) {
        long p = dif_us(ahora, t_ant);
        n_per++; sum_per += p;
        if (p < min_per) min_per = p;
        if (p > max_per) max_per = p;
        if (p > 25000) sobre25++;
        if (p > 30000) sobre30++;
    }
    primera = 0;
    t_ant = ahora;
    if (t_rep == 0) t_rep = ahora.tv_sec;
    if (ahora.tv_sec - t_rep >= 60 && n_per > 0) {
        printf("SCAN %ld ciclos: periodo us min/prom/max = %ld/%ld/%ld; >25ms: %ld; >30ms: %ld; E/S max us: %ld\n",
               n_per, min_per, sum_per / n_per, max_per, sobre25, sobre30, max_es);
        fflush(stdout);
        n_per = 0; sum_per = 0; min_per = 1L << 30; max_per = 0; sobre25 = 0; sobre30 = 0; max_es = 0;
        t_rep = ahora.tv_sec;
    }
}

static void estad_es(const struct timespec &ini)
{
    struct timespec fin;
    clock_gettime(CLOCK_MONOTONIC, &fin);
    long d = dif_us(fin, ini);
    if (d > max_es) max_es = d;
}

// Los GPIO 16..55 son del expansor Cypress CY8C9540A (I2C 0x20). Numeracion de Linux (esquematico, U8):
// puerto 0 = gpio16..23, puerto 1 = 24..31, puerto 2 (solo 4 bits) = 32..35, puerto 3 = 36..43,
// puerto 4 = 44..51, puerto 5 (4 bits) = 52..55. Ej.: D12 = gpio38 = puerto 3 bit 2; D10 = gpio16 = puerto 0 bit 0.
// En la Galileo sus entradas quedan en modo alta impedancia (flotantes: se leen como 0 sin nada conectado).
// Se les pone pull-up resistivo (reg 0x1D) y se las saca de alta impedancia (reg 0x23). Solo RAM del Cypress.
static int cy_leer(int fd, unsigned char reg, unsigned char *v)
{
    return write(fd, &reg, 1) == 1 && read(fd, v, 1) == 1;
}

// Pone pull-up resistivo y saca de alta impedancia, y VERIFICA leyendo de vuelta; reintenta hasta 12 veces (50 ms) y avisa si no lo logra.
// En el arranque las primeras transacciones I2C pueden perderse: sin verificar, D4 y D5 quedaban flotando.
static void cy_pullup(int gpio)
{
    if (gpio < 16 || gpio > 55) return;
    int g = gpio - 16, puerto, nbit;
    if (g < 16) { puerto = g / 8; nbit = g % 8; }
    else if (g < 20) { puerto = 2; nbit = g - 16; }
    else { puerto = 3 + (g - 20) / 8; nbit = (g - 20) % 8; }
    int bit = 1 << nbit;
    int fd = open("/dev/i2c-0", O_RDWR);
    if (fd < 0) return;
    if (ioctl(fd, I2C_SLAVE_FORCE, 0x20) == 0) {
        int logrado = 0;
        for (int intento = 0; intento < 12 && !logrado; intento++) {
            unsigned char sel[2] = { 0x18, (unsigned char)puerto }, v = 0, pu = 0, hz = 0;
            if (write(fd, sel, 2) == 2 && cy_leer(fd, 0x1D, &pu) && cy_leer(fd, 0x23, &hz)) {
                if ((pu & bit) && !(hz & bit)) { logrado = 1; continue; }   // ya esta como se quiere
                unsigned char w[2] = { 0x1D, (unsigned char)(pu | bit) };
                if (write(fd, w, 2) == 2) {
                    if (cy_leer(fd, 0x23, &v)) { unsigned char w2[2] = { 0x23, (unsigned char)(v & ~bit) }; write(fd, w2, 2); }
                }
            }
            if (!logrado) usleep(50000);
        }
        if (!logrado) printf("Galileo: aviso: no se pudo verificar el pull-up de gpio%d\n", gpio);
    }
    close(fd);
}

void initializeHardware()
{
    int i;
    for (i = 0; i < 4; i++) {
        if (SAL[i].mux >= 0) gpio_salida(SAL[i].mux, SAL[i].mux_nivel);
        gpio_salida(SAL[i].gpio, 0);                       // arrancar siempre en nivel inactivo
        fd_sal[i] = gpio_abrir_valor(SAL[i].gpio, O_WRONLY);
        sal_actual[i] = 0;
    }
    for (i = 0; i < 8; i++) {
        if (ENT[i].mux >= 0) gpio_salida(ENT[i].mux, ENT[i].mux_nivel);
        if (ENT[i].pullup >= 0) gpio_salida(ENT[i].pullup, 1);
        gpio_direccion(ENT[i].gpio, "in");
        cy_pullup(ENT[i].gpio);
        fd_ent[i] = gpio_abrir_valor(ENT[i].gpio, O_RDONLY);
    }
    printf("Galileo: E/S lista (8 entradas, 4 salidas)\n");
}

void finalizeHardware()
{
    for (int i = 0; i < 4; i++) {
        if (fd_sal[i] >= 0) { pwrite(fd_sal[i], "0", 1, 0); close(fd_sal[i]); }   // salidas a inactivo
    }
    for (int i = 0; i < 8; i++) if (fd_ent[i] >= 0) close(fd_ent[i]);
}

void updateBuffersIn()
{
    estad_scan_entrada();
    struct timespec ini;
    clock_gettime(CLOCK_MONOTONIC, &ini);
    pthread_mutex_lock(&bufferLock);
    forzado_limpiar_si_reciente();
    for (int i = 0; i < 8; i++)
        if (bool_input[0][i] != NULL) {
            *bool_input[0][i] = !gpio_leer(fd_ent[i]);   // nivel bajo = TRUE
            if (F_ENT_MASC >> i & 1) *bool_input[0][i] = (F_ENT_VAL >> i) & 1;   // forzado desde el panel
        }
    pthread_mutex_unlock(&bufferLock);
    estad_es(ini);
}

void updateBuffersOut()
{
    struct timespec ini;
    clock_gettime(CLOCK_MONOTONIC, &ini);
    pthread_mutex_lock(&bufferLock);
    for (int i = 0; i < 4; i++) {
        if (bool_output[0][i] == NULL || fd_sal[i] < 0) continue;
        if (F_SAL_MASC >> i & 1) *bool_output[0][i] = (F_SAL_VAL >> i) & 1;      // forzado desde el panel
        int n = *bool_output[0][i] ? 1 : 0;
        if (n != sal_actual[i]) { pwrite(fd_sal[i], n ? "1" : "0", 1, 0); sal_actual[i] = n; }
    }
    pthread_mutex_unlock(&bufferLock);
    estad_es(ini);
}
