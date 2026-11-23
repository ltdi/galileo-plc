(* Ejemplo de alumno: salida intermitente con dos temporizadores (1 s encendido, 3 s apagado)
   y un pulsador virtual (coil 1) que lo habilita. *)
PROGRAM prog0
  VAR
    salida AT %QX0.0 : BOOL;
    habilitar AT %QX0.1 : BOOL;
    ciclos AT %MW0 : INT;
  END_VAR
  VAR
    encendida : BOOL := FALSE;
    t_on : TON;
    t_off : TON;
  END_VAR

  IF habilitar THEN
    t_off(IN := NOT encendida AND NOT t_on.Q, PT := T#3s);
    IF t_off.Q THEN encendida := TRUE; END_IF;
    t_on(IN := encendida, PT := T#1s);
    IF t_on.Q THEN encendida := FALSE; ciclos := ciclos + 1; END_IF;
  ELSE
    encendida := FALSE;
    t_on(IN := FALSE, PT := T#1s);
    t_off(IN := FALSE, PT := T#3s);
  END_IF;
  salida := encendida;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM instance0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
