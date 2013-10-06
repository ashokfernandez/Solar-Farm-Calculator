import Pysolar
import datetime
import math

import matplotlib.pyplot as plt

lat = 40.67
lng = -73.94

panelAngle = 45




TIME_STEP = 30
SIM_LENGTH = 17520
start = datetime.datetime(2013, 12, 4, 0, 0, 0, 0)

currentDayOfYear = (start - datetime.datetime(2013, 1, 1)).days
print currentDayOfYear

 # Declination angle of the sun
argRadians = math.radians((360 * (284 + currentDayOfYear)) / 365.0)
delta = 23.45 * math.sin(argRadians)
a = 90 - lat + delta
    
# Calculates the irradiance on the panel for a day
argRadians_1 = math.radians(a + panelAngle)
argRadians_2 = math.radians(a)


days = []
radiation = []
irrPanel = []
for i in range(SIM_LENGTH):
	d = start + datetime.timedelta(minutes=TIME_STEP*i)
	days.append(d)

	altitude = Pysolar.GetAltitude(lat, lng, d)
	azimuth = Pysolar.GetAzimuth(lat, lng, d)

	radiation.append(Pysolar.radiation.GetRadiationDirect(d, altitude))
	panelIrr = (radiation[i] * math.sin(argRadians_1) / math.sin(argRadians_2))
	irrPanel.append(panelIrr)



plt.figure(1)
plt.plot(days, radiation, 'g')# , days, irrPanel, 'b')
plt.title('PySolar - Legit or not?')
plt.ylabel('Solar stuff')
plt.show()