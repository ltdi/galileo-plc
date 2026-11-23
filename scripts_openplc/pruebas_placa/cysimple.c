/* cysimple: lee dir/pull-up/strong/hi-z de los puertos 0,1,3 del Cypress con lecturas simples (sin inicio repetido). */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
static int fd;
static int rd1(int r) { unsigned char c = r, v = 0xEE; if (write(fd, &c, 1) != 1) return -1; if (read(fd, &v, 1) != 1) return -2; return v; }
int main(void) {
    int p, ports[3] = {0, 1, 3}, k;
    fd = open("/dev/i2c-0", O_RDWR); if (fd < 0) { perror("open"); return 1; }
    ioctl(fd, I2C_SLAVE_FORCE, 0x20);
    printf("IN  P0 %02x P1 %02x P3 %02x\n", rd1(0), rd1(1), rd1(3));
    for (k = 0; k < 3; k++) {
        unsigned char s[2] = { 0x18, ports[k] }; p = ports[k];
        write(fd, s, 2);
        printf("P%d dir=%02x pullup=%02x strong=%02x hiz=%02x\n", p, rd1(0x1C), rd1(0x1D), rd1(0x21), rd1(0x23));
    }
    return 0;
}
