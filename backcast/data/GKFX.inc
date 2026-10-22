* Backcast: the base capacities, plus nuclear units that ran in 2023 but are
* missing from base's 2023 column (see README.md, Capacity corrections). Their
* weekly GKRATE_ENTSOE ratings carry their outages and closures.
$include '../../base/data/GKFX.inc';

* Germany: Isar 2 and Neckarwestheim 2 (DE4-S) and Emsland (DE4-W) ran until
* 15 April 2023. Base has them in 2022 and at 0 from 2023.
GKFX('2023','DE4-S_A','GNR_ST_NUCL_CND_E-33') = GKFX('2022','DE4-S_A','GNR_ST_NUCL_CND_E-33');
GKFX('2023','DE4-W_A','GNR_ST_NUCL_CND_E-33') = GKFX('2022','DE4-W_A','GNR_ST_NUCL_CND_E-33');

* Finland: Olkiluoto 3 ran through 2023 (commercial operation from 16 April,
* test production before). Base adds it only from 2024.
GKFX('2023','FinA','GNR_ST_NUCL_CND_E-33') = GKFX('2024','FinA','GNR_ST_NUCL_CND_E-33');
