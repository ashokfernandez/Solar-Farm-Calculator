# -------------------------------------------------------------------------------------------------------------------
# SolarSimulation : Solar farm model simulator
# -------------------------------------------------------------------------------------------------------------------
# Author: Darren O'Neill
# Author: Jarrad Raumati
# Date: 20/09/2013
#
# This script simulates a solar farm to obtain the effeciency of a given
# location

# Input Variables--------------------------------------------------------#
import Pysolar
import Queue
import math
import matplotlib.pyplot as plt
import numpy
import time
from datetime import *

#start = time.time()

def calcTransmissionLength(site, GEP):
    ''' Calculates the distance between the solar farm site and the grid entry point (GEP) '''
    R = 6371 # radius of the earth (km) TODO: Citation needed

    # Calculate the latitude / longitude difference in radians
    dlat = math.radians(site.getLatitude() - GEP.getLatitude())
    dlon = math.radians(site.getLongitude() - GEP.getLongitude())
    
    # Average latitude in radians
    latAverage = math.radians((site.getLatitude()+GEP.getLatitude()) / 2)

    # The linear distance between the site and the GEP
    length = R * math.sqrt((dlat) ** 2 + (math.cos(latAverage) * dlon) ** 2)

    return length

def calcOptimumAngle(directIrr, site):

    testAngle = [x * 0.1 for x in range(0, 90)]  # [0:0.1:90] specifices angle between 0 and 90 degrees
    angleLength = len(testAngle) # length of test angle array
    
    meanIrr = list(range(angleLength)) # init array for length for mean irradiance

    # iterates through each angle and calculates the mean irradiance for that year
    for i in range(angleLength):
        yearlyIrradiance = []

        for j in range(365):
            # This simulates a year of how much irradiance is incident on a panel surface.
            
            # arbitary angle that is used for calculating the irradiance
            argRadians = math.radians(360/365*(284 + j))
            # same as above for the next 3 lines
            a = 90 - site.getLatitude() + 23.45 * math.sin(argRadians)
            argRadians_1 = math.radians(a + testAngle[i])
            argRadians_2 = math.radians(a)

            # Calculates the irradiance on the panel for a day
            yearlyIrradiance.append(directIrr[j] * math.sin(argRadians_1) / math.sin(argRadians_2))
        
        # Take the mean irradiance and stores within an array
        meanIrr[i] = numpy.mean(yearlyIrradiance)
    
    # Takes the angle with the highest average irradiance
    ind = meanIrr.index(max(meanIrr))

    #the optimum angle for solar panel
    opAngle = testAngle[ind]

    return opAngle


def calcCableResistance(cable, temperature):
    ''' Calculates the resistance of a cable given the cable material, ambient temperature, diameter and length. '''

    # Uses base temperature of 20 degrees celcius to correct the resistivity for the ambient temperature.
    caliResistivity = cable.material.getResistivity()*(1 + cable.material.getTempCoefficient()*(temperature-20))
    
    # area of the cable
    area = math.pi / 4 * (cable.getDiameter() * 1e-3) ** 2
    resistance = p * cable.getLength() / area

    return resistance

# -------------------------------------------------------------------------------------------------------------------
# SOLAR PANELS
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
panelVoltage = 30.5 # Voltage of the panel at maximum power point
panelEff = 0.15 # Solar panel efficiency (typically 15-18 #)
panelDegRate = 0.4 # Rate at which the solar panel degradates (# per year)
panelArea = 1.63 # Panel area (m^2)


# Financial
panelCost = 50 # Cost of the single panel
panelDepRate = 20 # Panel depreciation rate (% per year)


class PVPanel(object):
    ''' Class to store information relating to a solar PV panel '''
    def __init__(self, voltage, efficiency, degradationRate, area, cost, depRate = 0):
        ''' Initialise a PV panel object '''
        self.voltage = voltage                  # Panel rated voltage (V)
        self.efficiency = efficiency            # Panel rated efficiency (%)
        self.degradationRate = degradationRate  # Panel asset degradation rate (%)
        self.area = area                        # Panel surface area (m^2)

        # Financial properties
        self.cost = cost                        # Cost (currency/unit)
        self.depRate = depRate                  # Asset deprecation rate (%)

    def getVoltage(self):
        ''' Return the panel voltage '''
        return self.voltage

    def setVoltage(self, voltage):
        ''' Set the panel voltage '''
        self.voltage = voltage

    def getEfficiency(self):
        ''' Return the panel efficiency '''
        return self.efficiency

    def setEfficiency(self, efficiency):
        ''' Set the panel efficiency '''
        self.efficiency = efficiency

    def getDegradationRate(self):
        ''' Return the panel asset degradation rate '''
        return self.degradationRate

    def setDegradationRate(self, degradationRate):
        ''' Set the asset degradation rate '''
        self.degradationRate = degradationRate

    def getArea(self):
        ''' Return the panel surface area '''
        return self.area

    def setArea(self):
        ''' Set the panel surface area '''
        self.area = area

    def getCost(self):
        ''' Return the cost of the panel '''
        return self.cost

    def setCost(self, cost):
        ''' Set the cost of the panel '''
        self.cost = cost

    def getDepRate(self):
        ''' Return the asset depreciation rate of the panel '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset value depreciation rate of the panel '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# SOLAR MODULE
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
moduleNum = 20 # Number of solar panels in a module
solarVoltage = panelVoltage * moduleNum

class PVModule(object):
    ''' Class to store information relating to a solar PV module. A module contains PV panels '''
    def __init__(self, panelType, panelNum):
        ''' Initialise a PV module object '''
        self.panelType = panelType      # Type of panel within the module
        self.panelNum = panelNum        # Number of panels within the module
        self.voltage = None             # Total voltage of the module (panels connected in series)
        self.__calculateModuleVoltage()

    def __calculateModuleVoltage(self):
        ''' Calculate the total voltage of the module '''
        self.voltage = self.panelType.getVoltage() * self.panelNum        

    def setPanelType(self, panelType):
        ''' Set the panel type within a module '''
        self.panelType = panelType
        self.__calculateModuleVoltage()

    def getPanelType(self):
        ''' Return the panel object within the module '''
        return self.panelType

    def setPanelNum(self, panelNum):
        ''' Set the number of panels within a module '''
        self.panelNum = panelNum
        self.__calculateModuleVoltage

    def getVoltage(self):
        ''' Return the module voltage '''
        return self.voltage

# -------------------------------------------------------------------------------------------------------------------
# SOLAR ARRAY
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
arrayModuleNum = 7 # Number of modules that make up an array (modlues are in parrallel)
arrayAngle = 45 # Angle from panel to horizontal
useOptimumAngle = 1

class PVArray(object):
    ''' Class to store the information relating to a PV array. An array contains PV modules '''
    def __init__(self, moduleType, moduleNum, arrayAngle):
        ''' Initialise a PV array object '''
        self.moduleType = moduleType    # Type of module within the array
        self.moduleNum = moduleNum      # Number of modules in the array in parallel connection
        self.angle = arrayAngle         # Angle of the PV panels
        self.voltage = None             # Array voltage
        self.__CalculateArrayVoltage

    def __CalculateArrayVoltage(self):
        ''' Calculates the total voltage of the PV array '''
        self.voltage = self.moduleType.getVoltage()

    def getModuleType(self):
        ''' Return the module type within the array '''
        return self.moduleType

    def setModuleType(self, moduleType):
        ''' Set the module type within the array '''
        self.moduleType = moduleType
        self.__CalculateArrayVoltage

    def getModuleNum(self):
        ''' return the number of modules within the array '''
        return self.moduleNum

    def setModuleNum(self, moduleNum):
        ''' Set the number of modules within the array '''
        self.moduleNum = moduleNum

    def getVoltage(self):
        ''' Return the voltage of the array '''
        return self.voltage

    def getAngle(self):
        ''' Return the angle of the PV panels '''
        return self.angle

    def setAngle(self, angle):
        ''' Set the angle of the panels within the array '''
        self.angle = angle
# -------------------------------------------------------------------------------------------------------------------
# MATERIAL
# -------------------------------------------------------------------------------------------------------------------

class Material(object):
    ''' Class object for a material '''
    def __init__(self, name, resistivity, tempCoefficient):
        ''' Initialise a material object '''
        self.name = name
        self.resistivity = resistivity
        self.tempCoefficient = tempCoefficient

    def getResistivity(self):
        ''' Return the resistivity of the material '''
        return self.resistivity

    def setResistivity(self, resistivity):
        ''' Sets the resistivity of the material '''
        self.resistivity = resistivity

    def getTempCoefficient(self):
        ''' Return the temperature coefficient of the material '''
        return self.tempCoefficient

    def setTempCoefficient(self, tempCoefficient):
        ''' Set the temperature coefficient of the material '''
        self.tempCoefficient = tempCoefficient

# -------------------------------------------------------------------------------------------------------------------
# DC CABLE
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
DCdiameter = 20 # DC cable diameter in mm
DCcableMaterial = 'Cu' # DC cable conductor material
DCcableLength = 100 # DC cable length in meters

# Financial
DCcostPerMeter = 100 # Cost of DC cable per meter
DCDepRate = 6 # DC cable depreciation rate (# per year)

class DCCable(object):
    ''' Class to store the information relating to the DC cable between the PV array and the inverter '''
    def __init__(self, diameter, material, length, costPerMeter, depRate):
        ''' Initialise a DC cable object '''
        self.diameter = diameter            # Diameter of the cable (mm)
        self.material = material            # Material of the conductor within the cable (e.g. Cu, Al)
        self.length = length                # Length of the total amount of cable

        # Financial properties
        self.costPerMeter = costPerMeter    # Cost per meter (currency/m)
        self.depRate = depRate              # Asset depreciation rate (%/year)

    def getDiameter(self):
        ''' Return the cable diameter '''
        return self.diameter

    def setDiameter(self, diameter):
        ''' Set the cable diameter '''
        self.diameter = diameter

    def getMaterial(self):
        ''' Return the cable material '''
        return self.material

    def setMaterial(self, material):
        ''' Set the material of the cable '''
        self.material = material

    def getLength(self):
        ''' Return the length of the cable '''
        return self.length

    def setLength(self, length):
        ''' Set the length of the cable '''
        self.length = length

    def getCostPerMeter(self):
        ''' Return the cost of the DC cable '''
        return self.cost

    def setCostPerMeter(self, costPerMeter):
        ''' Set the cost per meter of cable '''
        self.costPerMeter = costPerMeter

    def getCost(self):
        ''' Return the total cost of cable '''
        return self.costPerMeter * self.length

    def getDepRate(self):
        ''' Return the asset depreciation rate of the cable '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset depreciation rate of the cable '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# INVERTER
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
InvPowerFactor = 0.95 # Power factor of the output of the inverter
InvEff = 0.85 # Inverter effeciency (typicall loss 4-15 #)
InvOutVolt = 400 # Output voltage of the inverter (line to line)

# # Financial
InvCost = 10000 # Cost of the inverter/s
InvDepRate = 7 # Inverter depreciation rate (# per year)

class Inverter(object):
    ''' Class to store the information relating to the Inverter '''
    def __init__(self, powerFactor, efficiency, voltage, cost, depRate):
        '''Initialise an inverter object '''
        self.powerFactor = powerFactor  # Power factor of the inverter
        self.efficiency = efficiency    # Efficiency of the inverter
        self.voltage = voltage          # Output voltage of the inverter to the transformer

        # Financial properties
        self.cost = cost                # Unit cost of the inverter (currency/unit)
        self.depRate = depRate          # Asset depreciation rate (%/year)

    def getPowerFactor(self):
        ''' Return the power factor '''
        return self.powerFactor

    def setPowerFactor(self, powerFactor):
        ''' Set the power factor of the inverter '''
        self.powerFactor = powerFactor

    def getEfficiency(self):
        ''' Return the efficiency of the inverter '''
        return self.efficiency

    def setEfficiency(self, efficiency):
        ''' Set the efficiency of the inverter '''
        self.efficiency = efficiency

    def getVoltage(self):
        ''' Return the output voltage of the inverter '''
        return self.voltage

    def setVoltage(self, voltage):
        ''' Set the output voltage of the inverter '''
        self.voltage = voltage

    def getCost(self):
        ''' Return the unit cost of the inverter '''
        return self.cost

    def setCost(self, cost):
        ''' Set the unit cost of the inverter '''
        self.cost = cost

    def getDepRate(self):
        ''' Return the asset depreciation rate of the inverter '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset depreciation rate of the inverter '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# Inv-Tx Lines (AC1 Cables)
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
AC1Diameter = 6 # Inv-Tx line cable diameter
AC1Material = 'Al' # Inv-Tx cable material
AC1Length = 100 # Length of the Inv-Tx cable

# Financial
AC1Cost = 100 # Cost of cable per meter
AC1DepRate = 6 # Inv-Tx cable depreciation rate (# per year)

class AC1Cable(object):
    ''' Class that stores the information relating to the AC cable
    between the inverter and the transformer '''
    def __init__(self, diameter, material, length, costPerMeter, depRate):
        ''' Initialise the AC cable object '''
        self.diameter = diameter
        self.material = material
        self.length = length

        # Financial properties
        self.getCostPerMeter = costPerMeter
        self.depRate = depRate

    def getDiameter(self):
        ''' Return the cable diameter '''
        return self.diameter

    def setDiameter(self, diameter):
        ''' Set the cable diameter '''
        self.diameter = diameter

    def getMaterial(self):
        ''' Return the cable material '''
        return self.material

    def setMaterial(self, material):
        ''' Set the material of the cable '''
        self.material = material

    def getLength(self):
        ''' Return the length of the cable '''
        return self.length

    def setLength(self, length):
        ''' Set the length of the cable '''
        self.length = length

    def getCostPerMeter(self):
        ''' Return the cost per meter of the cable '''
        return self.costPerMeter

    def setCostPerMeter(self, costPerMeter):
        ''' Set the cost per meter of the cable '''
        self.costPerMeter = costPerMeter

    def getCost(self):
        ''' Return the total cost of the cable '''
        return self.costPerMeter * self.length

    def getDepRate(self):
        ''' Return the asset depreciation rate of the cable '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset depreciation rate of the cable '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# TRANSFORMER
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
TxOutVolt = 11e3 # Transformer secondary voltage
TxEff = 0.95 # Transformer efficiency
TxRating = 3 # MVA rating

# Financial
TxCost = 1000000 # Cost of the transformer
TxDepRate = 6 # Transformer depreciation rate (# per year)
TxScrap = 30000 # Transformer scrap value

class Transformer(object):
    ''' Class that stores the information relating to a transformer '''
    def __init__(self, voltage, efficiency, VARating, cost, depRate, scrap):
        ''' Initialise the transformer object '''
        self.voltage = voltage
        self.efficiency = efficiency
        self.VARating = VARating

        # Financial properties
        self.cost = cost
        self.depRate = depRate
        self.scrap = scrap

    def getVoltage(self):
        ''' Return the high voltage side of the transformer '''
        return self.voltage

    def setVoltage(self, voltage):
        ''' Set the high voltage side of the transformer '''
        self.voltage = voltage

    def getEfficiency(self):
        ''' Return the efficiency of the transformer '''
        return self.efficiency

    def setEfficiency(self, efficiency):
        ''' Set the efficiency of the transformer '''
        self.efficiency = efficiency

    def getVARating(self):
        ''' Return the rating of the transformer (MVA) '''
        return self.VARating

    def setVARating(self, VARating):
        ''' Set the rating of the transformer (MVA) '''
        self.VARating = VARating

    def getCost(self):
        ''' Return the unit cost of the transformer '''
        return self.cost

    def setCost(self, cost):
        ''' Set the unit cost of the transformer '''
        self.cost = cost

    def getDepRate(self):
        ''' Return the asset depreciation rate of the transformer '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset depreciation rate of the transformer '''
        self.depRate = depRate

    def getScrap(self):
        ''' Return the scrap value of the cable '''
        return self.sc

    def setScrap(self, scrap):
        ''' Set the scrap value of the cable '''
        self.scrap = scrap

# -------------------------------------------------------------------------------------------------------------------
# GEP LINES
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
AC2StrandNum = 5 # Number of strands in ACC or ACSR cable
AC2StrandDiameter = 2 # Strand diameter in mm
AC2Material = 'Al' # Strand material
specifyLength = 0
AC2Length = 0

# Financial
AC2Cost = 100 # Cost of SINGLE cable per meter
TranLineCost = 1000 # Cost of building the transmission line per kilometer
AC2DepRate = 6 # Depreciation rate of the GXP line (# per year)

class GEPLine(object):
    ''' Class that stores the information relating the transmission line between the solar farm and the grid entry
    point '''
    def __init__(self, strandNum, diameter, material, length, latitude, longitude, costPerMeter, depRate):
        ''' Initialise the GEP object '''
        self.strandNum = strandNum
        self.diameter = diameter
        self.material = material
        self.length = length
        self.latitude = latitude
        self.longitude = longitude

        # Financial properties
        self.costPerMeter = costPerMeter
        self.depRate = depRate

    def getStrandNum(self):
        ''' Return the number of strands in ACC or ACSR cable '''
        return self.strandNum

    def setStrandNum(self, strandNum):
        ''' Set the number of strands in ACC or ACSR cable '''
        self.strandNum = strandNum

    def getDiameter(self):
        ''' Return the strand diameter '''
        return self.diameter

    def setDiameter(self, diameter):
        ''' Set the diameter of the strand (mm) '''
        self.diameter = diameter

    def getMaterial(self):
        ''' Return the strand material '''
        return self.material

    def setMaterial(self, material):
        ''' Set the material of the strand '''
        self.material = material

    def getLength(self):
        ''' Return the length of the strand '''
        return self.length

    def setLength(self, length):
        ''' Set the strand length '''
        self.length = length

    def getLatitude(self):
        ''' Return the latitude of the GEP '''
        return self.latitude

    def setLatitude(self, latitude):
        ''' Set the latitude of the GEP '''
        self.latitude = latitude

    def getLongitude(self):
        ''' Return the longitude of the GEP '''
        return self.longitude

    def setLongitude(self, longitude):
        ''' Set the longitude of the GEP '''
        self.longitude = longitude

    def getCostPerMeter(self):
        ''' Return the cost per meter of the transmission line '''
        return self.costPerMeter

    def setCostPerMeter(self, costPerMeter):
        ''' Set the cost per meter of the transmission line '''
        self.costPerMeter = costPerMeter

    def getCost(self):
        ''' Return the total cost of the transmission line '''
        return self.costPerMeter * self.length

    def getDepRate(self):
        ''' Return the asset depreciation rate of the transmission line '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the asset depreciation rate of the transmission line '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# CIRCUIT BREAKER
# -------------------------------------------------------------------------------------------------------------------

class CircuitBreaker(object):
    ''' Class for storing information relating to a  circuit breaker '''
    def __init__(self, cost, depRate):
        ''' Initialise the circuit breaker class object '''
        self.cost = cost
        self.depRate = depRate

    def getCost(self):
        ''' Return the cost of a circuit breaker '''
        return self.cost

    def setCost(self, cost):
        ''' Set the cost of the circuit breaker '''
        self.cost = cost

    def getDepRate(self):
        ''' Return the depreciation rate of the circuit breaker '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the depreciation rate of the circuit breaker '''
        self.depRate = depRate

# -------------------------------------------------------------------------------------------------------------------
# SITE PARAMETERS
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
numTx = 3 # Number of transfromers
numArrays = 30 # Number of solar arrays
numCircuitBreakers = 15 # Number of circuit breakers
numInverters = 10 # Number of inverters

siteLat = 27.67 # Site latitude
siteLon = 85.42 # Site longitude
GXPLat = 27.70 # GXP latitude
GXPLon = 85.32 # GXP longitude

temp = []
irradiance = [] # Average solar irradiance perpendicular to the ground in W/m^2
sunlightHours = [] # Number of sunlight hours per day (could turn into a function)

# see pysolar for irradiance and temperature
for i in range(365):
    temp.append((-0.0005 * i**2) + (0.2138 * i) + 2.1976)
    irradiance.append((-0.021* i**2) + (8.5246 * i) + 74.471) # Formula calculated from data in source
    sunlightHours.append((-5e-11 * i**5) + (4e-8 * i**4) + (-1e-5 * i**3) + (6e-4 * i**2) + (2.99e-2 * i) + 6.0658)


siteArea = 1 # Site area in km^2

# Financial
breakerCost = 10000 # Cost of each circuit breakers
breakerDepRate = 6 # Circuit breaker depreciation rate (# per year)
landPrice = 100000 # Cost per km^2 of land
landAppRate = 3 # Land appreciation rate (# per year)

class Site(object):
    ''' Class that stores the information relating to the solar farm site '''
    def __init__(self, transformer, transformerNum, array, arrayNum, circuitBreaker, circuitBreakerNum, inverter,
        inverterNum, latitude, longitude, temperature, irradiance, sunlightHours, landPrice, landAppRate):
        ''' Initialise the solar farm site object '''
        self.transformer = transformer
        self.transformerNum = transformerNum
        self.array = array
        self.arrayNum = arrayNum
        self.circuitBreaker = circuitBreaker
        self.circuitBreakerNum = circuitBreakerNum
        self.inverter = inverter
        self.inverterNum = inverterNum
        self.latitude = latitude
        self.longitude = longitude
        self.temperature = temperature
        self.irradiance = irradiance
        self.sunlightHours = sunlightHours

        # Finanical properties
        self.landPrice = landPrice
        self.landAppRate = landAppRate

    def getTransformer(self):
        ''' Return the transformer used within the site '''
        return self.transformer

    def setTransformer(self, transformer):
        ''' Set the transformer type used within the site '''
        self.transformer = transformer

    def getTransformerNum(self):
        ''' Return the number of transformers within the site '''
        return self.transformerNum

    def setTransformerNum(self):
        ''' Set the number of transformers within the site '''
        self.transformerNum = transformerNum

    def getArray(self):
        ''' Return the array type used within the site '''
        return self.array

    def setArray(self, array):
        ''' Set the array type used within the site '''
        self.array = array

    def getArrayNum(self, array):
        ''' Return the number of arrays within the site '''
        return self.arrayNum

    def setArrayNum(self, arrayNum):
        ''' Set the number of arrays within the site '''
        self.arrayNum = arrayNum

    def getCircuitBreaker(self):
        ''' Return the circuit breaker type '''
        self.circuitBreaker

    def setCircuitBreaker(self, circuitBreaker):
        ''' Set the circuit breaker type '''
        self.circuitBreaker = circuitBreaker

    def getCircuitBreakerNum(self):
        ''' Return the number of circuit breakers within the site '''
        return self.circuitBreakerNum

    def setCircuitBreakerNum(self, circuitBreakerNum):
        ''' Set the number of circuit beakers within the site '''
        self.circuitBreakerNum = circuitBreakerNum

    def getInverter(self):
        ''' Return the inverter type '''
        return self.Inverter

    def setInverter(self, inverter):
        ''' Set the inverter type '''
        self.Inverter = inverter

    def getInverterNum(self):
        ''' Return the number of inverters '''
        return self.inverterNum

    def setInverterNum(self, inverterNum):
        ''' Set the number of inverters '''
        self.inverterNum = inverterNum

    def getLatitude(self):
        ''' Return the latitude of the site '''
        return self.latitude

    def setLatitude(self, latitude):
        ''' Set the latitude of the site '''
        self.latitude = latitude

    def getLongitude(self):
        ''' Return the longitude of the site '''
        return self.longitude

    def setLongitude(self, longitude):
        ''' Set the longitude of the site '''
        self.longitude = longitude

    def getTemperature(self):
        ''' Return the temperature of the site '''
        return self.temperature

    def setTemperature(self, temperature):
        ''' Set the temperature of the site '''
        self.temperature = temperature

    def getIrradiance(self):
        ''' Return the irradiance of the site '''
        return self.irradiance

    def setIrradiance(self, irradiance):
        ''' Set the irradiance of the site '''
        self.irradiance = irradiance

    def getSunlightHours(self):
        ''' Return the sunlight hours of the site '''
        return self.sunlightHours

    def setSunlightHours(self, sunlightHours):
        ''' Set the sunlight hours of the site '''
        self.sunlightHours = sunlightHours

    def getLandPrice(self):
        ''' Return the land price of the solar farm '''
        return self.landPrice

    def setLandPrice(self, landPrice):
        ''' Set the land price of the solar farm '''
        self.landPrice = landPrice

    def getLandAppRate(self):
        ''' Return the land appreciation rate '''
        return self.landAppRate

    def setLandAppRate(self):
        ''' Set the land appreciation rate '''
        self.landAppRate = landAppRate

# -------------------------------------------------------------------------------------------------------------------
# MISC FINANCIAL
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
maintainceBudget = 100000 # Maintaince budget per year
labourCosts = 500000      # Intial labour costs to build site
miscCapitalCosts = 500000 # Misc initial capital costs
miscDepRate = 8           # Misc depreciation rate (%/year)
buyBackRate = 0.25        # Selling rate of power ($/kWh)

class Financial(object):
    ''' Class that stores the information relating to the finanical data that is independent of the solar farm '''
    def __init__(self, maintenance, labour, capital, depRate, selling):
        ''' Initialise the Financial object '''
        self.maintenance = maintenance      # Maintaince budget per year
        self.labour = labour                # Initial labour costs to build site
        self.capital = capital              # Initial capital costs
        self.depRate = depRate              # Depreciation rate (%/year)
        self.selling = selling              # Selling rate of power (currency/kWh)

    def getMaintenance(self):
        ''' Return the maintenance budget per year '''
        return self.maintenance

    def setMaintenance(self, maintenance):
        ''' Set the maintenance budget per year '''
        self.maintenance = maintenance

    def getLabour(self):
        ''' Return the labour costs '''
        return self.labour

    def setLabour(self, labour):
        ''' Set the  labour costs '''
        self.labour = labour

    def getCapital(self):
        ''' Return the capital costs '''
        return self.capital

    def setCapital(self, capital):
        ''' Set the capital costs '''
        self.capital = capital

    def getDepRate(self):
        ''' Return the depreciation rate '''
        return self.depRate

    def setDepRate(self, depRate):
        ''' Set the depreciation rate '''
        self.depRate = depRate

    def getSelling(self):
        ''' Return the selling rate of power '''
        return self.selling

    def setSelling(self, selling):
        ''' Set the selling rate of power '''
        self.selling = selling

# -------------------------------------------------------------------------------------------------------------------
# SIMULATION DETAILS
# -------------------------------------------------------------------------------------------------------------------

# findPayBack = 0 # Find the payback period

# startDay = 13
# startMonth = 'November'
# startYear = 2013

# endDay = 28
# endMonth = 'February'
# endYear = 2016

# months = {'January' : 0, 'February' : 28, 'March' : 59, 'April': 89, 'May': 120, 
#           'June' : 150 , 'July': 181, 'August': 212, 'September': 242, 'October': 273, 
          'November':303, 'December':334}

# beginDay = startDay + months[startMonth] #daysMonths(bindex);

# if findPayBack == 0:
#     simLength = 365 * (endYear - startYear - 1) + (365 - beginDay) + months[endMonth]+ endDay
# else:
#     simLength = 50 * 365

class SimulationDay(object):
    ''' Contains a date object with a day to simulate, as well as the output data from the simulation'''
    def __init__(self, date):
        self.date = date
        self.outputData = []

    # def dateToIndex(date):
    #     ''' Returns the index of the day and the month of the datetime object given.
    #     The returned value is a tuple in the form (day, month) where the day is an integer
    #     between 0 and 364 and month is an integer 0 - 11 so they can be used an an array index'''
    #     # Get the date of the first day of the year
    #     startOfYear = datetime.date(date.year, 1, 1)
        
    #     # Calculate the day of the year as a value between 0 and 364
    #     dayOfYear = date - startOfYear
    #     dayOfYear = dayOfYear.days
        
    #     # Get the month of the year as an array index
    #     month = date.month - 1

    #     return (dayOfYear, month)

class Simulation(object):
    '''Object to contain the simulation parameters'''
    def __init__(self, start, finish, numThreads=5):
        ''' '''
        self.start = start
        self.finish = finish
        self.days = (start - finish).days
        self.numThreads = numThreads
        
        # Queues to store the input and output to the simulation
        self.inputDays = Queue.Queue()
        self.outputDays = Queue.Queue()

        # Queue up the list of days to simulate
        dates = [self.start - datetime.timedelta(days=self.days) for self.days in range(0,numdays)]
        for day in dates:
            simulationDay = SimlationDay(day)
            self.inputDays.put(simulationDay)


    def getStartDate(self):
        return self.start

    def setStartDate(self, date):
        self.start = date

    def getFinishDate(self):
        return self.finish

    def setFinishDate(self, date):
        self.finish = date



# -------------------------------------------------------------------------------------------------------------------


# if specifyLength == 0:
#     AC2Length = calc_length2(siteLat, siteLon, GXPLat, GXPLon)


# # Solar Panel calcs

# # Working the irradiance on the panel as a function of the day
# optimumAngle = calc_optimumAngle(irradiance, siteLat)

# panelIrr = []

# if useOptimumAngle == 1:
#     usedAngle = optimumAngle
# else:
#     usedAngle = arrayAngle

# for i in range(365):
#     argRadians = math.radians(360/365*(284 + i))
#     a = 90 - siteLat + 23.45 * math.sin(argRadians)

#     argRadians_1 = math.radians(a + usedAngle)
#     argRadians_2 = math.radians(a)
#     panelIrr.append(irradiance[i] * math.sin(argRadians_1) / math.sin(argRadians_2))


# # plot(panelIrr)

# # Initialise data arrays

# solarOutput = list(range(simLength))
# DCoutput = list(range(simLength))
# invOutput = list(range(simLength))
# AC1Output = list(range(simLength))
# TxOut = list(range(simLength))
# AC2Output = list(range(simLength))
# totalEffeciency = list(range(simLength))
# elecEff = list(range(simLength))
# energyOutput = list(range(simLength))

# capitalWorth = list(range(50))


# day = beginDay - 1
# days = list(range(simLength))
# year = 0
# numPanels = moduleNum*arrayModuleNum*numArrays        
# totalArea = panelArea*numPanels




class CalculateDay(threading.Thread):
    
    def __init__(self, inputQueue, outputQueue):
        ''' Takes an input of SimulationDay objects, runs the simulation for that day and stores the result
        inside the SimulationDay object before pushing it to the output queue'''
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
    
    def run(self):
        while True:
            # Check if there are any more days to simulate
            if self.inputQueue.empty()
                return

            
            # TODO: Add simulation parameters
            # solarVoltage = 0, totalArea panelEff
            # temperature = 0
            # DCcableMaterial, DCdiameter, DCcableLength, InvEff,TxEff
            # AC1Material, AC1Diameter, AC1Length, InvPowerFactor*InvOutVolt
            # AC2Material, AC2StrandDiameter, AC2Length, AC2StrandNum, TxOutVolt
            lat = 1
            lng = 1

            # Date to simulate irradiance
            simulationDay = self.inputQueue.get()
            year = simulationDay.date.year
            month = simulationDay.date.month
            day = simulationDay.date.day

            # Constants
            SIMULATION_TIMESTEP_MINS = 30
            MINS_PER_DAY = 1440.00 #      Make it a float so it divides nicely
            STEPS_PER_DAY = int(MINS_PER_DAY / SIMULATION_TIMESTEP_MINS)

            # Running totals for the total output energy effciencies at each timestep
            energyOutput = 0
            totalEffeciency = 0
            elecEff = 0

            # Simulate the irradiance over a day in half hour increments
            for i in range(STEPS_PER_DAY):        
                # Create a datetime to represent the time of day on the given date
                minutesIntoDay = i * SIMULATION_TIMESTEP_MINS
                d = datetime.datetime(year, month, day) + datetime.timedelta(minutes=minutesIntoDay)

                # Get the sun altitude and irrandiance for the day using Pysolar
                altitude = Pysolar.GetAltitude(lat, lng, d)
                irradiance = Pysolar.radiation.GetRadiationDirect(d, altitude)

                # Calculates the solar power in W for a whole day
                solarOutput = irradiance * totalArea * panelEff  # TODO: DEGREDATION RATE (1 - panelDegRate / (100*365) * i)
        
                # DC cable calcs
                DCresistance = calc_resistance(DCcableMaterial, temperature, DCdiameter, DCcableLength)
                DCcurrent = solarOutput / solarVoltage # TODO find this constant solarVoltage
                DCloss = 2 * DCcurrent**2 * DCresistance
                DCoutput = solarOutput - DCloss
            
                # Inverter calcs
                invOutput = DCoutput * InvEff

                # 3 Phase AC Cables to Tx calcs
                AC1resistance = calc_resistance(AC1Material, temperature, AC1Diameter, AC1Length)
                IAC1 = invOutput / (math.sqrt(3) * InvPowerFactor*InvOutVolt)
                AC1loss = 3 * IAC1**2 * AC1resistance
                AC1Output = invOutput - AC1loss
                

                # Transformer calcs
                TxOut = AC1Output * TxEff
                

                # 3 Phase tranmission lines to GXP calcs
                strandResistance = calc_resistance(AC2Material, temperature, AC2StrandDiameter, AC2Length)
                totalResistance = strandResistance / AC2StrandNum
                IAC2 = TxOut / (math.sqrt(3) * InvPowerFactor * TxOutVolt)
                AC2loss = 3 * IAC2**2 * totalResistance
                AC2Output = TxOut - AC2loss
                
                # Final outputs
                totalEffeciency += (AC2Output / (irradiance * totalArea)) * 100
                elecEff += (AC2Output / solarOutput) * 100
                energyOutput += AC2Output * (float(SIMULATION_TIMESTEP_MINS) / 60) # Daily output in Wh


            # Average the effciencies over the day
            totalEffeciency /= STEPS_PER_DAY
            elecEff /= STEPS_PER_DAY
            


            #-------------Finicial-----------------------------------------------#
            # if day == startDay and i != 1:
            #     # Calculate finicial data
            #     year = year + 1
            #     capitalWorth = landPrice * siteArea * (1+landAppRate/100)**year 
            #     capitalWorth += panelCost * numPanels * (1-panelDepRate/100)**year + DCcostPerMeter*DCcableLength*(1-DCDepRate/100)**year
            #     capitalWorth += InvCost*numInverters*(1-InvDepRate/100)**year + AC1Cost*AC1Length*(1-AC1DepRate/100)**year
            #     capitalWorth += TxCost*(1-TxDepRate/100)**2 + (AC2Cost + TranLineCost)*AC2Length*(1-AC2DepRate/100)**year
            #     capitalWorth += miscCapitalCosts*(1-miscDepRate/100)**year
                
            #     expenses = maintainceBudget*year + labourCosts
            #     totalIncome = sum(energyOutput)/1000*buyBackRate
                
            #     if (totalIncome > (expenses + capitalWorth(1)))
            #         break
                
            
            # elif i == 1:
            #     # Initial Capital Worth
            #     capitalWorth[year + 1] = landPrice*siteArea + panelCost*numPanels
            #     capitalWorth += DCcostPerMeter*DCcableLength + InvCost*numInverters
            #     capitalWorth += AC1Cost*AC1Length + TxCost + (AC2Cost + TranLineCost)*AC2Length
            #     capitalWorth += miscCapitalCosts
            
            #---------------------------------------------------------------------#
    

# t = range(len(solarOutput))
# plt.plot(t, solarOutput, t, DCoutput)
# plt.show()

