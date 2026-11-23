(* Arranque directo de un motor con enclavamiento (marcha / paro) y rele termico.
   Cableado: pulsador de MARCHA (normal abierto) a D2; pulsador de PARO (normal CERRADO) a D3; contacto del termico
   (normal CERRADO) a D4; las entradas se activan al cerrarse a GND, asi que PARO y TERMICO estan en 1 en reposo
   (si un cable se corta, el motor se detiene: logica de falla segura). KM1 (contactor) en D8; luz de falla en D9. *)
PROGRAM main
  VAR
    marcha AT %IX0.0 : BOOL;     (* D2  pulsador NA *)
    paro_nc AT %IX0.1 : BOOL;    (* D3  pulsador NC: 1 = sin pulsar *)
    termico_nc AT %IX0.2 : BOOL; (* D4  contacto NC del termico: 1 = sin disparo *)
    km1 AT %QX0.0 : BOOL;        (* D8  contactor del motor *)
    falla AT %QX0.1 : BOOL;      (* D9  piloto de falla de termico *)
  END_VAR
  km1 := (marcha OR km1) AND paro_nc AND termico_nc;
  falla := NOT termico_nc;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
