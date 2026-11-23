(* Programa de fabrica: SALIDAS SIEMPRE APAGADAS.
   Es lo que corre la placa al encenderse hasta que se cargue otro programa. No hace nada a proposito: ninguna
   salida se activa por si sola ni por una escritura Modbus (el programa las reescribe en FALSE en cada ciclo de 20 ms).
   Para probar la placa se usa el panel en vivo (http://127.0.0.1:8088): ver las entradas y FORZAR salidas o entradas. *)
PROGRAM main
  VAR
    q0 AT %QX0.0 : BOOL;   (* D8  *)
    q1 AT %QX0.1 : BOOL;   (* D9  *)
    q2 AT %QX0.2 : BOOL;   (* D10 *)
    q3 AT %QX0.3 : BOOL;   (* D11 *)
  END_VAR
  q0 := FALSE;
  q1 := FALSE;
  q2 := FALSE;
  q3 := FALSE;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
