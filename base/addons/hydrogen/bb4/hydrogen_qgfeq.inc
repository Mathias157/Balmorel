+VGE_T(IY411,IA,G,IS3,T)$(IHYDROGEN_GETOH2(G) OR IHYDROGEN_GEHTOH2(G) OR IHYDROGEN_GETOHH2(G))
+(VGBIOMETH_T(IY411,IA,G,IS3,T)/GDATA(G,'GDFE'))$(IHYDROGEN_GH2TOBIOMETH(G))
+(VGBIOGASUPGRADING_T(IY411,IA,G,IS3,T)/GDATA(G,'GDFE'))$(IHYDROGEN_GBIOGASUPGRADING(G))
+(VGBIOGASMETHANATION_T(IY411,IA,G,IS3,T)/GDATA(G,'GDFE'))$(IHYDROGEN_GBIOGASMETHANATION(G))
+(VHYDROGEN_GH2_T(IY411,IA,G,IS3,T)/GDATA(G,'GDFE'))$(IHYDROGEN_GH2STO(G) OR IHYDROGEN_GCH4TOH2(G))
$ifi %generic_synfuel%==yes +(VSYNFUEL_G_T(IY411,IA,G,IS3,T)/GDATA(G,'GDFE'))$(IHYDROGEN_BIOTOSYNFUEL(G))
