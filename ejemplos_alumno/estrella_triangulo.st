(* Arranque estrella-triangulo de un motor trifasico.
   Entradas: MARCHA (NA) D2, PARO (NC) D3, termico (NC) D4.  Salidas: KM1 linea D8, KM2 estrella D9, KM3 triangulo D10.
   Al dar MARCHA: KM1 + KM2 (estrella) durante T_ESTRELLA; luego KM2 suelta, pausa de T_MUERTO y entra KM3 (triangulo).
   KM2 y KM3 estan enclavados por programa (y deben estarlo ademas por cableado, con contactos NC en serie). *)
PROGRAM main
  VAR
    marcha AT %IX0.0 : BOOL;
    paro_nc AT %IX0.1 : BOOL;
    termico_nc AT %IX0.2 : BOOL;
    km1 AT %QX0.0 : BOOL;
    km2 AT %QX0.1 : BOOL;
    km3 AT %QX0.2 : BOOL;
  END_VAR
  VAR
    en_marcha : BOOL := FALSE;
    t_estrella : TON;
    t_muerto : TON;
  END_VAR
  en_marcha := (marcha OR en_marcha) AND paro_nc AND termico_nc;
  t_estrella(IN := en_marcha, PT := T#5s);
  t_muerto(IN := t_estrella.Q, PT := T#100ms);
  km1 := en_marcha;
  km2 := en_marcha AND NOT t_estrella.Q AND NOT km3;
  km3 := en_marcha AND t_muerto.Q AND NOT km2;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
