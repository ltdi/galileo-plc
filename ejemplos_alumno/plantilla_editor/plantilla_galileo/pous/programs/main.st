PROGRAM main
  VAR
    (* Entradas: D2 D3 D4 D5 D6 D7 D12 D13  ->  %IX0.0 ... %IX0.7 (TRUE = contacto a GND) *)
    pulsador AT %IX0.0 : BOOL;
    (* Salidas: D8 D9 D10 D11  ->  %QX0.0 ... %QX0.3 *)
    luz AT %QX0.0 : BOOL;
  END_VAR
  luz := pulsador;
END_PROGRAM
