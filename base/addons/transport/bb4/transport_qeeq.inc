* Transport add-on. Added by Juan Gea Bermudez

*adding electricity demand from transport
$ifi %TRANSPORT_SYNTHFUEL_COMMODITY%==ELECTRICITY  +VTRANSDEMAND_T(IY411,IR,IS3,T)$(TRANSDEMAND_Y(IY411,IR)
$ifi %TRANSPORT_SYNTHFUEL_COMMODITY%==ELECTRICITY $ifi %TRANSPORT_DEMAND_AGGREGATED%==yes OR SUM(IRI,TRANSDEMAND_Y(IY411,IRI))
$ifi %TRANSPORT_SYNTHFUEL_COMMODITY%==ELECTRICITY )


