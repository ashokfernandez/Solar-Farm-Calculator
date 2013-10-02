# Author: Darren O'Neill    Date: 20/09/2013
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



#-------------------Solar Panels-------------------------------#

panelVoltage = 30.5 # Voltage of the panel at maximum power point
panelEff = 0.15 # Solar panel effeciency (typically 15-18 #)
panelDegRate = 0.4 # Rate at which the solar panel degradates (# per year)
panelArea = 1.63 # Panel area (m^2)


# Finacial
panelCost = 50 # Cost of the single panel
panelDepRate = 20 # Panel depreciation rate (# per year)


#------------------Solar Module--------------------------------#

moduleNum = 20 # Number of solar panels in a module

solarVoltage = panelVoltage * moduleNum


#----------------Array Parameters------------------------------#

arrayModuleNum = 7 # Number of modules that make up an array (modlues are in parrallel)
arrayAngle = 45 # Angle from panel to horizontal
useOptimumAngle = 1

#-----------------------DC cables------------------------------#

DCdiameter = 20 # DC cable diameter in mm
DCcableMaterial = 'Cu' # DC cable conductor material
DCcableLength = 100 # DC cable length in meters

# Finacial
DCcostPerMeter = 100 # Cost of DC cable per meter
DCDepRate = 6 # DC cable depreciation rate (# per year)

#---------------------Inverter---------------------------------#

InvPowerFactor = 0.95 # Power factor of the output of the inverter
InvEff = 0.85 # Inverter effeciency (typicall loss 4-15 #)
InvOutVolt = 400 # Output voltage of the inverter (line to line)

# Finicial
InvCost = 10000 # Cost of the inverter/s
InvDepRate = 7 # Inverter depreciation rate (# per year)

#--------------------Inv-Tx Lines (AC1 Cables)-----------------#

AC1Diameter = 6 # Inv-Tx line cable diameter
AC1Material = 'Al' # Inv-Tx cable material
AC1Length = 100 # Length of the Inv-Tx cable

# Finicial

AC1Cost = 100 # Cost of cable per meter
AC1DepRate = 6 # Inv-Tx cable depreciation rate (# per year)

#-----------------Transformer----------------------------------#

TxOutVolt = 11e3 # Transformer secondary voltage
TxEff = 0.95 # Transformer efficiency
TxRating = 3 # MVA rating

# Financial

TxCost = 1000000 # Cost of the transformer
TxDepRate = 6 # Transformer depreciation rate (# per year)
TxScrap = 30000 # Transformer scrap value

#-----------------GXP Lines------------------------------------#

AC2StrandNum = 5 # Number of strands in ACC or ACSR cable
AC2StrandDiameter = 2 # Strand diameter in mm
AC2Material = 'Al' # Strand material
specifyLength = 0
AC2Length = 0



# Finacial
AC2Cost = 100 # Cost of SINGLE cable per meter
TranLineCost = 1000 # Cost of building the transmission line per kilometer
AC2DepRate = 6 # Depreciation rate of the GXP line (# per year)

#----------------Site Parameters--------------------------------#

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

# Finicial
breakerCost = 10000 # Cost of each circuit breakers
breakerDepRate = 6 # Circuit breaker depreciation rate (# per year)
landPrice = 100000 # Cost per km^2 of land
landAppRate = 3 # Land appreciation rate (# per year)

#------------------------Other Finicial-------------------------#

maintainceBudget = 100000 # Maintaince budget per year
labourCosts = 500000 # Intial labour costs to build site
miscCapitalCosts = 500000# Misc initial capital costs
miscDepRate = 8 # Misc depreciation rate (# per year)
buyBackRate = 0.25 # Selling rate of power ($/kWh)

#--------------------Simulation Details------------------------#

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

#------------------------------------------------------------------------#


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

