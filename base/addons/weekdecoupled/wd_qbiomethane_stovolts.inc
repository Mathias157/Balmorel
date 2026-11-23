* WeekDecoupled add-on (docs/adr/0006): the last time step links to the week's own first time step
   + (SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VBIOMETHSTOVOLTS(IY411,S,ITALIAS)) - SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VBIOMETHSTOVOLTS(IY411,S++1,ITALIAS)))$(CARD(T) EQ ORD(T))
