/* iotest: mide cuanto tarda leer los puertos de entrada del expansor Cypress CY8C9540A (I2C, 0x20)
   en una sola transaccion, frente al ~2,2 ms por pin que cuesta la lectura por sysfs. Solo LEE. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

static long us(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000000L + t.tv_nsec / 1000L; }

int main(void) {
    int fd = open("/dev/i2c-0", O_RDWR);
    if (fd < 0) { perror("open /dev/i2c-0"); return 1; }
    if (ioctl(fd, I2C_SLAVE_FORCE, 0x20) < 0) { perror("I2C_SLAVE_FORCE"); return 1; }
    unsigned char reg, buf[8];
    int largos[] = {1, 6};
    for (int k = 0; k < 2; k++) {
        int n = largos[k], N = 500;
        long t0 = us(), mn = 1 << 30, mx = 0;
        for (int i = 0; i < N; i++) {
            long a = us();
            reg = 0x00;                         /* registro "Input Port 0" */
            if (write(fd, &reg, 1) != 1) { perror("write"); return 1; }
            if (read(fd, buf, n) != n) { perror("read"); return 1; }
            long d = us() - a;
            if (d < mn) mn = d; if (d > mx) mx = d;
        }
        long tot = us() - t0;
        printf("lectura de %d byte(s): promedio %ld us, minimo %ld us, maximo %ld us (N=%d)\n", n, tot / N, mn, mx, N);
    }
    printf("puertos 0..5 (entradas): ");
    reg = 0x00; write(fd, &reg, 1); read(fd, buf, 6);
    for (int i = 0; i < 6; i++) printf("%02x ", buf[i]);
    printf("\n");
    close(fd);
    return 0;
}
