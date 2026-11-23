(* Prueba de E/S: cada salida sigue a un bit de memoria (registros 1024..1027 por Modbus) *)
PROGRAM prog0
  VAR
    q0 AT %QX0.0 : BOOL; q1 AT %QX0.1 : BOOL; q2 AT %QX0.2 : BOOL; q3 AT %QX0.3 : BOOL;
    m0 AT %MW0 : INT; m1 AT %MW1 : INT; m2 AT %MW2 : INT; m3 AT %MW3 : INT;
  END_VAR
  q0 := m0 <> 0; q1 := m1 <> 0; q2 := m2 <> 0; q3 := m3 <> 0;
END_PROGRAM
CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM inst0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
