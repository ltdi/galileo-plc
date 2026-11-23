(* Inversion de giro con enclavamiento: ADELANTE y ATRAS no pueden estar activos a la vez, y para invertir hay que parar.
   Entradas: ADELANTE (NA) D2, ATRAS (NA) D3, PARO (NC) D4, termico (NC) D5. Salidas: KM_adelante D8, KM_atras D9. *)
PROGRAM main
  VAR
    adelante AT %IX0.0 : BOOL;
    atras AT %IX0.1 : BOOL;
    paro_nc AT %IX0.2 : BOOL;
    termico_nc AT %IX0.3 : BOOL;
    km_adelante AT %QX0.0 : BOOL;
    km_atras AT %QX0.1 : BOOL;
  END_VAR
  km_adelante := (adelante OR km_adelante) AND NOT km_atras AND paro_nc AND termico_nc;
  km_atras := (atras OR km_atras) AND NOT km_adelante AND paro_nc AND termico_nc;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
