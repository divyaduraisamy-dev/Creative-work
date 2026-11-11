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

Used by `heat_model.py` to train the walk planner on the KOVU page (from my IST707 final project).
For education and general guidance only, not veterinary advice. Please cite the studies above if
you use these numbers.
