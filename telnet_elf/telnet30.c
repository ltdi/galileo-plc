/* Abre telnetd 30 min (acceso de laboratorio, sin clave) y lo apaga. Se sube como sketch con clupload. */
#include <stdlib.h>
#include <unistd.h>
int main(void) {
    system("killall yes 2>/dev/null; telnetd -b 10.42.0.151 -p 23");
    sleep(1800);
    system("killall telnetd");
    return 0;
}
