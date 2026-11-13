* Reservoir volumes cut to the ENTSO-E observed maximum filling of 2023 (16.1.D):
* where the highest level Balmorel can reach (max over seasons of HYRSDATA's
* HYRSMAXVOL x volume) is above it, HYRSMAXVOL_G is scaled so they are equal.
* Regions below the observed maximum, or without ENTSO-E data, keep base's.
* Regions with a seasonal HYRSDATA envelope (the Nordics) keep base's: the envelope
* already holds their historical weekly levels.
* Written by: pixi run python analysis/hydro_reservoir_volumes.py 2023
$include '../../base/data/HYRSMAXVOL_G.inc';

* AT: volume 2328 -> 2058 GWh, reachable 2211 -> 1955 GWh (observed max)
HYRSMAXVOL_G('AT_A',GGG) = 0.884274 * HYRSMAXVOL_G('AT_A',GGG);
* CH: volume 7561 -> 5396 GWh, reachable 7183 -> 5127 GWh (observed max)
HYRSMAXVOL_G('CH_A',GGG) = 0.713695 * HYRSMAXVOL_G('CH_A',GGG);
* ES: volume 14200 -> 10745 GWh, reachable 13490 -> 10208 GWh (observed max)
HYRSMAXVOL_G('ES_A',GGG) = 0.756719 * HYRSMAXVOL_G('ES_A',GGG);
* FR: volume 12186 -> 3172 GWh, reachable 11577 -> 3014 GWh (observed max)
HYRSMAXVOL_G('FR_A',GGG) = 0.260322 * HYRSMAXVOL_G('FR_A',GGG);
* GR: volume 3542 -> 3172 GWh, reachable 3365 -> 3013 GWh (observed max)
HYRSMAXVOL_G('GR_A',GGG) = 0.895606 * HYRSMAXVOL_G('GR_A',GGG);
* HR: volume 1517 -> 1215 GWh, reachable 1441 -> 1154 GWh (observed max)
HYRSMAXVOL_G('HR_A',GGG) = 0.801301 * HYRSMAXVOL_G('HR_A',GGG);
* IT: volume 5989 -> 4002 GWh, reachable 5689 -> 3802 GWh (observed max)
HYRSMAXVOL_G('IT_A',GGG) = 0.668282 * HYRSMAXVOL_G('IT_A',GGG);
* RO: volume 3096 -> 2900 GWh, reachable 2942 -> 2755 GWh (observed max)
HYRSMAXVOL_G('RO_A',GGG) = 0.936475 * HYRSMAXVOL_G('RO_A',GGG);
* RS: volume 702 -> 685 GWh, reachable 667 -> 651 GWh (observed max)
HYRSMAXVOL_G('RS_A',GGG) = 0.975984 * HYRSMAXVOL_G('RS_A',GGG);
