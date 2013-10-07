import sys
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
from SolarSimulation import *
import datetime
import ReverseGeocode 
import Countries
import AverageTemperatureData

siteLat = -21.0928
siteLong = -175.1050

gridLat = -21.0910
gridLong = -175.1102

startDate = datetime.date(2013, 1, 1)
endDate = datetime.date(2020, 1, 1)

# Get the site information from the Reverse Geocode
code = ReverseGeocode.get_country_code(siteLat, siteLong)

if code == False:
	print "Google couldn't locate a supported country at that location"
	sys.exit()
	
print "Running simulation in %s" % Countries.LONG_CODE_TO_NAME[code]

temperature = AverageTemperatureData.TEMPERATURE_DATA[code]['PAST']	
siteToGXP = calcLength(siteLat, siteLong, gridLat, gridLong)


#TODO: Add panel rating to PVPanel input
panel = PVPanel(voltage=30.5, efficiency=15, degradationRate=0.4, area=1.63, cost=50,
	currency='NZD')

module = PVModule(panelType=panel, panelNum=30)
array = PVArray(moduleType=module, moduleNum=7, arrayAngle=21)

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
					 powerPrice = 20, baseCurrency='NZD')

simulation = Simulation(start=startDate, finish=endDate, PVPanel=panel, PVModule=module, PVArray=array, 
	                   DCCable=dcCable, Inverter=inverter, AC1Cable=ac1Cable, Transformer=transformer, 
	                   AC2Cable=ac2Cable, CircuitBreaker=circuitBreaker, Site=site, Financial=financial,
                       numThreads=10, simulationTimestepMins=30)


results = simulation.run()

powerResults = results['power']
financialResults = results['financial']

def FinancialFormatter(x, pos):
    '''Converts a money amount into millions or billions if the value is big enough'''
    
    # If under a million, print like normal
    if x < 1e6:
    	format = '$%1.1f' % x
    # Else if under a billion print the amount in millions
    elif x < 1e9:
    	format = '$%1.1fM' % (x*1e-6)
    # Else print as billions
    else:
    	format = '$%1.1fB' % (x*1e-9)

    return format

formatter = FuncFormatter(FinancialFormatter)

# Output day simulation data to csv

# f = open('averagePower.csv', 'w')
# for day in powerResults['averagePower']:
# 	f.write(str(day) + '\n')
# f.close()

# f = open('days.csv', 'w')
# for day in powerResults['days']:
# 	f.write(str(day) + '\n')
# f.close()

plt.figure(1)
# plt.subplot(311)
plt.plot(powerResults['days'], powerResults['averagePower'])
plt.title('Average Power of the PV farm')
plt.ylabel('Power (kW)')

plt.figure(2)
# plt.subplot(312)
plt.plot(powerResults['days'], powerResults['electricalEnergy'], 'g')
plt.title('Electrical energy of the PV farm at GEP')
plt.ylabel('Energy (kWh)')

plt.figure(3)
# plt.subplot(313)
plt.plot(powerResults['days'], powerResults['totalEffciency'], 'r')
plt.title('Total efficiency of the PV farm')
plt.ylabel('Efficiency (%)')

plt.figure(4)
a = plt.subplot(311)
a.yaxis.set_major_formatter(formatter)
plt.plot(financialResults['days'], financialResults['netAssetValue'])
plt.title('Net Asset Value')

a = plt.subplot(312)
a.yaxis.set_major_formatter(formatter)
plt.plot(financialResults['days'], financialResults['loanValue'], 'r')
plt.title('Loan Value')

a = plt.subplot(313)
a.yaxis.set_major_formatter(formatter)
plt.plot(financialResults['days'], financialResults['accumulativeRevenue'], 'g')
plt.title('Accumlative Revenue')

plt.figure(5)
plt.plot(financialResults['days'], powerResults['electricalEffciency'], 'g')
plt.title('Electrical Effciency')
plt.ylabel('Efficiency (%)')

plt.show()