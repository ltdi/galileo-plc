/* Rescate tras un reinicio: red (MAC de la etiqueta + DHCP) y telnetd 6 h. Se sube como sketch con clupload. */
#include <stdlib.h>
#include <unistd.h>
int main(void) {
    system("ifconfig eth0 down; ifconfig eth0 hw ether 98:4f:ee:00:fa:94; ifconfig eth0 up");
    sleep(4);
    system("udhcpc -i eth0 -n -q -t 5 -T 3 > /dev/null 2>&1");
    system("killall telnetd 2>/dev/null; telnetd -b 10.42.0.151 -p 23");
    system("dmesg > /tmp/dmesg_rescate.txt; cp /proc/uptime /tmp/uptime_rescate.txt");
    sleep(21600);
    system("killall telnetd");
    return 0;
}
