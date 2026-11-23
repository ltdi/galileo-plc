(* Ascensor de 3 pisos para la placa de 8 entradas / 4 salidas: 3 llamadas, 3 sensores de piso, emergencia,
   puerta cerrada; salidas: subir, bajar, abrir puerta, luz de en-movimiento. *)
PROGRAM prog0
  VAR
    llam1 AT %IX0.0 : BOOL; llam2 AT %IX0.1 : BOOL; llam3 AT %IX0.2 : BOOL;
    s1 AT %IX0.3 : BOOL; s2 AT %IX0.4 : BOOL; s3 AT %IX0.5 : BOOL;
    emerg AT %IX0.6 : BOOL; puerta_cerrada AT %IX0.7 : BOOL;
    subir AT %QX0.0 : BOOL; bajar AT %QX0.1 : BOOL; abrir AT %QX0.2 : BOOL;
    movimiento AT %QX0.3 : BOOL;
    viajes AT %MW0 : INT;
  END_VAR
  VAR
    destino : INT := 0; piso : INT := 1;
    p1 : BOOL; p2 : BOOL; p3 : BOOL;
    t_puerta : TON; t_max : TON; r1 : R_TRIG; r2 : R_TRIG; r3 : R_TRIG;
  END_VAR
  IF s1 THEN piso := 1; END_IF; IF s2 THEN piso := 2; END_IF; IF s3 THEN piso := 3; END_IF;
  r1(CLK := llam1); r2(CLK := llam2); r3(CLK := llam3);
  IF r1.Q THEN p1 := TRUE; END_IF; IF r2.Q THEN p2 := TRUE; END_IF; IF r3.Q THEN p3 := TRUE; END_IF;
  IF destino = 0 THEN
    IF p1 THEN destino := 1; ELSIF p2 THEN destino := 2; ELSIF p3 THEN destino := 3; END_IF;
  END_IF;
  subir := (destino > piso) AND puerta_cerrada AND NOT emerg;
  bajar := (destino <> 0) AND (destino < piso) AND puerta_cerrada AND NOT emerg;
  t_max(IN := subir OR bajar, PT := T#20s);
  IF t_max.Q THEN destino := 0; END_IF;
  t_puerta(IN := (destino = piso) AND destino <> 0, PT := T#4s);
  abrir := (destino = piso) AND destino <> 0 AND NOT t_puerta.Q;
  IF t_puerta.Q THEN
    IF piso = 1 THEN p1 := FALSE; END_IF; IF piso = 2 THEN p2 := FALSE; END_IF; IF piso = 3 THEN p3 := FALSE; END_IF;
    destino := 0; viajes := viajes + 1;
  END_IF;
  movimiento := subir OR bajar;
END_PROGRAM
CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM inst0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
