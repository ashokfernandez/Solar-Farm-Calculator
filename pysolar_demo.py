import Pysolar
import datetime

import matplotlib.pyplot as plt

lat = 43.53
lng = 172.62


TIME_STEP = 1
SIM_LENGTH = 1440
start = datetime.datetime(2013, 9, 4, 0, 0, 0, 0)
days = []
radiation = []
for i in range(SIM_LENGTH):
	d = start + datetime.timedelta(minutes=TIME_STEP*i)
	days.append(d)

	altitude = Pysolar.GetAltitude(lat, lng, d)
	azimuth = Pysolar.GetAzimuth(lat, lng, d)

	radiation.append(Pysolar.radiation.GetRadiationDirect(d, altitude))
	

plt.figure(1)
plt.plot(days, radiation)
plt.title('PySolar - Legit or not?')
plt.ylabel('Solar stuff')
plt.show()