import sys
from SolarSimulation import *
import datetime
import ReverseGeocode 
import Countries
import AverageTemperatureData

siteLat = -43.521886
siteLong = 172.583864

gridLat = -43.521543
gridLong = 172.571075

startDate = datetime.date(2013, 1, 1)
endDate = datetime.date(2015, 1, 1)

# Get the site information from the Reverse Geocode
code = ReverseGeocode.get_country_code(siteLat, siteLong)

if code == False:
	print "Google couldn't locate a supported country at that location"
	sys.exit()
	
print "Running simulation in %s" % Countries.LONG_CODE_TO_NAME[code]

temperature = AverageTemperatureData.TEMPERATURE_DATA[code]['PAST']	
siteToGXP = calcLength(siteLat, siteLong, gridLat, gridLong)

exchange = PyExchangeRates.Exchange('843ce8fdc22c47779fb3040c2ba9a586')


panel = PVPanel(voltage=30.5, efficiency=15, degradationRate=0.4, area=1.63, cost=50,
	currency='NZD')

module = PVModule(panelType=panel, panelNum=20)
array = PVArray(moduleType=module, moduleNum=7, arrayAngle=45)

MATERIAL_CU = Material(name='Cu', resistivity=1.68e-8, tempCoefficient=3.62e-3)
MATERIAL_AL = Material(name='Al', resistivity=2.82e-8, tempCoefficient=3.9e-3)

dcCable = DCCable(diameter=20, material=MATERIAL_CU, length=100, costPerMeter=100, depRate=0)
ac1Cable = AC1Cable(strandNum=5, diameter=6, material=MATERIAL_AL, length=100, costPerMeter=100,
	depRate=0)
ac2Cable = AC2Cable(strandNum=5, diameter=2, material=MATERIAL_AL, length=siteToGXP,
	costPerMeter=100, depRate=0)

inverter = Inverter(powerFactor=0.95, efficiency=95, voltage=400, cost=1000, depRate=0)
transformer = Transformer(voltage=11e3, efficiency=98, VARating=1, cost=1000, depRate=0,
	scrapValue=500)

circuitBreaker = CircuitBreaker(cost=1000)

site = Site(transformerNum=3, arrayNum=30, latitude=siteLat, longitude=siteLong,
	circuitBreakerNum=15, inverterNum=10, temperature=temperature, landPrice=10000000,
	landAppRate=1.03)

financial = Financial(maintenance=30000, miscExpenses=(500000+500000), interestRate = 6,
					 powerPrice = 0.2, baseCurrency='NZD')

simulation = Simulation(start=startDate, finish=endDate, PVPanel=panel, PVModule=module, PVArray=array, 
	                   DCCable=dcCable, Inverter=inverter, AC1Cable=ac1Cable, Transformer=transformer, 
	                   AC2Cable=ac2Cable, CircuitBreaker=circuitBreaker, Site=site, Financial=financial,
                       numThreads=100, simulationTimestepMins=120)

simulation.run()