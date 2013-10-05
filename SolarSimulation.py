# --------------------------------------------------------------------------------------------------
# SolarSimulation : Solar farm model simulator
# --------------------------------------------------------------------------------------------------
# Author: Darren O'Neill
# Author: Jarrad Raumati 
# Author: Ashok Fernandez
# Date: 20/09/2013
#
# This script simulates a solar farm to obtain the effeciency of a given
# location
# --------------------------------------------------------------------------------------------------

import operator
import Pysolar
import Queue
import threading
import math
import matplotlib.pyplot as plt
import numpy
import time
import datetime
import PyExchangeRates

# For the progress bar in the console when the scraping operation is happening
from time import sleep
import progressbar # https://pypi.python.org/pypi/progressbar/

# Create a currency exchange
CURRENCY_EXCHANGE = PyExchangeRates.Exchange('843ce8fdc22c47779fb3040c2ba9a586')


def calcLength(lat1, lng1, lat2, lng2):
    ''' Calculates the distance between two latitude and longtitude points in meters. '''
    R = 6371 # radius of the earth (km) TODO: Citation needed

    # Calculate the latitude / longitude difference in radians
    dlat = math.radians(lat1 - lat2)
    dlon = math.radians(lng1 - lng2)
    
    # Average latitude in radians
    latAverage = math.radians((lat1+lat2) / 2)

    # The linear distance between the site and the GEP in m
    length = R * math.sqrt((dlat) ** 2 + (math.cos(latAverage) * dlon) ** 2) * 1000

    return length

def calcOptimumAngle(directIrr, siteLat):
    ''' Calculates the optimum angle of the PV panels based on the latitude of the site. '''
    # [0:0.1:90] specifices angle between 0 and 90 degrees
    # testAngle = [x * 0.1 for x in range(0, 90)]
    # angleLength = len(testAngle) # length of test angle array
    
    # meanIrr = list(range(angleLength)) # init array for length for mean irradiance

    # # iterates through each angle and calculates the mean irradiance for that year
    # for i in range(angleLength):
    #     yearlyIrradiance = []

    #     for j in range(365):
    #         # This simulates a year of how much irradiance is incident on a panel surface.
            
    #         # arbitary angle that is used for calculating the irradiance
    #         argRadians = math.radians(360/365*(284 + j))
    #         # same as above for the next 3 lines
    #         a = 90 - site.getLatitude() + 23.45 * math.sin(argRadians)
    #         argRadians_1 = math.radians(a + testAngle[i])
    #         argRadians_2 = math.radians(a)

    #         # Calculates the irradiance on the panel for a day
    #         yearlyIrradiance.append(directIrr[j] * math.sin(argRadians_1) / math.sin(argRadians_2))
        
    #     # Take the mean irradiance and stores within an array
    #     meanIrr[i] = numpy.mean(yearlyIrradiance)
    
    # # Takes the angle with the highest average irradiance
    # ind = meanIrr.index(max(meanIrr))

    # #the optimum angle for solar panel
    # opAngle = testAngle[ind]

    # Taken from "Interconnecting Issues of PV/Wind Hybrid System with Electric Utility, 2011"
    declinationAngle = 23.45 * math.sin(360 * (284 + 30) / 365)
    monthlyBestTiltAngle = siteLat - declinationAngle

    return monthlyBestTiltAngle

def calcCableResistance(cable, temperature):
    ''' Calculates the resistance of a cable given the cable material, ambient temperature,
        diameter and length. '''

    # Uses base temperature of 20 degrees celcius to correct the resistivity for the ambient
    # temperature.
    caliResistivity = cable.material.getResistivity()*(1 +
        cable.material.getTempCoefficient()*(temperature-20))
    
    # area of the cable
    area = math.pi / 4 * (cable.getDiameter() * 1e-3) ** 2
    resistance = caliResistivity * cable.getLength() / area

    return resistance

# --------------------------------------------------------------------------------------------------
# ASSET SUPERCLASS
# --------------------------------------------------------------------------------------------------
class Asset(object):
    ''' Asset superclass for PV farm components. Contains the financial data relating to the
        asset. '''
    exchange = CURRENCY_EXCHANGE

    def __init__(self, cost, currency, depRate = 0):
        ''' Initialise the asset superclass object. '''
        self.cost = self.exchange.withdraw(cost, currency)   # Cost (currency/unit)
        self.depRate = depRate                               # Asset deprecation rate (%)

    def getCost(self):
        ''' Return the cost of the asset. '''
        return self.cost

    def getDepreciatedValue(self, timedelta):
        ''' Returns the assets value factoring in depreciation over the given time. '''
        # converts depreciation rate to per day and timedelta has to be num days
        return self.cost*(1-self.depRate/(365*100))**timedelta

    def getDepRate(self):
        ''' Return the asset depreciation rate of the asset. '''
        return self.depRate

    def getCurrency(self):
        ''' Return the currency of the asset's cost. '''
        return self.cost.getCurrencyKey()

# --------------------------------------------------------------------------------------------------
# SOLAR PANELS
# --------------------------------------------------------------------------------------------------
class PVPanel(Asset):
    ''' Class to store information relating to a solar PV panel. '''
    def __init__(self, voltage, efficiency, degradationRate, area, cost, currency = 'USD',
            depRate = 0):
        ''' Initialise a PV panel object. '''
        self.voltage = voltage                  # Panel rated voltage (V)
        self.efficiency = efficiency            # Panel rated efficiency (%)
        self.degradationRate = degradationRate  # Panel asset degradation rate (%)
        self.area = area                        # Panel surface area (m^2)

        # Financial properties
        super(PVPanel, self).__init__(cost, currency, depRate)

    def getVoltage(self):
        ''' Return the panel voltage. '''
        return self.voltage

    def getEfficiency(self):
        ''' Return the panel efficiency between 0 and 1 (converts from a percentage). '''
        return self.efficiency / 100.0

    def getDegradationRate(self):
        ''' Return the panel asset degradation rate. '''
        return self.degradationRate

    def getArea(self):
        ''' Return the panel surface area. '''
        return self.area

# --------------------------------------------------------------------------------------------------
# SOLAR MODULE
# --------------------------------------------------------------------------------------------------
class PVModule(Asset):
    ''' Class to store information relating to a solar PV module. A module contains PV panels. '''
    def __init__(self, panelType, panelNum):
        ''' Initialise a PV module object. '''
        self.panelType = panelType      # Type of panel within the module
        self.panelNum = panelNum        # Number of panels within the module
        self.voltage = None             # Total voltage of the module (panels connected in series)

        # Financial properties
        super(PVModule, self).__init__(panelType.getCost() * panelNum, panelType.getCurrency(),
            panelType.getDepRate())
        self.__calculateModuleVoltage()

    def __calculateModuleVoltage(self):
        ''' Calculate the total voltage of the module. '''
        self.voltage = self.panelType.getVoltage() * self.panelNum        

    def getPanelType(self):
        ''' Return the panel object within the module. '''
        return self.panelType

    def getVoltage(self):
        ''' Return the module voltage. '''
        return self.voltage

    def getArea(self):
        '''Calculates the total area of the panels in m^2. '''
        return self.panelType.getArea() * self.panelNum

# --------------------------------------------------------------------------------------------------
# SOLAR ARRAY
# --------------------------------------------------------------------------------------------------
class PVArray(Asset):
    ''' Class to store the information relating to a PV array. An array contains PV modules. '''
    def __init__(self, moduleType, moduleNum, arrayAngle):
        ''' Initialise a PV array object. '''
        self.moduleType = moduleType    # Type of module within the array
        self.moduleNum = moduleNum      # Number of modules in the array in parallel connection
        self.angle = arrayAngle         # Angle of the PV panels
        self.voltage = None             # Array voltage

        # Financial properties
        super(PVArray, self).__init__(moduleType.getCost() * moduleNum, moduleType.getCurrency(),
            moduleType.getDepRate())
        self.__CalculateArrayVoltage()

    def __CalculateArrayVoltage(self):
        ''' Calculates the total voltage of the PV array. '''
        self.voltage = self.moduleType.getVoltage()

    def getModuleType(self):
        ''' Return the module type within the array. '''
        return self.moduleType

    def getModuleNum(self):
        ''' return the number of modules within the array. '''
        return self.moduleNum

    def getVoltage(self):
        ''' Return the voltage of the array. '''
        return self.voltage

    def getAngle(self):
        ''' Return the angle of the PV panels. '''
        return self.angle

    def getArea(self):
        ''' Calculates the total area of the panels in m^2. '''
        return self.moduleType.getArea() * self.moduleNum

# --------------------------------------------------------------------------------------------------
# MATERIAL
# --------------------------------------------------------------------------------------------------
class Material(object):
    ''' Class object for a material. '''
    def __init__(self, name, resistivity, tempCoefficient):
        ''' Initialise a material object. '''
        self.name = name
        self.resistivity = resistivity
        self.tempCoefficient = tempCoefficient

    def getResistivity(self):
        ''' Return the resistivity of the material. '''
        return self.resistivity

    def getTempCoefficient(self):
        ''' Return the temperature coefficient of the material. '''
        return self.tempCoefficient

# --------------------------------------------------------------------------------------------------
# DC CABLE
# --------------------------------------------------------------------------------------------------
class DCCable(Asset):
    ''' Class to store the information relating to the DC cable between the PV array and the
        inverter. '''
    def __init__(self, diameter, material, length, costPerMeter, currency = 'USD', depRate = 0):
        ''' Initialise a DC cable object. '''
        self.diameter = diameter            # Diameter of the cable (mm)
        self.material = material            # Material of the conductor within the cable (e.g. Cu, Al)
        self.length = length                # Length of the total amount of cable

        # Financial properties
        super(DCCable, self).__init__(costPerMeter * length, currency, depRate)

    def getDiameter(self):
        ''' Return the cable diameter. '''
        return self.diameter

    def getMaterial(self):
        ''' Return the cable material. '''
        return self.material

    def getLength(self):
        ''' Return the length of the cable. '''
        return self.length

# --------------------------------------------------------------------------------------------------
# INVERTER
# --------------------------------------------------------------------------------------------------
class Inverter(Asset):
    ''' Class to store the information relating to the Inverter. '''
    def __init__(self, powerFactor, efficiency, voltage, cost, currency = 'USD', depRate = 0):
        '''Initialise an inverter object. '''
        self.powerFactor = powerFactor  # Power factor of the inverter
        self.efficiency = efficiency    # Efficiency of the inverter
        self.voltage = voltage          # Output voltage of the inverter to the transformer

        # Financial properties
        super(Inverter, self).__init__(cost, currency, depRate)

    def getPowerFactor(self):
        ''' Return the power factor. '''
        return self.powerFactor

    def getEfficiency(self):
        ''' Return the efficiency of the inverter between 0 and 1. '''
        return self.efficiency / 100.0

    def getVoltage(self):
        ''' Return the output voltage of the inverter. '''
        return self.voltage

# --------------------------------------------------------------------------------------------------
# Inv-Tx Lines (AC1 Cables)
# --------------------------------------------------------------------------------------------------
class AC1Cable(Asset):
    ''' Class that stores the information relating to the AC cable
    between the inverter and the transformer. '''
    def __init__(self, strandNum, diameter, material, length, costPerMeter, currency = 'USD',
        depRate = 0):
        ''' Initialise the AC cable object. '''
        self.strandNum = strandNum
        self.diameter = diameter
        self.material = material
        self.length = length

        # Financial properties
        super(AC1Cable, self).__init__(costPerMeter * length, currency, depRate)

    def getStrandNum(self):
        ''' Return the number of strands for the AC1 cable. '''
        return self.strandNum

    def getDiameter(self):
        ''' Return the cable diameter. '''
        return self.diameter

    def getMaterial(self):
        ''' Return the cable material. '''
        return self.material

    def getLength(self):
        ''' Return the length of the cable. '''
        return self.length

# --------------------------------------------------------------------------------------------------
# TRANSFORMER
# --------------------------------------------------------------------------------------------------
class Transformer(Asset):
    ''' Class that stores the information relating to a transformer. '''
    def __init__(self, voltage, efficiency, VARating, cost, currency = 'USD', depRate = 0,
        scrapValue = 0):
        ''' Initialise the transformer object '''
        self.voltage = voltage
        self.efficiency = efficiency
        self.VARating = VARating

        # Financial properties
        super(Transformer, self).__init__(cost, currency, depRate)
        self.scrapValue = scrapValue

    def getVoltage(self):
        ''' Return the high voltage side of the transformer '''
        return self.voltage

    def getEfficiency(self):
        ''' Return the efficiency of the transformer between 0 and 1 '''
        return self.efficiency / 100.0

    def getVARating(self):
        ''' Return the rating of the transformer (MVA) '''
        return self.VARating

    def getScrapValue(self):
        ''' Return the scrap value of the cable '''
        return self.scrapValue

# --------------------------------------------------------------------------------------------------
# AC2 LINES (TX Line)
# --------------------------------------------------------------------------------------------------
class AC2Cable(Asset):
    ''' Class that stores the information relating the transmission line between the solar farm and
    the grid entry point '''
    def __init__(self, strandNum, diameter, material, length, costPerMeter, currency = 'USD',
        depRate = 0):
        ''' Initialise the GEP object '''
        self.strandNum = strandNum
        self.diameter = diameter
        self.material = material
        self.length = length        # Length of cable in meters
        
        # Financial properties
        super(AC2Cable, self).__init__(costPerMeter * length, currency, depRate)

    def getStrandNum(self):
        ''' Return the number of strands in ACC or ACSR cable '''
        return self.strandNum

    def getDiameter(self):
        ''' Return the strand diameter '''
        return self.diameter

    def getMaterial(self):
        ''' Return the strand material '''
        return self.material

    def getLength(self):
        ''' Return the length of the strand '''
        return self.length

# --------------------------------------------------------------------------------------------------
# CIRCUIT BREAKER
# --------------------------------------------------------------------------------------------------
class CircuitBreaker(Asset):
    ''' Class for storing information relating to a  circuit breaker '''
    def __init__(self, cost, currency = 'USD', depRate = 0):
        ''' Initialise the circuit breaker class object '''
        super(CircuitBreaker, self).__init__(cost, currency, depRate)

# --------------------------------------------------------------------------------------------------
# SITE PARAMETERS
# --------------------------------------------------------------------------------------------------
class Site(Asset):
    ''' Class that stores the information relating to the solar farm site '''
    def __init__(self, transformerNum, arrayNum, circuitBreakerNum, inverterNum, 
                 latitude, longitude, temperature, landPrice, landAppRate=0, currency='USD'):
        ''' Initialise the solar farm site object '''
        self.transformerNum = transformerNum
        self.arrayNum = arrayNum
        self.circuitBreakerNum = circuitBreakerNum
        self.inverterNum = inverterNum
        self.temperature = temperature
        self.landPrice = landPrice
        self.landAppRate = landAppRate
        self.latitude = latitude
        self.longitude = longitude

        # Financial properties
        super(Site, self).__init__(landPrice, currency, -landAppRate)

    def getTransformerNum(self):
        ''' Return the number of transformers within the site '''
        return self.transformerNum

    def getArrayNum(self):
        ''' Return the number of arrays within the site '''
        return self.arrayNum

    def getCircuitBreakerNum(self):
        ''' Return the number of circuit breakers within the site '''
        return self.circuitBreakerNum

    def getInverterNum(self):
        ''' Return the number of inverters '''
        return self.inverterNum

    def getLatitude(self):
        ''' Return the site latitude '''
        return self.latitude

    def getLongitude(self):
        ''' Return the site longitude '''
        return self.longitude

    def getTemperature(self, month):
        ''' Get the temperature of the site during the given month, months are specified
        as 1 for January and 12 for December '''
        return self.temperature[month - 1]


# --------------------------------------------------------------------------------------------------
# MISC FINANCIAL----------------
# --------------------------------------------------------------------------------------------------

# Deprecated variables
# maintainceBudget = 100000 # Maintaince budget per year
# labourCosts = 500000      # Intial labour costs to build site
# miscCapitalCosts = 500000 # Misc initial capital costs
# miscDepRate = 8           # Misc depreciation rate (# per year)
# buyBackRate = 0.25        # Selling rate of power ($/kWh)

class Financial(object):
    ''' Class that stores the information relating to the finanical data that is independent of the
    solar farm '''
    exchange = CURRENCY_EXCHANGE

    def __init__(self, maintenance, miscExpenses, interestRate, powerPrice, baseCurrency='USD'):
        ''' Initialise the Financial object '''
        self.baseCurrency = baseCurrency         # Base currency that results are returned in
        self.interestRate = interestRate                                               # Interest rate (%/year)
        self.maintenance = Financial.exchange.withdraw(maintenance,self.baseCurrency)  # Maintaince budget per year
        self.loan = Financial.exchange.withdraw(miscExpenses,self.baseCurrency)        # + assets 
        self.powerPrice = Financial.exchange.withdraw(powerPrice,self.baseCurrency)    # Selling rate of power (currency/kWh)
        

    def getDailyMaintenance(self):
        ''' Return the maintenance budget per year '''
        return self.maintenance / 365.0

    def addToLoan(self, cost):
        ''' Adds money to the initial cost '''
        self.loan += cost
        self.loan.convert(self.baseCurrency)

    def makeLoanPayment(self, payment):
        ''' Pays back money to the loan for the initial costs '''
        self.loan -= payment
        self.loan.convert(self.baseCurrency)

    def accumlateDailyInterest(self):
        ''' Adds interest to the intial expenses loan '''
        if self.loan.getAmount() > 0:
            self.loan *= (1 + self.interestRate/(365*100))
            self.loan.convert(self.baseCurrency)

    def getCurrentLoanValue(self):
        ''' Returns the current value of the loan '''
        return self.loan.getAmount()

    def getPowerPrice(self):
        ''' Return the selling rate of power '''
        return self.powerPrice

# --------------------------------------------------------------------------------------------------
# SIMULATION DETAILS
# --------------------------------------------------------------------------------------------------

# if findPayBack == 0:
#     simLength = 365 * (endYear - startYear - 1) + (365 - beginDay) + months[endMonth]+ endDay
# else:
#     simLength = 50 * 365
class thread_SimulateDay(threading.Thread):
    def __init__(self, inputQueue, outputQueue, timestep_mins):
        ''' Takes an input of SimulationDay objects, runs the simulation for that day and stores
        the result inside the SimulationDay object before pushing it to the output queue'''
        threading.Thread.__init__(self)
        self.timestep_mins = timestep_mins
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
    
    def run(self):
        while True:
            # Check if there are any more days to simulate
            if self.inputQueue.empty():
                return

            # Date to simulate irradiance
            simDay = self.inputQueue.get()
            year = simDay.date.year
            month = simDay.date.month
            day = simDay.date.day

            # Time steps
            SIMULATION_TIMESTEP_MINS = self.timestep_mins
            MINS_PER_DAY = 1440.00 #             Make it a float so it divides nicely
            STEPS_PER_DAY = int(MINS_PER_DAY / SIMULATION_TIMESTEP_MINS)

            # Simulation parameters
            solarVoltage = simDay.parameters['PVArray'].getVoltage() 
            totalArea = simDay.parameters['Site'].getArrayNum() * simDay.parameters['PVArray'].getArea()
            
            panelEff = simDay.parameters['PVPanel'].getEfficiency()
            panelDegRate = simDay.parameters['PVPanel'].getDegradationRate()

            DCcable = simDay.parameters['DCCable']
            # DCcableMaterial = simDay.parameters['DCCable'].getMaterial()
            # DCdiameter = simDay.parameters['DCCable'].getDiameter() 
            # DCcableLength = simDay.parameters['DCCable'].getLength()
            
            InvEff = simDay.parameters['Inverter'].getEfficiency()
            InvPowerFactor = simDay.parameters['Inverter'].getPowerFactor()
            InvOutVolt = simDay.parameters['Inverter'].getVoltage()
            
            TxEff = simDay.parameters['Transformer'].getEfficiency()
            TxOutVolt = simDay.parameters['Transformer'].getVoltage()

            AC1Cable = simDay.parameters['AC1Cable']
            AC1StrandNum = simDay.parameters['AC1Cable'].getStrandNum()
            # AC1Diameter = simDay.parameters['AC1Cable'].getDiameter()
            # AC1Length = simDay.parameters['AC1Cable'].getLength()
            
            AC2Cable = simDay.parameters['AC2Cable']
            # AC2StrandDiameter = simDay.parameters['AC2Cable'].getDiameter()
            # AC2Length = simDay.parameters['AC2Cable'].getLength()
            AC2StrandNum = simDay.parameters['AC2Cable'].getStrandNum()
            
            lat = simDay.parameters['Site'].getLatitude()
            lng = simDay.parameters['Site'].getLongitude()

            temperature =  simDay.parameters['Site'].getTemperature(month)


            # Number of days into the simulation this day occurs
            currentSimDay = (simDay.parameters['start'] - simDay.date).days

            # Running totals for the total output energy effciencies at each timestep
            energyOutput = 0
            totalEffciency = 0
            elecEff = 0
            sunnyTime = 0
            powerRunVal = 0

            # Simulate the irradiance over a day in half hour increments
            for i in range(STEPS_PER_DAY):

                # Create a datetime to represent the time of day on the given date
                minutesIntoDay = i * SIMULATION_TIMESTEP_MINS
                d = datetime.datetime(year, month, day) + datetime.timedelta(minutes=minutesIntoDay)

                # Get the sun altitude and irrandiance for the day using Pysolar
                altitude = Pysolar.GetAltitude(lat, lng, d)
                irradiance = Pysolar.radiation.GetRadiationDirect(d, altitude)

                # Calculates the solar power in W for a whole day
                solarOutput = irradiance * totalArea * panelEff  * (1 - panelDegRate / (100*365) * currentSimDay)
        
                # DC cable calcs
                DCresistance = calcCableResistance(DCcable, temperature)
                DCcurrent = solarOutput / solarVoltage # TODO find this constant solarVoltage         # ----------------- DC_CURRENT
                DCloss = 2 * DCcurrent**2 * DCresistance
                DCoutput = solarOutput - DCloss
            
                # Inverter calcs
                invOutput = DCoutput * InvEff

                # 3 Phase AC Cables to Tx calcs
                AC1StrandResistance = calcCableResistance(AC1Cable, temperature)
                AC1TotalResistance = AC1StrandResistance / AC1StrandNum
                IAC1 = invOutput / (math.sqrt(3) * InvPowerFactor*InvOutVolt)                       # ------------------ AC_CURRENT_1
                AC1loss = 3 * IAC1**2 * AC1TotalResistance
                AC1Output = invOutput - AC1loss
                
                # Transformer calcs
                TxOut = AC1Output * TxEff                

                # 3 Phase tranmission lines to GXP calcs
                strandResistance = calcCableResistance(AC2Cable, temperature)
                totalResistance = strandResistance / AC2StrandNum
                IAC2 = TxOut / (math.sqrt(3) * InvPowerFactor * TxOutVolt)                         # --------------------- AC_CURRENT_2
                AC2loss = 3 * IAC2**2 * totalResistance
                AC2Output = TxOut - AC2loss


                
                # Final outputs
                if irradiance > 0:
                    sunnyTime += 1
                    totalEffciency += (AC2Output / (irradiance * totalArea)) * 100
                    elecEff += (AC2Output / solarOutput) * 100
                    energyOutput += AC2Output * (float(SIMULATION_TIMESTEP_MINS) / 60) # Daily output in Wh
                    powerRunVal += AC2Output


            # Average the effciencies over the day
            sunnyTime = float(sunnyTime)
            totalEffciency /= sunnyTime
            elecEff /= sunnyTime
            powerRunVal /= sunnyTime
            
            # Save the output data to the SimulationDay object
            simDay.averagePower = powerRunVal
            simDay.electricalEffciency = elecEff
            simDay.totalEffciency = totalEffciency
            simDay.electricalEnergy = energyOutput

            # TODO: Calculate peak currents for the day and output from the thread.
            simDay.peakCurrent_DC = DCcurrent
            simDay.peakCurrent_AC1 = IAC1
            simDay.peakCurrent_AC2 = IAC2

            # Push the completed simulation day to the output queue and tick it off the input queue
            self.outputQueue.put(simDay)
            self.inputQueue.task_done()

class SimulationDay(object):
    ''' Contains a date object with a day to simulate, as well as the output data from the
    simulation'''
    def __init__(self, date, parameters):
        
        # Date to simulate and the parameters of the simulation
        self.date = date
        self.parameters = parameters
    
        # Outputs are stored here
        self.peakCurrent_DC = 0
        self.peakCurrent_AC1 = 0
        self.peakCurrent_AC2 = 0
        self.averagePower = 0
        self.electricalEnergy = 0
        self.electricalEffciency = 0
        self.totalEffciency = 0

    def setElectricalEnergy(self, electricalEnergy):
        ''' Sets the electrical energy from the simulation '''
        self.electricalEnergy = electricalEnergy

    def getElectricalEnergy(self):
        ''' Gets the electrical energy from the simulation '''
        return self.electricalEnergy

    def setElectricalEffciency(self, electricalEffciency):
        ''' Sets the average electrical effciency from the day simulated, that is the 
        effciency between the output of the solar panels and the grid connection point '''
        self.electricalEffciency = electricalEffciency

    def getElectricalEffciency(self):
        ''' Gets the average electrical effciency from the day simulated, that is the 
        effciency between the output of the solar panels and the grid connection point '''
        return self.electricalEffciency

    def setTotalEffciency(self, totalEffciency):
        ''' Sets the average total effciency from the day simulated, that is the 
        effciency between the solar energy in and the energy out at the grid connection point'''
        self.totalEffciency = totalEffciency

    def getTotalEffciency(self):
        ''' Gets the average total effciency from the day simulated, that is the 
        effciency between the solar energy in and the energy out at the grid connection point'''
        return self.totalEffciency

class Simulation(object):
    '''Object to contain the simulation parameters'''
    def __init__(self, start, finish, PVPanel, PVModule, PVArray, DCCable, 
                 Inverter, AC1Cable, Transformer, AC2Cable, CircuitBreaker, Site, Financial,
                 numThreads=5, simulationTimestepMins=30):
        '''Initilise the simulation'''
        self.start = start
        self.finish = finish
        self.numDays = (finish - start).days
        self.days = [self.start + datetime.timedelta(days=x) for x in range(0,self.numDays)]
        self.numThreads = numThreads
        self.simulationTimestepMins = simulationTimestepMins

        # Simulation parameters
        self.parameters = {
            'start': start,
            'finish': finish,
            'PVPanel' : PVPanel,
            'PVModule': PVModule, 
            'PVArray' : PVArray,
            'DCCable' : DCCable, 
            'Inverter': Inverter,
            'AC1Cable': AC1Cable, 
            'Transformer': Transformer, 
            'AC2Cable': AC2Cable, 
            'CircuitBreaker': CircuitBreaker, 
            'Site': Site,
            'Financial' : Financial
        }

        # Simulation results - will be replaced by dictionary with array results when the 
        # simulations have been run
        self.powerResults = {}
        self.financialResults = {}
        
        # Queues to store the input and output to the simulation
        self.inputQueue = Queue.Queue()
        self.outputQueue = Queue.Queue()

        print "Initialising %i day simulation" % self.numDays

        print "Start date: ", self.start
        print "Finish date: ", self.finish

        # Queue up the list of days to simulate
        

        for day in self.days:
            simulationDay = SimulationDay(day, self.parameters)
            self.inputQueue.put(simulationDay)

        print "Added %i simulations to the work queue" % self.inputQueue.qsize()

    def getStartDate(self):
        return self.start

    def setStartDate(self, date):
        self.start = date

    def getFinishDate(self):
        return self.finish

    def setFinishDate(self, date):
        self.finish = date

    def __runFinancial(self):
        '''Runs the finicial simulation, requires the results from power flow simulation'''

        # Sum the costs of all the assets 
        initalCosts = self.parameters['PVArray'].getCost()
        
        DCCableCost = (2 * self.parameters['DCCable'].getCost())
        initalCosts += DCCableCost # initalCosts + (2 * self.parameters['DCCable'].getCost()) # Worth of DC cables

        initalCosts += self.parameters['Inverter'].getCost() * self.parameters['Site'].getInverterNum() # Worth of the inverters
        initalCosts += 3 * self.parameters['AC1Cable'].getCost()  # Worth of AC1 cables
        initalCosts += self.parameters['Transformer'].getCost() * self.parameters['Site'].getTransformerNum() # Worth of the transfomers
        initalCosts += 3 * self.parameters['AC2Cable'].getCost()  # Worth of the GEP transmission line

        # Add the inital asset costs to the loan
        self.parameters['Financial'].addToLoan(initalCosts)

        # Get the relevant results from the power simulation
        electricalEnergy = self.powerResults['electricalEnergy']

        # Empty arrays for the results of the financial simulation
        netAssetValue = []
        loanValue = []
        accumulativeRevenue = []

        # Variables to accumlate stuff
        revenueAccumulator = 0
        expensesAccumulator = 0

        # Get the initial value of the loan
        initialExpenses = self.parameters['Financial'].getCurrentLoanValue()

        # Simulate the financial life of the project
        for i in range(self.numDays):

            # Calculate the net value of all the assets, factoring in depreciation
            dailyCapitalWorth = self.parameters['Site'].getDepreciatedValue(i) # Worth of the land
            dailyCapitalWorth += self.parameters['PVArray'].getDepreciatedValue(i) # made the assumption only one input required (works out total panel worth)
            dailyCapitalWorth += 2 * self.parameters['DCCable'].getDepreciatedValue(i) # Worth of DC cables
            dailyCapitalWorth += self.parameters['Inverter'].getDepreciatedValue(i) * self.parameters['Site'].getInverterNum() # Worth of the inverters
            dailyCapitalWorth += 3 * self.parameters['AC1Cable'].getDepreciatedValue(i)  # Worth of AC1 cables
            dailyCapitalWorth += self.parameters['Transformer'].getDepreciatedValue(i) * self.parameters['Site'].getTransformerNum() # Worth of the transfomers
            dailyCapitalWorth += 3 * self.parameters['AC2Cable'].getDepreciatedValue(i)  # Worth of the GEP transmission line
            
            # Save the current net asset value
            netAssetValue.append(dailyCapitalWorth)
            
            # Calculate the daily expenses
            dailyExpenses = self.parameters['Financial'].getDailyMaintenance()
            # expensesAccumulator += dailyExpenses
            # accumulativeExpenses.append(initialExpenses + expensesAccumulator)
            
            # Calculate the value of the power sold for this day
            dailyRevenue = (electricalEnergy[i] / 1000.0) * self.parameters['Financial'].getPowerPrice()  # Convert to watt hours
            revenueAccumulator += dailyRevenue
            accumulativeRevenue.append(revenueAccumulator)

            # Add the daily expenses to the loan, make a payment with the revenue and accumulate some interest
            self.parameters['Financial'].addToLoan(dailyExpenses)
            self.parameters['Financial'].makeLoanPayment(dailyRevenue)
            self.parameters['Financial'].accumlateDailyInterest()

            # Save the current loan value
            loanValue.append(self.parameters['Financial'].getCurrentLoanValue())

        # Save the simulation results
        self.financialResults = {
            'days' : self.days,
            'netAssetValue' : netAssetValue,
            'loanValue' : loanValue,
            'accumulativeRevenue' : accumulativeRevenue,
        }


    def __runPower(self):
        ''' Runs the power flow simulation'''
        numberOfSimulationDays = self.inputQueue.qsize()

        # Spawn the threads
        for i in range(self.numThreads):
            simulationThread = thread_SimulateDay(self.inputQueue, self.outputQueue, self.simulationTimestepMins)
            simulationThread.setDaemon(True)
            simulationThread.start()
        
        # Create a progress bar
        widgets = ['Running Simulation: ', progressbar.Percentage(), ' ', 
                   progressbar.Bar(), ' ', progressbar.ETA()]
        bar = progressbar.ProgressBar(maxval=numberOfSimulationDays, widgets=widgets)
        bar.start()

        # While the amount of output objects is less than the amount of input objects, update the progress bar
        completedSimulations = 0
        while(completedSimulations < numberOfSimulationDays):
            # Stops the console from being updated unecesseraly
            sleep(0.25)
            completedSimulations = (numberOfSimulationDays - self.inputQueue.qsize())
            bar.update(completedSimulations)

        # Finish up the progress bar
        bar.finish()

        print "Finished printing bar"

        # Join threads
        self.inputQueue.join()

        print "Finished joining threads"

        # Dequeue the results
        resultDays = []
        while not self.outputQueue.empty():
            resultDays.append(self.outputQueue.get())
            self.outputQueue.task_done()

        print "Finished Dequeueing results"

        # Sort the resultant simulation dates into order
        resultDays.sort(key=operator.attrgetter('date'))

        print "Sorted results"

        days = []
        electricalEnergy = []
        totalEffciency = []
        electricalEffciency = []
        averagePower = []

        for day in resultDays:
            days.append(day.date)
            electricalEnergy.append(day.electricalEnergy / 1000) # Converts energy to kWh
            electricalEffciency.append(day.electricalEffciency)
            totalEffciency.append(day.totalEffciency)
            averagePower.append(day.averagePower / 1000) # Converts power to kW

        print "Split data"

        self.powerResults = {
            'days' : self.days,
            'electricalEnergy' : electricalEnergy,
            'electricalEffciency' : electricalEffciency,
            'totalEffciency' : totalEffciency,
            'averagePower' : averagePower
        }


    def run(self):
        self.__runPower()
        self.__runFinancial()

        plt.figure(1)
        plt.subplot(311)
        plt.plot(self.days, self.powerResults['averagePower'])
        plt.title('Average output power being supplied to the Grid')
        plt.ylabel('Power (kW)')

        plt.subplot(312)
        plt.plot(self.days, self.powerResults['electricalEffciency'], 'g')
        plt.title('Electrical efficiency of the PV farm at GEP')
        plt.ylabel('Efficiency (%)')

        plt.subplot(313)
        plt.plot(self.days, self.powerResults['totalEffciency'], 'r')
        plt.title('Total efficiency of the PV farm')
        plt.ylabel('Efficiency (%)')
        
        plt.figure(2)
        plt.subplot(311)
        plt.plot(self.days, self.financialResults['netAssetValue'], 'r')
        
        plt.subplot(312)
        plt.plot(self.days, self.financialResults['accumulativeExpenses'], 'g')

        plt.subplot(313)
        plt.plot(self.days, self.financialResults['accumulativeRevenue'], 'b')

        plt.show()

        # return (powerData, financialData)

# --------------------------------------------------------------------------------------------------
# Redundant code
# --------------------------------------------------------------------------------------------------

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

#-------------Financial-----------------------------------------------#
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