/* cyvolcado: vuelca los registros del expansor Cypress CY8C9540A (I2C 0x20) con transacciones de inicio repetido
   (como el kernel). Solo escribe el selector de puerto (0x18). Conviene congelar OpenPLC (kill -STOP) mientras corre. */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>
static int fd;
static int leer(int reg, unsigned char *b, int n) {
    unsigned char r = reg; struct i2c_msg m[2]; struct i2c_rdwr_ioctl_data d;
    m[0].addr = 0x20; m[0].flags = 0; m[0].len = 1; m[0].buf = &r;
    m[1].addr = 0x20; m[1].flags = I2C_M_RD; m[1].len = n; m[1].buf = b;
    d.msgs = m; d.nmsgs = 2;
    return ioctl(fd, I2C_RDWR, &d) < 0 ? -1 : n;
}
int main(void) {
    unsigned char b[16]; int p, i;
    fd = open("/dev/i2c-0", O_RDWR); if (fd < 0) { perror("open"); return 1; }
    ioctl(fd, I2C_SLAVE_FORCE, 0x20);
    if (leer(0x00, b, 6) == 6) { printf("INPUT  0x00..05:"); for (i = 0; i < 6; i++) printf(" %02x", b[i]); printf("\n"); } else printf("INPUT: error\n");
    if (leer(0x08, b, 6) == 6) { printf("OUTPUT 0x08..0D:"); for (i = 0; i < 6; i++) printf(" %02x", b[i]); printf("\n"); } else printf("OUTPUT: error\n");
    if (leer(0x2e, b, 1) == 1) printf("DEVICE ID/STATUS 0x2E: %02x\n", b[0]);
    printf("puerto: mask(19) selPWM(1A) inv(1B) dir(1C) pullup(1D) pulldn(1E) odhigh(1F) odlow(20) strong(21) slow(22) hiz(23)\n");
    for (p = 0; p < 6; p++) {
        unsigned char s[2] = { 0x18, p };
        write(fd, s, 2);
        if (leer(0x19, b, 11) != 11) { printf("  P%d: error de lectura\n", p); continue; }
        printf("  P%d:", p); for (i = 0; i < 11; i++) printf(" %02x", b[i]); printf("\n");
    }
    return 0;
}
