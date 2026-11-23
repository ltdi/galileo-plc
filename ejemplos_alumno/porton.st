(* Porton automatico: pulsador/control, fines de carrera, fotocelula, luz de aviso, cierre automatico *)
PROGRAM prog0
  VAR
    pulsador AT %IX0.0 : BOOL; fc_abierto AT %IX0.1 : BOOL; fc_cerrado AT %IX0.2 : BOOL;
    fotocelula AT %IX0.3 : BOOL;
    abrir AT %QX0.0 : BOOL; cerrar AT %QX0.1 : BOOL; luz AT %QX0.2 : BOOL;
    ciclos AT %MW0 : INT;
  END_VAR
  VAR
    estado : INT := 0; r : R_TRIG; t_esp : TON; t_max : TON;
  END_VAR
  r(CLK := pulsador);
  CASE estado OF
    0: IF r.Q THEN estado := 1; END_IF;
    1: IF fc_abierto THEN estado := 2; END_IF; IF t_max.Q THEN estado := 4; END_IF;
    2: IF t_esp.Q THEN estado := 3; END_IF; IF r.Q THEN estado := 3; END_IF;
    3: IF fotocelula THEN estado := 1; END_IF; IF fc_cerrado THEN estado := 0; ciclos := ciclos + 1; END_IF; IF t_max.Q THEN estado := 4; END_IF;
    4: IF r.Q THEN estado := 0; END_IF;
  END_CASE;
  t_esp(IN := estado = 2, PT := T#10s);
  t_max(IN := estado = 1 OR estado = 3, PT := T#30s);
  abrir := estado = 1; cerrar := estado = 3;
  luz := (estado = 1) OR (estado = 3) OR (estado = 4);
END_PROGRAM
CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM inst0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
