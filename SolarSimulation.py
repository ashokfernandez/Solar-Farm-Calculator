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
from SolarAssets import *

# For the progress bar in the console when the scraping operation is happening
from time import sleep
import progressbar # https://pypi.python.org/pypi/progressbar/

# Create a currency exchange
# CURRENCY_EXCHANGE = PyExchangeRates.Exchange('843ce8fdc22c47779fb3040c2ba9a586')


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

# def getDailyEnergy(angle, date, latitude, longitude):
#     '''Returns the total energy of of a day'''

#     timeStepMins = 30.0 # time step in minutes
#     minsPerDay = 1440.00  # Minutes in a day (float for dividing)

#     timeStep = minsPerDay / float(timeStepMins)

#     # Num days into the year
#     yearDay = (datetime.datetime(2013, 1, 1) - date).days + 1

#      # arbitary angle that is used for calculating the irradiance
#     argRadians = math.radians(360 / 365 * (284 + yearDay))
#     # same as above for the next 3 lines
#     a = 90 - latitude + 23.45 * math.sin(argRadians)
#     argRadians_1 = math.radians(a + angle)
#     argRadians_2 = math.radians(a)

#     # Irrdiance scale factor
#     scaleFactor = math.sin(argRadians_1) / math.sin(argRadians_2)

#     # Variable store the total energy in the year
#     dayEnergy = 0

#     for i in range(int(timeStep)):

#         minutesIntoDay = i * timeStepMins
#         d = date + datetime.timedelta(minutes=minutesIntoDay)

#         altitude = Pysolar.GetAltitude(latitude, longitude, d)
#         irradiance = Pysolar.radiation.GetRadiationDirect(d, altitude) 

#         dayEnergy += irradiance * scaleFactor * (timeStepMins / 60)

#     return dayEnergy


# def calcOptimumAngle(siteLat, siteLon):
#     ''' Calculates the optimum angle of the PV panels based on the latitude of the site. '''

#     # [0:0.1:90] specifices angle between 0 and 90 degrees
#     testAngle = [x * 0.1 for x in range(0, 900)]

#     angleLength = len(testAngle) # length of test angle array
#     # arbitary start day (just need to simulate a year)

#     start = datetime.datetime(2013, 1, 1)

#     days = [start + datetime.timedelta(days=x) for x in range(0,365)]
    
    
#     yearlyEnergy = []

#     # iterates through each angle and calculates the mean irradiance for that year
#     for i in range(angleLength):
        

#         yearEnergy = 0

#         for j in range(365):

#             yearEnergy += getDailyEnergy(testAngle[i], days[i], siteLat, siteLon)
        
#         yearlyEnergy.append(yearlyEnergy)
    
#     # Takes the angle with the highest average yearly energy
#     ind = yearlyEnergy.index(max(yearlyEnergy))

#     #the optimum angle for solar panel
#     opAngle = testAngle[ind]

#     return opAngle

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
        return self.loan

    def amountInBaseCurrency(self, money):
        ''' Returns the value of a money object in the base currency of the loan'''
        return money.convert(self.baseCurrency).getAmount()

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
            SIMULATION_TIMESTEP_MINS = float(self.timestep_mins)
            MINS_PER_DAY = 1440.00 # Make it a float so it divides nicely
            STEPS_PER_DAY = int(MINS_PER_DAY / SIMULATION_TIMESTEP_MINS)
# --------------------------------------------------------------------------------------------------
#---------- Simulation parameters
# --------------------------------------------------------------------------------------------------
            totalArea = simDay.parameters['Site'].getArrayNum() * simDay.parameters['PVArray'].getArea()
            
            solarVoltage = simDay.parameters['PVArray'].getVoltage() 
            panelEff = simDay.parameters['PVPanel'].getEfficiency()
            panelDegRate = simDay.parameters['PVPanel'].getDegradationRate()
            panelAngle = simDay.parameters['PVArray'].getAngle() 
            
            DCcable = simDay.parameters['DCCable']
            
            InvEff = simDay.parameters['Inverter'].getEfficiency()
            InvPowerFactor = simDay.parameters['Inverter'].getPowerFactor()
            InvOutVolt = simDay.parameters['Inverter'].getVoltage()
            
            TxEff = simDay.parameters['Transformer'].getEfficiency()
            TxOutVolt = simDay.parameters['Transformer'].getVoltage()

            AC1Cable = simDay.parameters['AC1Cable']
            AC1StrandNum = simDay.parameters['AC1Cable'].getStrandNum()
            
            AC2Cable = simDay.parameters['AC2Cable']

            AC2StrandNum = simDay.parameters['AC2Cable'].getStrandNum()
            
            lat = simDay.parameters['Site'].getLatitude()
            lng = simDay.parameters['Site'].getLongitude()

            temperature =  simDay.parameters['Site'].getTemperature(month)


            # Number of days into the simulation this day occurs
            currentSimDay = (simDay.date - simDay.parameters['start']).days + 1
            currentDayOfYear = (simDay.date - datetime.date(year, 1, 1)).days + 1

            # f = open("day" + str(currentSimDay) + '.csv', 'w')

            # Running totals for the total output energy effciencies at each timestep
            energyOutput = 0
            totalEffciency = 0
            elecEff = 0
            sunnyTimeSteps = 0
            powerRunVal = 0

# --------------------------------------------------------------------------------------------------
#---------- Tilted irradiance calculation
# --------------------------------------------------------------------------------------------------

            #TODO: Fix this shit from making the power go negative
            # Declination angle of the sun
            argRadians = math.radians((360 * (284 + currentDayOfYear)/ 365.0))
            delta = 23.45 * math.sin(argRadians)
            a = 90 - lat + delta
                
            # Calculates the irradiance on the panel for a day
            # argRadians_1 = math.radians(a + panelAngle)
            argRadians_2 = math.radians(a)
            panelAngle_rad = math.radians(panelAngle)

            if lat > 0:
                panelAzimuth = math.radians(180)
            elif lat <= 0:
                panelAzimuth = math.radians(0)

            # Factor to multiple the irradiance with to consider the panel angle
            # tiltedFactor = math.sin(argRadians_1) / math.sin(argRadians_2)

            # Calculate the amount of sunlight hours in the day
            # http://mathforum.org/library/drmath/view/56478.html
            P = math.asin(0.39795 * math.cos(0.2163108 + 2 * math.atan(0.9671396 * math.tan(0.00860 * (currentDayOfYear-186)))))
            numerator = math.sin(0.8333 * math.pi/180) + math.sin(lat * math.pi/180) * math.sin(P)
            denominator =  math.cos(lat * math.pi /180) * math.cos(P) 
            sunlightHours = 24 - (24/math.pi) * math.acos( numerator / denominator )

# --------------------------------------------------------------------------------------------------
#---------- SOLAR MODEL
# --------------------------------------------------------------------------------------------------

            # Simulate the irradiance over a day in half hour increments
            for i in range(STEPS_PER_DAY):

                # Create a datetime to represent the time of day on the given date
                minutesIntoDay = i * SIMULATION_TIMESTEP_MINS
                d = datetime.datetime(year, month, day) + datetime.timedelta(minutes=minutesIntoDay)

                # Get the sun altitude and irradiance for the day using Pysolar
                azimuth_deg = Pysolar.GetAzimuth(lat, lng, d)
                azimuth_rad = math.radians(azimuth_deg)
                altitude = Pysolar.GetAltitude(lat, lng, d)
                irradiance = Pysolar.radiation.GetRadiationDirect(d, altitude)

                tiltedFactor = math.cos(argRadians_2) * math.sin(panelAngle_rad) * math.cos(panelAzimuth - azimuth_rad) + math.sin(argRadians_2) * math.cos(panelAngle_rad)

                if irradiance > 0:
                    # Calculate the amount of irradiance on the panel
                    panelIrradiance = irradiance * tiltedFactor
                    # Calculates the solar power in W for a whole day
                    solarOutput = panelIrradiance * totalArea * panelEff * (1 - ((panelDegRate / 100.0) / 365.0) * currentSimDay)
            
                    # DC cable calcs
                    DCresistance = calcCableResistance(DCcable, temperature)
                    DCcurrent = solarOutput / solarVoltage # TODO find this constant solarVoltage         # ----------------- DC_CURRENT
                    DCloss = 2 * DCcurrent** 2 * DCresistance
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
                    sunnyTimeSteps += 1
                    totalEffciency += (AC2Output / (panelIrradiance * totalArea)) * 100
                    elecEff += (AC2Output / solarOutput) * 100
                    energyOutput += AC2Output * (float(SIMULATION_TIMESTEP_MINS) / 60) # Daily output in Wh
                    powerRunVal += AC2Output

# --------------------------------------------------------------------------------------------------
#---------- RESULTS
# --------------------------------------------------------------------------------------------------

            # Average the effciencies over the day
            sunnyTime = sunlightHours * float(60 / SIMULATION_TIMESTEP_MINS)
            totalEffciency /= sunnyTimeSteps
            elecEff /= sunnyTime
            powerRunVal /= sunnyTime
            
            # Save the output data to the SimulationDay object
            simDay.averagePower = powerRunVal
            simDay.electricalEffciency = elecEff
            simDay.totalEffciency = totalEffciency
            simDay.electricalEnergy = energyOutput
            simDay.sunnyTime = a

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
        self.sunnyTime = 0

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


    def runPower(self):
        ''' Runs the power flow simulation'''
        numberOfSimulationDays = self.inputQueue.qsize()

        # Spawn the threads
        for i in range(self.numThreads):
            simulationThread = thread_SimulateDay(self.inputQueue, self.outputQueue, self.simulationTimestepMins)
            simulationThread.setDaemon(True)
            simulationThread.start()

    def getPowerProgress(self):
        ''' Returns percentage of days simulated in the power simulation as a number between 0 and 100 '''
        itemsLeft = self.inputQueue.qsize()
        totalItems = self.numDays

        progress = (float(itemsLeft) / totalItems) * 100 + 1
        progress = round(progress)

        return progress


    def getPowerResults(self):
        ''' Processes and gets the power results'''
        # Join threads
        self.inputQueue.join()

        # Dequeue the results
        resultDays = []
        while not self.outputQueue.empty():
            resultDays.append(self.outputQueue.get())
            self.outputQueue.task_done()

        # Sort the resultant simulation dates into order
        resultDays.sort(key=operator.attrgetter('date'))

        days = []
        electricalEnergy = []
        totalEffciency = []
        electricalEffciency = []
        averagePower = []
        sunnyTime = []

        for day in resultDays:
            days.append(day.date)
            electricalEnergy.append(day.electricalEnergy / 1000) # Converts energy to kWh
            electricalEffciency.append(day.electricalEffciency)
            totalEffciency.append(day.totalEffciency)
            averagePower.append(day.averagePower / 1000) # Converts power to kW
            sunnyTime.append(day.sunnyTime)

        self.powerResults = {
            'days' : self.days,
            'electricalEnergy' : electricalEnergy,
            'electricalEffciency' : electricalEffciency,
            'totalEffciency' : totalEffciency,
            'averagePower' : averagePower,
            'sunnyTime' : sunnyTime
        }

        return self.powerResults

    def runFinancial(self):
        '''Runs the finicial simulation, requires the results from power flow simulation. Blocks until complete'''

        # Sum the costs of all the assets 
        initalCosts = self.parameters['PVArray'].getCost()
        initalCosts += initalCosts + (2 * self.parameters['DCCable'].getCost()) # Worth of DC cables
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

        # Variables to accumlate financial stuff
        revenueAccumulator = CURRENCY_EXCHANGE.withdraw(0, 'USD')
        expensesAccumulator = CURRENCY_EXCHANGE.withdraw(0, 'USD')

        # Get the initial value of the loan
        # initialExpenses = self.parameters['Financial'].getCurrentLoanValue()


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

            if i == 0:
                self.parameters['Financial'].addToLoan(dailyCapitalWorth)
            
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



        # Convert all the results to float arrays in the base currency
        netAssetValue = [self.parameters['Financial'].amountInBaseCurrency(x) for x in netAssetValue]
        loanValue = [self.parameters['Financial'].amountInBaseCurrency(x) for x in loanValue]
        accumulativeRevenue = [self.parameters['Financial'].amountInBaseCurrency(x) for x in accumulativeRevenue]

        # Save the simulation results
        self.financialResults = {
            'days' : self.days,
            'netAssetValue' : netAssetValue,
            'loanValue' : loanValue,
            'accumulativeRevenue' : accumulativeRevenue,
        }

    def getFinancialResults(self):
        ''' Returns the financial results'''
        return self.financialResults


    # def run(self):
    #     ''' Runs the power simulation then the financial simulation and returns a dictionary with the
    #     results from each '''
    #     self.runPower()
    #     self.runFinancial()

        

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