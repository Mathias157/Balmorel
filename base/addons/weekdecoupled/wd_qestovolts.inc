* WeekDecoupled add-on (docs/adr/0006): the last time step links to the week's own first time step
   + (SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VESTOVOLTS(IY411,IA,IGESTOS,S,ITALIAS)) - SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VESTOVOLTS(IY411,IA,IGESTOS,S++1,ITALIAS)))$(CARD(T) EQ ORD(T))
