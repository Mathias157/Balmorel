TABLE TECHGROUPKPOT(CCCRRRAAA,TECH_GROUP)       'Technology group capacity restriction by geography (MW)'                         
                                                                                                          RESERVOIR_PMP           
DK1                                                                                                       eps                     
DK2                                                                                                       eps                     
FIN                                                                                                       eps                     
DE4-E                                                                                                     19320                   
DE4-N                                                                                                     952.8                   
DE4-S                                                                                                     17304                   
DE4-W                                                                                                     9184                    
NL                                                                                                        eps                     
NO1                                                                                                       3729                    
NO2                                                                                                       11317                   
NO3                                                                                                       4583                    
NO4                                                                                                       5257                    
NO5                                                                                                       8116                    
SE1                                                                                                       eps                     
SE2                                                                                                       eps                     
SE3                                                                                                       eps                     
SE4                                                                                                       eps                     
UK                                                                                                        26884                   
EE                                                                                                        eps                     
LV                                                                                                        eps                     
LT                                                                                                        9000                    
PL                                                                                                        16638                   
FR                                                                                                        54000                   
BE                                                                                                        11772                   
                                                                                                                                  
                                                                                                                                  
IT                                                                                                        9580.64516129032        
CH                                                                                                        9870.96774193548        
AT                                                                                                        9870.96774193548        
CZ                                                                                                        1172                    
ES                                                                                                        35032.2580645161        
PT                                                                                                        2952                    
SK                                                                                                        2952                    
HU                                                                                                        2952                    
SI                                                                                                        2952                    
HR                                                                                                        2952                    
RO                                                                                                        2952                    
BG                                                                                                        2952                    
GR                                                                                                        2952                    
IE                                                                                                        2952                    
LU                                                                                                        2952                    
                                                                                                                                  
                                                                                                                                  
*National potentials (not activated by default)                                                                                   
+                                                                                                         WINDTURBINE_ONSHORE     
$ontext                                                                                                                           
NORWAY                                                                                                    14000                   
DENMARK                                                                                                   6200                    
FINLAND                                                                                                   15000                   
GERMANY                                                                                                   98700                   
NETHERLANDS                                                                                               10300                   
SWEDEN                                                                                                    35000                   
UNITED_KINGDOM                                                                                            38400                   
ESTONIA                                                                                                   15800                   
LATVIA                                                                                                    23300                   
LITHUANIA                                                                                                 21400                   
POLAND                                                                                                    10426                   
BELGIUM                                                                                                   6719                    
FRANCE                                                                                                    101200                  
                                                                                                                                  
DE4-S                                                                                                     7444                    
$offtext                                                                                                                          
;                                                                                                                                 
$ifi not %limited_individual_heatpump% == yes $goto unlimited_individual_heatpumps
* Simple assumption of 50% less heat pump capacity compared to 2050 baseline allflex scenario
TECHGROUPKPOT('AL','HEATPUMP')=727.37413/2;
TECHGROUPKPOT('AT','HEATPUMP')=15825.0303/2;
TECHGROUPKPOT('BA','HEATPUMP')=1759.07783/2;
TECHGROUPKPOT('BE','HEATPUMP')=20924.557/2;
TECHGROUPKPOT('BG','HEATPUMP')=4404.4341/2;
TECHGROUPKPOT('CH','HEATPUMP')=15733.9782/2;
TECHGROUPKPOT('CY','HEATPUMP')=612.696479/2;
TECHGROUPKPOT('CZ','HEATPUMP')=16557.3655/2;
TECHGROUPKPOT('DE4-E','HEATPUMP')=21138.4188/2;
TECHGROUPKPOT('DE4-N','HEATPUMP')=6492.84726/2;
TECHGROUPKPOT('DE4-S','HEATPUMP')=56242.709/2;
TECHGROUPKPOT('DE4-W','HEATPUMP')=61942.7148/2;
TECHGROUPKPOT('DK1','HEATPUMP')=3171.34028/2;
TECHGROUPKPOT('DK2','HEATPUMP')=2176.52205/2;
TECHGROUPKPOT('EE','HEATPUMP')=1654.0602/2;
TECHGROUPKPOT('ES','HEATPUMP')=31691.4424/2;
TECHGROUPKPOT('FIN','HEATPUMP')=10017.4462/2;
TECHGROUPKPOT('FR','HEATPUMP')=87888.982/2;
TECHGROUPKPOT('GR','HEATPUMP')=8613.7441/2;
TECHGROUPKPOT('HR','HEATPUMP')=5161.4643/2;
TECHGROUPKPOT('HU','HEATPUMP')=16291.0235/2;
TECHGROUPKPOT('IE','HEATPUMP')=7310.0506/2;
TECHGROUPKPOT('IT','HEATPUMP')=88132.103/2;
TECHGROUPKPOT('LT','HEATPUMP')=1946.44317/2;
TECHGROUPKPOT('LU','HEATPUMP')=1622.06297/2;
TECHGROUPKPOT('LV','HEATPUMP')=1717.97743/2;
TECHGROUPKPOT('ME','HEATPUMP')=233.53311/2;
TECHGROUPKPOT('MK','HEATPUMP')=550.83761/2;
TECHGROUPKPOT('MT','HEATPUMP')=193.32315/2;
TECHGROUPKPOT('NL','HEATPUMP')=24098.1774/2;
TECHGROUPKPOT('NO1','HEATPUMP')=2123.88255/2;
TECHGROUPKPOT('NO2','HEATPUMP')=1316.3814/2;
TECHGROUPKPOT('NO3','HEATPUMP')=828.93465/2;
TECHGROUPKPOT('NO4','HEATPUMP')=654.13227/2;
TECHGROUPKPOT('NO5','HEATPUMP')=554.8733/2;
TECHGROUPKPOT('PL','HEATPUMP')=31509.5923/2;
TECHGROUPKPOT('PT','HEATPUMP')=4511.91996/2;
TECHGROUPKPOT('RO','HEATPUMP')=16606.2249/2;
TECHGROUPKPOT('RS','HEATPUMP')=3687.4394/2;
TECHGROUPKPOT('SE1','HEATPUMP')=331.61354/2;
TECHGROUPKPOT('SE2','HEATPUMP')=666.86212/2;
TECHGROUPKPOT('SE3','HEATPUMP')=4819.70668/2;
TECHGROUPKPOT('SE4','HEATPUMP')=1464.74915/2;
TECHGROUPKPOT('SI','HEATPUMP')=2402.6931/2;
TECHGROUPKPOT('SK','HEATPUMP')=5402.8392/2;
TECHGROUPKPOT('UK','HEATPUMP')=100754.32/2;
$label unlimited_individual_heatpumps

* low pit thermal storage potential
$ifi not %low_pit_storage% == yes $goto unlimited_pit_storage
TECHGROUPKPOT('AT','PIT')=16425.4/2;
TECHGROUPKPOT('BA','PIT')=245.07/2;
TECHGROUPKPOT('BE','PIT')=65117.2/2;
TECHGROUPKPOT('CH','PIT')=10138.22/2;
TECHGROUPKPOT('DE4-E','PIT')=9002.16/2;
TECHGROUPKPOT('DK1','PIT')=104381.665/2;
TECHGROUPKPOT('DK2','PIT')=46163.79/2;
TECHGROUPKPOT('EE','PIT')=43417.875/2;
TECHGROUPKPOT('FIN','PIT')=114355.29/2;
TECHGROUPKPOT('FR','PIT')=384223./2;
TECHGROUPKPOT('GR','PIT')=6088.7507/2;
TECHGROUPKPOT('LT','PIT')=391219.84/2;
TECHGROUPKPOT('LV','PIT')=89857.82/2;
TECHGROUPKPOT('NL','PIT')=7661.64/2;
TECHGROUPKPOT('NO1','PIT')=53408.33/2;
TECHGROUPKPOT('NO2','PIT')=79767.1/2;
TECHGROUPKPOT('NO3','PIT')=30362.79/2;
TECHGROUPKPOT('NO4','PIT')=21082.79/2;
TECHGROUPKPOT('NO5','PIT')=14707.53/2;
TECHGROUPKPOT('PT','PIT')=60155.1/2;
TECHGROUPKPOT('RS','PIT')=2132.24/2;
TECHGROUPKPOT('SE1','PIT')=40200.14/2;
TECHGROUPKPOT('SE2','PIT')=98850.8212/2;
TECHGROUPKPOT('SE3','PIT')=283458.24/2;
TECHGROUPKPOT('SE4','PIT')=114979.23/2;
TECHGROUPKPOT('UK','PIT')=136.866/2;
$label unlimited_pit_storage

* low salt-cavern storage potential
$ifi not %low_saltcavern% == yes $goto unlimited_saltcavern
TECHGROUPKPOT('BE','H2_SALTCAVERN_STORAGE')=4547209.8/2;
TECHGROUPKPOT('DE4-E','H2_SALTCAVERN_STORAGE')=15385500/2;
TECHGROUPKPOT('DE4-N','H2_SALTCAVERN_STORAGE')=535341/2;
TECHGROUPKPOT('DE4-W','H2_SALTCAVERN_STORAGE')=10781221/2;
TECHGROUPKPOT('DK1','H2_SALTCAVERN_STORAGE')=1789687/2;
TECHGROUPKPOT('ES','H2_SALTCAVERN_STORAGE')=6955541/2;
TECHGROUPKPOT('FR','H2_SALTCAVERN_STORAGE')=3498727.2/2;
TECHGROUPKPOT('GR','H2_SALTCAVERN_STORAGE')=1844576/2;
TECHGROUPKPOT('NL','H2_SALTCAVERN_STORAGE')=4704056/2;
TECHGROUPKPOT('PL','H2_SALTCAVERN_STORAGE')=4257020/2;
TECHGROUPKPOT('PT','H2_SALTCAVERN_STORAGE')=728132/2;
TECHGROUPKPOT('RO','H2_SALTCAVERN_STORAGE')=2463280.2/2;
TECHGROUPKPOT('UK','H2_SALTCAVERN_STORAGE')=5501270/2;
$label unlimited_saltcavern

TABLE TECHGROUPKPOT2(CCCRRRAAA,TECH_GROUP)       'Technology group capacity restriction by geography (MW)'
        SOLARPV
AL      600
AT      51000
BA      1000
BE      27500
BG      4500
CH      10000
CY      1500
CZ      12000
DE4-E   50549
DE4-N   24213
DE4-S   76050
DE4-W   58119
DK1     20094
DK2     11926
EE      1315
ES      96000
FIN     7160
FR      125000
GR      23500
HR      1500
HU      11500
IE      10220
IT      125000
LT      1605
LU      1000
LV      571
ME      1000
MK      2000
MT      205
NL      69000
NO1     1200
NO2     1200
NO3     700
NO4     150
NO5     1150
PL      43418
PT      14500
RO      17500
RS      2500
SE1     2993
SE2     3833
SE3     5750
SE4     5750
SI      6000
SK      2500
UK      42000
;

TECHGROUPKPOT(CCCRRRAAA, 'SOLARPV') = TECHGROUPKPOT2(CCCRRRAAA,'SOLARPV');
