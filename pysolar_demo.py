import Pysolar
import datetime

lat = 43.53
lng = 172.62

altitudes = []
dates = []
for i in range(24):
	d = datetime.datetime(2013, 9, 4, i, 0, 0, 0)

	altitude = Pysolar.GetAltitude(lat, lng, d)
	azimuth = Pysolar.GetAzimuth(lat, lng, d)

	altitudes.append(Pysolar.radiation.GetRadiationDirect(d, altitude))
	dates.append(d)

for i, val in enumerate(altitudes):
	print val, dates[i].strftime("%Y-%m-%d %H:%M %p")