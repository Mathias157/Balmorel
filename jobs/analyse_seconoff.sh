cli_options=$1
pixi run analyse $cli_options dem electricity --filters 'Scenario in ["APS_base_allflex_INV", "noh2_INV", "noh2_exo_INV", "noh2noev_INV", "noh2noev_exo_INV", "noh2noevnoii_INV", "noh2noevnoii_exo_INV", "noh2noevnoiinodh_INV", "noh2noevnoiinodh_exo_INV"]'
