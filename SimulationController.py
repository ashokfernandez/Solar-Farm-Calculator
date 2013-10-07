# import sys
# from matplotlib.ticker import FuncFormatter
# import matplotlib.pyplot as plt
from SolarAssets import *
from SolarSimulation import *

import ReverseGeocode 
import Countries
import AverageTemperatureData

import datetime

startDate = datetime.date(2013, 1, 1)
endDate = datetime.date(2015, 1, 1)



def CreateSimulation(inputParameters, optionalInputParameters):
	''' Takes the input parameters from the view controller and instantiates the necessary components to run a simulation '''

	# ---------------------- GEO CODING ---------------------------

	# Get the site information from the Reverse Geocode
	code = ReverseGeocode.get_country_code(inputParameters['siteLatitude'], inputParameters['siteLongitude'])

	# Throw an exception if the GeoCode Fails
	if code == False:
		raise ReverseGeocode.CountryNotFound("Country Not Found at Given Lat, Long")


	# ------------------ LOAD DATA FROM FILES ----------------------
	
	# Load the temperature data
	temperature = AverageTemperatureData.TEMPERATURE_DATA[code]['PAST']	
	


	# ------------- CALCULATE OPTIONAL PARAMETERS ------------------

	# If the user specified for the transmission line length to be calculated, then calculate it
	if optionalInputParameters['TXCableLength'] == None:
		TXCableLength = calcLength(inputParameters['siteLatitude'], inputParameters['siteLongitude'], 
								   inputParameters['siteGridLatitude'], inputParameters['siteGridLongitude'])
	else:
		TXCableLength = optionalInputParameters['TXCableLength']


	# --------------- CREATE SIMULATION OBJECTS ---------------------
	
	# Constants
	MATERIALS = {}
	MATERIALS['Copper'] = Material(name='Cu', resistivity=1.68e-8, tempCoefficient=3.62e-3)
	MATERIALS['Aluminium'] = Material(name='Al', resistivity=2.82e-8, tempCoefficient=3.9e-3)

	# Instantiate the panel object
	panel = PVPanel(voltage=inputParameters['panelVoltage'], 
		 			efficiency=inputParameters['panelAngle'] , 
		 			degradationRate=inputParameters['panelDegradation'], 
		 			area=inputParameters['panelArea'], 
		 			cost=inputParameters['panelCost'], 
		 			currency=inputParameters['panelCurrency'])

	module = PVModule(panelType=panel, 
		 			  panelNum=inputParameters['siteNumPanels'])
	
	array = PVArray(moduleType=module, 
					moduleNum=inputParameters['siteNumModules'], 
					arrayAngle=inputParameters['panelAngle'])

	

	dcCable = DCCable(diameter=inputParameters['DCCableDiameter'], 
					  material=MATERIALS[inputParameters['DCCableMaterial']], 
					  length=inputParameters['DCCableLength'], 
					  costPerMeter=inputParameters['DCCableCost'], 
					  depRate=inputParameters['DCCableDepreciation'])	

	ac1Cable = AC1Cable(strandNum=inputParameters['ACCableNumStrands'], 
						diameter=inputParameters['ACCableDiameter'], 
						material=MATERIALS[inputParameters['ACCableMaterial']], 
						length=inputParameters['ACCableLength'], 
						costPerMeter=inputParameters['ACCableCost'], 
						depRate=inputParameters['ACCableDepreciation'])

	ac2Cable = AC2Cable(strandNum=inputParameters['TXCableNumStrands'], 
						diameter=inputParameters['TXCableDiameter'], 
						material=MATERIALS[inputParameters['TXCableMaterial']], 
						length=TXCableLength, 
						costPerMeter=inputParameters['TXCableCost'], 
						depRate=inputParameters['TXCableDepreciation'])

	inverter = Inverter(powerFactor=inputParameters['inverterPowerFactor'], 
						efficiency=inputParameters['inverterEfficiency'], 
						voltage=inputParameters['inverterOutputVoltage'], 
						cost=inputParameters['inverterCost'] , 
						depRate=inputParameters['inverterDepreciation'])
	
	transformer = Transformer(voltage=inputParameters['transformerOutputVoltage'], 
							  efficiency=inputParameters['transformerEfficiency'] , 
							  VARating=inputParameters['transformerRating'] , 
							  cost=inputParameters['transformerCost'] , 
							  depRate=inputParameters['transformerDepreciation'])

	circuitBreaker = CircuitBreaker(cost=inputParameters['circuitBreakerCost'])

	site = Site(transformerNum=inputParameters['siteNumTransformers'], 
				arrayNum=inputParameters['siteNumArrays'], 
				latitude=inputParameters['siteLatitude'], 
				longitude=inputParameters['siteLongitude'],
		  		circuitBreakerNum=inputParameters['siteNumCircuitBreakers'], 
		  		inverterNum=inputParameters['siteNumInverters'], 
		  		temperature=temperature, 
		  		landPrice=inputParameters['siteCost'],
		  		landCurrency=inputParameters['siteCurrency'],
				landAppRate=inputParameters['siteAppreciation'])

	financial = Financial(maintenance=inputParameters['financialMaintenance'], 
						  miscExpenses=inputParameters['financialMiscExpenses'], 
						  interestRate =inputParameters['financialInterestRate'],
						  powerPrice = inputParameters['financialPowerPrice'], 
						  baseCurrency=inputParameters['financialBaseCurrency'])

	simulation = Simulation(start=startDate, finish=endDate, PVPanel=panel, PVModule=module, PVArray=array, 
		                   DCCable=dcCable, Inverter=inverter, AC1Cable=ac1Cable, Transformer=transformer, 
		                   AC2Cable=ac2Cable, CircuitBreaker=circuitBreaker, Site=site, Financial=financial,
	                       numThreads=50, simulationTimestepMins=60)


	return simulation



# def FinancialFormatter(x, pos):
#     '''Converts a money amount into millions or billions if the value is big enough'''
    
#     # If under a million, print like normal
#     if x < 1e6:
#     	format = '$%1.1f' % x
#     # Else if under a billion print the amount in millions
#     elif x < 1e9:
#     	format = '$%1.1fM' % (x*1e-6)
#     # Else print as billions
#     else:
#     	format = '$%1.1fB' % (x*1e-9)

#     return format

# formatter = FuncFormatter(FinancialFormatter)

# # Output day simulation data to csv

# # f = open('averagePower.csv', 'w')
# # for day in powerResults['averagePower']:
# # 	f.write(str(day) + '\n')
# # f.close()

# # f = open('days.csv', 'w')
# # for day in powerResults['days']:
# # 	f.write(str(day) + '\n')
# # f.close()

# plt.figure(1)
# plt.subplot(311)
# plt.plot(powerResults['days'], powerResults['averagePower'])
# plt.title('Average Power of the PV farm')
# plt.ylabel('Power (kW)')

# plt.subplot(312)
# plt.plot(powerResults['days'], powerResults['sunnyTime'], 'g')
# plt.title('Electrical energy of the PV farm at GEP')
# plt.ylabel('Energy (kWh)')

# plt.subplot(313)
# plt.plot(powerResults['days'], powerResults['totalEffciency'], 'r')
# plt.title('Total efficiency of the PV farm')
# plt.ylabel('Efficiency (%)')

# # plt.figure(2)
# # a = plt.subplot(311)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['netAssetValue'])
# # plt.title('Net Asset Value')

# # a = plt.subplot(312)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['loanValue'], 'r')
# # plt.title('Loan Value')

# # a = plt.subplot(313)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['accumulativeRevenue'], 'g')
# # plt.title('Accumlative Revenue')

# plt.show()