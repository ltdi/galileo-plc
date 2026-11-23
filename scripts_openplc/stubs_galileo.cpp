// Stubs para lo que se deja fuera de la version Galileo: snap7 (S7) y maestro Modbus.
// (DNP3 se anexa desde dnp3_dummy.disabled de OpenPLC.)
#include "ladder.h"

// snap7 / S7
void initializeSnap7() {}
void finalizeSnap7() {}
void startSnap7() {}
void stopSnap7() {}

// Maestro Modbus (necesita libmodbus): desactivado en esta version
void initializeMB() {}
void updateBuffersIn_MB() {}
void updateBuffersOut_MB() {}

