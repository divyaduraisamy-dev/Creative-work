# MWD_heat_strain_dataset.csv

46 rows of military working dog (MWD) heat-strain measurements, compiled by hand by Divya
Duraisamy from the values reported in:

- O'Brien, C., Karis, A. J., Tharion, W. J., Sullivan, H. M., and Hoyt, R. W. "Core Temperature
  Responses of Military Working Dogs During Training Activities and Exercise Walks."
  *U.S. Army Medical Department Journal*, 2017.
- O'Brien, C., and Berglund, L. G. "Predicting Recovery from Exertional Heat Strain in Military
  Working Dogs." *Journal of Thermal Biology*, vol. 76, 2018.
  https://doi.org/10.1016/j.jtherbio.2018.07.001

Each row is one dog and one training activity in October, March or August: weight, length, air
temperature and humidity, core temperature (Tc) at the end of exercise and 5 to 60 minutes into
recovery, and the Canine Thermal Model (CTM) values. Dogs are anonymous ("OCT Dog 1", ...).

Used by `heat_model.py` to train the walk planner on the KOVU page (from my IST707 final project),
and by `build_walk_table.py` to precompute it for the plain web version.
For education and general guidance only, not veterinary advice. Please cite the studies above if
you use these numbers.

# foodkeeper.json

USDA FSIS FoodKeeper data, English (public domain, U.S. government work). Listed on the
"FSIS FoodKeeper Data" page on catalog.data.gov, which links to
https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json. The file says it is version 128
(FMA-Data-v128.xlsx), last modified September 6, 2018.

The FSIS site turns away automated downloads (HTTP 403), so this copy came from the Internet
Archive's snapshot of that address (July 2, 2025). Its fingerprint (SHA-1
676CHRGJHGCERQXXKMAAPV2QL2MK5WG3, compressed) matches the archive's October 6, 2026 capture, so it
is the same file FSIS was still serving then. Saved here uncompressed.

Six sheets: Version, Category, Product (661 foods, with pantry / refrigerator / freezer times,
each as Min, Max and Metric, plus "DOP_" = from the date of purchase and "After_Opening" /
"After_Thawing" times), CookingTips, CookingMethods and Data Dictionary.

Used by `keep_or_toss.py`, which reads the storage times for the Keep or Toss app while the site
builds (see `keep_or_toss_content.py`). To update, replace this file with a newer download and
rebuild; the build prints the version it read.
