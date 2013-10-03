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
import math
import matplotlib.pyplot as plt
import numpy
import time

start = time.time()

def calc_length2(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    latAverage = math.radians( (lat1+lat2) / 2 )
    length = R * math.sqrt((dlat)**2 + (math.cos(latAverage) * dlon) **2)
    return length



def calc_optimumAngle(directIrr, siteLat):

    testAngle = [x * 0.1 for x in range(0, 90)]  # [0:0.1:90]
    angleLength = len(testAngle)
    
    meanIrr = list(range(angleLength))

    for i in range(angleLength):
        yearlyIrradiance = []

        for j in range(365):
            argRadians = math.radians(360/365*(284 + j))
            a = 90 - siteLat + 23.45 * math.sin(argRadians)
            
            argRadians_1 = math.radians(a + testAngle[i])
            argRadians_2 = math.radians(a)

            yearlyIrradiance.append(directIrr[j] * math.sin(argRadians_1) / math.sin(argRadians_2))
        
        meanIrr[i] = numpy.mean(yearlyIrradiance)
    

    ind = meanIrr.index(max(meanIrr))

    opAngle = testAngle[ind]

    return opAngle


def calc_resistance(mat, temp, diameter, length):

    if mat == 'Cu':
        p = 1.68e-8*(1 + 0.00362*(temp-20))
    elif mat == 'Al':
        p = 2.82e-8*(1 + 0.0039*(temp-20))
    
     
    area = math.pi / 4*(diameter*1e-3)**2
     
    resistance = p*length/area
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
panelDepRate = 20 # Panel depreciation rate (# per year)


class PVPanel(object):
    ''' Class to store information relating to a solar PV panel '''
    def __init__(self, voltage, efficiency, degradationRate, area):
        ''' Initialise a PV panel object '''
        self.voltage = voltage                  # Panel rated voltage (V)
        self.efficiency = efficiency            # Panel rated efficiency (%)
        self.degradationRate = degradationRate  # Panel asset degradation rate (%)
        self.area = area                        # Panel surface area (m^2)

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
    def __init__(self, diameter, material, length):
        self.diameter = diameter    # Diameter of the cable (mm)
        self.material = material    # Material of the conductor within the cable (e.g. Cu, Al)
        self.length = length        # Length of the total amount of cable

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

class Material(object):
    ''' Class object for a material '''
    def __init__(self, name, resistivity):
        self.name = name
        self.resistivity = resistivity

    def getResistivity(self):
        ''' Return the resistivity of the material '''
        return self.resistivity

    def setResistivity(self, resistivity):
        ''' Sets the resistivity of the material '''
        self.resistivity = resistivity

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
    def __init__(self, powerFactor, efficiency, voltage):
        self.powerFactor = powerFactor  # Power factor of the inverter
        self.efficiency = efficiency    # Efficiency of the inverter
        self.voltage = voltage          # Output voltage of the inverter to the transformer

    def getPowerFactor(self):
        ''' Return the power factor '''
        return self.powerFactor

    def setPowerFactor(self, powerFactor):
        ''' Set the power factor of the inverter '''
        self.powerFactor = powerFactor
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

# -------------------------------------------------------------------------------------------------------------------
# GXP LINES
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

# -------------------------------------------------------------------------------------------------------------------
# MISC FINANCIAL
# -------------------------------------------------------------------------------------------------------------------

# Deprecated variables
maintainceBudget = 100000 # Maintaince budget per year
labourCosts = 500000 # Intial labour costs to build site
miscCapitalCosts = 500000# Misc initial capital costs
miscDepRate = 8 # Misc depreciation rate (# per year)
buyBackRate = 0.25 # Selling rate of power ($/kWh)

# -------------------------------------------------------------------------------------------------------------------
# SIMULATION DETAILS
# -------------------------------------------------------------------------------------------------------------------

findPayBack = 0 # Find the payback period

startDay = 13
startMonth = 'November'
startYear = 2013

endDay = 28
endMonth = 'February'
endYear = 2016

months = {'January' : 0, 'February' : 28, 'March' : 59, 'April': 89, 'May': 120, 
          'June' : 150 , 'July': 181, 'August': 212, 'September': 242, 'October': 273, 
          'November':303, 'December':334}
# daysMonths = [0, 28, 59, 89, 120, 150, 181, 212, 242, 273, 303, 334];

# bindex = find(ismember(months, startMonth));

# dindex = find(ismember(months, endMonth));

beginDay = startDay + months[startMonth] #daysMonths(bindex);

if findPayBack == 0:
    simLength = 365 * (endYear - startYear - 1) + (365 - beginDay) + months[endMonth]+ endDay
else:
    simLength = 50 * 365

# -------------------------------------------------------------------------------------------------------------------


if specifyLength == 0:
    AC2Length = calc_length2(siteLat, siteLon, GXPLat, GXPLon)


# Solar Panel calcs

# Working the irradiance on the panel as a function of the day
optimumAngle = calc_optimumAngle(irradiance, siteLat)

panelIrr = []

if useOptimumAngle == 1:
    usedAngle = optimumAngle
else:
    usedAngle = arrayAngle

for i in range(365):
    argRadians = math.radians(360/365*(284 + i))
    a = 90 - siteLat + 23.45 * math.sin(argRadians)

    argRadians_1 = math.radians(a + usedAngle)
    argRadians_2 = math.radians(a)
    panelIrr.append(irradiance[i] * math.sin(argRadians_1) / math.sin(argRadians_2))


# plot(panelIrr)



# Initialise data arrays

solarOutput = list(range(simLength))
DCoutput = list(range(simLength))
invOutput = list(range(simLength))
AC1Output = list(range(simLength))
TxOut = list(range(simLength))
AC2Output = list(range(simLength))
totalEffeciency = list(range(simLength))
elecEff = list(range(simLength))
energyOutput = list(range(simLength))

capitalWorth = list(range(50))


day = beginDay - 1
days = list(range(simLength))
year = 0
numPanels = moduleNum*arrayModuleNum*numArrays        
totalArea = panelArea*numPanels

for i in range(simLength):
    
    days[i] = day + 1 
    
    #---------------------Power/Energy Analysis---------------------------#    
    
    solarOutput[i] = panelIrr[day] * totalArea * panelEff * (1 - panelDegRate / (100*365) * i)
    
    # DC cable calcs
    
    DCresistance = calc_resistance(DCcableMaterial, temp[day], DCdiameter, DCcableLength)
    
    DCcurrent = solarOutput[i] / solarVoltage
    
    DCloss = 2 * DCcurrent**2 * DCresistance
    
    DCEff = (solarOutput[i] - DCloss) / solarOutput[i]
    
    DCoutput[i] = solarOutput[i] - DCloss
    
    # Inverter calcs
    
    invOutput[i] = DCoutput[i] * InvEff
    
    # 3 P AC Cables to Tx calcs
    
    AC1resistance = calc_resistance(AC1Material, temp[day], AC1Diameter, AC1Length)

    IAC1 = invOutput[i] / (math.sqrt(3) * InvPowerFactor*InvOutVolt)
    
    AC1loss = 3 * IAC1**2 * AC1resistance
    
    AC1Output[i] = invOutput[i] - AC1loss
    
    # Transformer calcs
    
    TxOut[i] = AC1Output[i] * TxEff
    
    # 3 P tranmission lines to GXP calcs
    
    strandResistance = calc_resistance(AC2Material, temp[day], AC2StrandDiameter, AC2Length)
    
    totalResistance = strandResistance / AC2StrandNum
    
    IAC2 = TxOut[i] / (math.sqrt(3) * InvPowerFactor * TxOutVolt)
    
    AC2loss = 3 * IAC2**2 * totalResistance
    
    AC2Output[i] = TxOut[i] - AC2loss
    
    totalEffeciency[i] = (AC2Output[i] / (panelIrr[day]*totalArea)) * 100
    
    elecEff[i] = (AC2Output[i] / solarOutput[i]) * 100
    
    energyOutput[i] = AC2Output[i] * sunlightHours[day] # Daily output in Wh
    
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
    
    if day < 364:
        day += 1
    else:
        day = 0    
        
print "Simulation took %.3fs" % (time.time() - start)
# income = sum(energyOutput)*buyBackRate;
t = range(len(solarOutput))
plt.plot(t, solarOutput, t, DCoutput)
plt.show()

