'''@package Simulation.py

Contains the core model and simulation code for the calculator. The thread class is where all the power simulations are done, and the
runFinancial method contains all the financial simulation code. Takes a set of Asset objects from Asset.py which specifies the parameters
of the simulation, as well as a start and finish date.

Author: Ashok Fernandez
Author: Darren O'Neill
Author: Jarrad Raumati 
Date: 20/09/2013
'''

# Import system modules
import operator
import Queue
import threading
import math
import datetime

# Import PySolar for irradiance calculations
import Pysolar


# --------------------------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------------------------------------------------------------

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
# SIMULATION THREAD
# --------------------------------------------------------------------------------------------------

class thread_SimulateDay(threading.Thread):
    '''Thread to simulate the power flow over a given day.

    Takes an input in the form of a queue of SimulationDay objects, gets a day from the queue, runs the simulation 
    for that day and stores the result inside the SimulationDay object before pushing it to the output queue. Terminates
    when there are not more days left in the input queue'''

    def __init__(self, inputQueue, outputQueue, timestep_mins):
        ''' Intantiates a simulation thread'''
        threading.Thread.__init__(self)
        self.timestep_mins = timestep_mins
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
    
    def run(self):
        '''' Method thats invoked to run the thread.

        The thread will keep running until the input queue is empty, at which point it will terminate.
        All the key simulation code is in here and is annotated to show what it does'''
        
        # Keep running the thread indefinitly until it terminates itself when it runs out of stuff to do
        while True:

            # Check if there are any more days to simulate, if not then terminate
            if self.inputQueue.empty():
                return

            # Day that is being simulated
            simDay = self.inputQueue.get()
            year = simDay.date.year
            month = simDay.date.month
            day = simDay.date.day

            # Time steps
            SIMULATION_TIMESTEP_MINS = float(self.timestep_mins)
            MINS_PER_DAY = 1440.00 # Make it a float so it divides nicely
            STEPS_PER_DAY = int(MINS_PER_DAY / SIMULATION_TIMESTEP_MINS)
            

            # --------------------------------------------------------------------------------------------------
            # SIMULATION PARAMETERS
            # --------------------------------------------------------------------------------------------------
            
            totalArea = simDay.parameters['Site'].getArrayNum() * simDay.parameters['PVArray'].getArea()
            panelNum = simDay.parameters['PVModule'].getPanelNum() * simDay.parameters['PVArray'].getModuleNum() * simDay.parameters['Site'].getArrayNum()
            
            solarVoltage = simDay.parameters['PVArray'].getVoltage() 
            panelDegRate = simDay.parameters['PVPanel'].getDegradationRate()
            panelAngle = simDay.parameters['PVArray'].getAngle()
            panelRating = simDay.parameters['PVPanel'].getRating() 
            
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


            # --------------------------------------------------------------------------------------------------
            # OUTPUT VARIABLES
            # --------------------------------------------------------------------------------------------------

            # Running totals for the total output energy effciencies at each timestep
            energyOutput = 0
            totalEffciency = 0
            elecEff = 0
            sunnyTimeSteps = 0
            powerRunVal = 0

            # Arrays to contain the current values so we can obtain the maximum
            DCCurrents = []
            AC1Currents = []
            AC2Currents = []



            # --------------------------------------------------------------------------------------------------
            # TILTED IRRADIANCE CALCULATION
            # --------------------------------------------------------------------------------------------------

            # Declination angle of the sun
            argRadians = math.radians((360 * (284 + currentDayOfYear)/ 365.0))
            delta = 23.45 * math.sin(argRadians)
            a = 90 - lat + delta
                
            # Calculates the irradiance on the panel for a day
            a_Radians = math.radians(a)
            panelAngle_rad = math.radians(panelAngle)

            # Check that latitude of the site and assign a panel azimuth accordingly
            if lat > 0:
                panelAzimuth = math.radians(180)
            elif lat <= 0:
                panelAzimuth = math.radians(0)

            # Calculate the amount of sunlight hours in the day
            # http://mathforum.org/library/drmath/view/56478.html
            P = math.asin(0.39795 * math.cos(0.2163108 + 2 * math.atan(0.9671396 * math.tan(0.00860 * (currentDayOfYear-186)))))
            numerator = math.sin(0.8333 * math.pi/180) + math.sin(lat * math.pi/180) * math.sin(P)
            denominator =  math.cos(lat * math.pi /180) * math.cos(P) 
            sunlightHours = 24 - (24/math.pi) * math.acos( numerator / denominator )

            


            # --------------------------------------------------------------------------------------------------
            # SOLAR MODEL
            # --------------------------------------------------------------------------------------------------

            # Simulate the irradiance over a day in the increment described by SIMULATION_TIMESTEP_MINS
            for i in range(STEPS_PER_DAY):

                # Create a datetime to represent the time of day on the given date
                minutesIntoDay = i * SIMULATION_TIMESTEP_MINS
                d = datetime.datetime(year, month, day) + datetime.timedelta(minutes=minutesIntoDay)

                # Get the sun altitude and irradiance for the day using Pysolar
                azimuth_deg = Pysolar.GetAzimuth(lat, lng, d)
                azimuth_rad = math.radians(azimuth_deg)
                altitude = Pysolar.GetAltitude(lat, lng, d)
                irradiance = Pysolar.radiation.GetRadiationDirect(d, altitude)

                # Factor in the panel angle
                tiltedFactor = math.cos(a_Radians) * math.sin(panelAngle_rad) * math.cos(panelAzimuth - azimuth_rad) + math.sin(a_Radians) * math.cos(panelAngle_rad)

                # Check if it's nighttime, not point simulating solar at night!
                if irradiance > 0:

                    # Calculate the amount of irradiance on the panel
                    panelIrradiance = irradiance * tiltedFactor
                    
                    # Calculates the solar power in W for a whole day
                    solarOutput = panelIrradiance * panelRating * panelNum / 1000 * (1 - ((panelDegRate / 100.0) / 365.0) * currentSimDay)
            
                    # DC cable calcs
                    DCresistance = calcCableResistance(DCcable, temperature)
                    DCcurrent = solarOutput / solarVoltage       
                    DCloss = 2 * DCcurrent** 2 * DCresistance
                    DCoutput = solarOutput - DCloss
                
                    # Inverter calcs
                    invOutput = DCoutput * InvEff

                    # 3 Phase AC Cables to Tx calcs
                    AC1StrandResistance = calcCableResistance(AC1Cable, temperature)
                    AC1TotalResistance = AC1StrandResistance / AC1StrandNum
                    IAC1 = invOutput / (math.sqrt(3) * InvPowerFactor*InvOutVolt)                       
                    AC1loss = 3 * IAC1**2 * AC1TotalResistance
                    AC1Output = invOutput - AC1loss
                    
                    # Transformer calcs
                    TxOut = AC1Output * TxEff                

                    # 3 Phase tranmission lines to GXP calcs
                    strandResistance = calcCableResistance(AC2Cable, temperature)
                    totalResistance = strandResistance / AC2StrandNum
                    IAC2 = TxOut / (math.sqrt(3) * InvPowerFactor * TxOutVolt)                         
                    AC2loss = 3 * IAC2**2 * totalResistance
                    AC2Output = TxOut - AC2loss
          
                    # Final outputs
                    sunnyTimeSteps += 1
                    totalEffciency += (AC2Output / (panelIrradiance * totalArea)) * 100
                    elecEff += (AC2Output / solarOutput) * 100
                    energyOutput += AC2Output * (float(SIMULATION_TIMESTEP_MINS) / 60) # Daily output in Wh
                    powerRunVal += AC2Output

                    # Save the DC, AC1, and AC2 currents
                    DCCurrents.append(DCcurrent)
                    AC1Currents.append(IAC1)
                    AC2Currents.append(IAC2)

            
            # --------------------------------------------------------------------------------------------------
            # STORE RESULTS
            # --------------------------------------------------------------------------------------------------

            # Average the effciencies over the day
            sunnyTime = sunlightHours * float(60 / SIMULATION_TIMESTEP_MINS)
            totalEffciency /= sunnyTimeSteps
            elecEff /= sunnyTime
            powerRunVal /= sunnyTime

            # Find the maximum currents
            maxDC = max(DCCurrents)
            maxAC1 = max(AC1Currents)
            maxAC2 = max(AC2Currents)

            # Save the output data to the SimulationDay object
            simDay.averagePower = powerRunVal
            simDay.electricalEffciency = elecEff
            simDay.totalEffciency = totalEffciency
            simDay.electricalEnergy = energyOutput
            simDay.sunnyTime = a
            simDay.peakCurrent_DC = maxDC
            simDay.peakCurrent_AC1 = maxAC1
            simDay.peakCurrent_AC2 = maxAC2

            # Push the completed simulation day to the output queue and tick it off the input queue
            self.outputQueue.put(simDay)
            self.inputQueue.task_done()




# --------------------------------------------------------------------------------------------------
# SIMULATION OBJECTS
# --------------------------------------------------------------------------------------------------

class SimulationDay(object):
    ''' Contains a date object with a day to simulate, as well as the output data from the
    simulation.

    This object represents a single day to simulate. The simulation threads treat each day as
    independant so they can be run in parallel. This contains all the input parameters and 
    a specific date to simulate. The outputs for the day are stored in there so they are able 
    to be unpacked and passed back to the controller.'''

    def __init__(self, date, parameters):
        ''' Initialises a simulation day at the given date using the given parameter dictionary'''    
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
                 numThreads=30, simulationTimestepMins=30):
        '''Initilise a simulation instance.

        This object is an instance of a simulation. It requires a set of input objects which provide the simulation
        parameters. The parameters are passed in the form asset objects which represent different components of the 
        solar farm, plus a start and finish date. The timestep for calculations can be adjusted, as can the amount of 
        execution threads (parallel processing elements). A larger timestep give a better resolution but will take 
        longer to calculate. A larger amount of threads will calculate the result faster but will place more strain on 
        the PC running the computation'''
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

        # Queue up the list of days to simulate
        for day in self.days:
            simulationDay = SimulationDay(day, self.parameters)
            self.inputQueue.put(simulationDay)


    def getStartDate(self):
        ''' Returns the start date of the simulation '''
        return self.start

    def setStartDate(self, date):
        ''' Sets the start date of the simulation '''
        self.start = date

    def getFinishDate(self):
        ''' Returns the finish date of the simulation '''
        return self.finish

    def setFinishDate(self, date):
        ''' Sets the finish date of the simulation '''
        self.finish = date


    def runPower(self):
        ''' Runs the power flow simulation.

        This gets the simulation days that were created and queued up when the simulation was initialised and
        starts a pool of simulation threads to start processing the queue. This method is non blocking - it merely
        invokes the simulation which runs on seperate threads to the program'''
        numberOfSimulationDays = self.inputQueue.qsize()

        # Spawn the threads
        for i in range(self.numThreads):
            simulationThread = thread_SimulateDay(self.inputQueue, self.outputQueue, self.simulationTimestepMins)
            simulationThread.setDaemon(True)
            simulationThread.start()

    def getPowerProgress(self):
        ''' Returns percentage of days simulated in the power simulation as a number between 0 and 100. 

        This is used to update the progress bar in the GUI'''
        # Get the total amount of day to be simulated and the amount of days left to simulate
        itemsLeft = self.inputQueue.qsize()
        totalItems = self.numDays

        # Calculate a percentage between 0-100 of how far through the simulation we are
        progress = ((float(totalItems - itemsLeft) / totalItems) * 100) + 1
        progress = round(progress)

        return progress


    def getPowerResults(self):
        ''' Processes and gets the power results. 

        Blocks until the power simulation is finished. When all the jobs are done this will retreieve all the results
        from the output queue, sort them into order by date and unpack the data from each day into arrays which are saved
        in a dictionary and returned to the caller.'''
        
        # Join threads from power simulation - this blocks until the simulation is complete
        self.inputQueue.join()

        # Dequeue the results
        resultDays = []
        while not self.outputQueue.empty():
            resultDays.append(self.outputQueue.get())
            self.outputQueue.task_done()

        # Sort the resultant simulation dates into order
        resultDays.sort(key=operator.attrgetter('date'))

        # Create arrays to store the output data
        days = []
        electricalEnergy = []
        totalEffciency = []
        electricalEffciency = []
        averagePower = []
        sunnyTime = []
        peakDC = []
        peakAC1 = []
        peakAC2 = []

        # Unpack the results for each day and store them in arrays
        for day in resultDays:
            days.append(day.date)
            electricalEnergy.append(day.electricalEnergy / 1000) # Converts energy to kWh
            electricalEffciency.append(day.electricalEffciency)
            totalEffciency.append(day.totalEffciency)
            averagePower.append(day.averagePower / 1000) # Converts power to kW
            sunnyTime.append(day.sunnyTime)
            peakDC.append(day.peakCurrent_DC)
            peakAC1.append(day.peakCurrent_AC1)
            peakAC2.append(day.peakCurrent_AC2)

        # Find the maximum currents
        peakDC = max(peakDC)
        peakAC1 = max(peakAC1)
        peakAC2 = max(peakAC2)

        # Save the results within the simulation object
        self.powerResults = {
            'days' : self.days,
            'electricalEnergy' : electricalEnergy,
            'electricalEffciency' : electricalEffciency,
            'totalEffciency' : totalEffciency,
            'averagePower' : averagePower,
            'sunnyTime' : sunnyTime,
            'peakDC' : peakDC,
            'peakAC1' : peakAC1,
            'peakAC2': peakAC2          
        }

        return self.powerResults




    def runFinancial(self):
        '''Runs the finicial simulation.

        This requires the results from power flow simulation, hence the power flow simulation must be complete BEFORE this
        method is called. Blocks until complete. Once the simulation is done it will return a dictionary of arrays with the 
        simulation results.'''

        # Sum the costs of all the assets 
        initalCosts = self.parameters['PVArray'].getCost() * self.parameters['Site'].getArrayNum()
        initalCosts += 2 * self.parameters['DCCable'].getCost() # Worth of DC cables
        initalCosts += self.parameters['Inverter'].getCost() * self.parameters['Site'].getInverterNum() # Worth of the inverters
        initalCosts += 3 * self.parameters['AC1Cable'].getCost() # Worth of AC1 cables
        initalCosts += self.parameters['Transformer'].getCost() * self.parameters['Site'].getTransformerNum() # Worth of the transfomers
        initalCosts += self.parameters['AC2Cable'].getCost() # Worth of the GEP transmission line
        initalCosts += self.parameters['Site'].getCost()

        # Add the inital asset costs to the loan
        self.parameters['Financial'].addToLoan(initalCosts)

        # Get the relevant results from the power simulation
        electricalEnergy = self.powerResults['electricalEnergy']

        # Empty arrays for the results of the financial simulation
        netAssetValue = []
        loanValue = []
        accumulativeRevenue = []

        # Variable to accumlate revenue
        revenueAccumulator = self.parameters['Financial'].getCurrencyExchange().withdraw(0, 'USD')

        # Simulate the financial life of the project
        for i in range(self.numDays):

            # Calculate the net value of all the assets, factoring in depreciation
            dailyCapitalWorth = self.parameters['Site'].getDepreciatedValue(i) # Worth of the land
            dailyCapitalWorth = self.parameters['PVArray'].getDepreciatedValue(i) * self.parameters['Site'].getArrayNum() # made the assumption only one input required (works out total panel worth)
            dailyCapitalWorth += 2 * self.parameters['DCCable'].getDepreciatedValue(i) # Worth of DC cables
            dailyCapitalWorth += self.parameters['Inverter'].getDepreciatedValue(i) * self.parameters['Site'].getInverterNum() # Worth of the inverters
            dailyCapitalWorth += 3 * self.parameters['AC1Cable'].getDepreciatedValue(i) # Worth of AC1 cables
            dailyCapitalWorth += self.parameters['Transformer'].getDepreciatedValue(i) * self.parameters['Site'].getTransformerNum() # Worth of the transfomers
            dailyCapitalWorth += self.parameters['AC2Cable'].getDepreciatedValue(i) # Worth of the AC2 transmission line
            
            # Save the current net asset value
            netAssetValue.append(dailyCapitalWorth)
            
            # Calculate the daily expenses
            dailyExpenses = self.parameters['Financial'].getDailyMaintenance()
            
            # Calculate the value of the power sold for this day
            dailyRevenue = (electricalEnergy[i]) * self.parameters['Financial'].getPowerPrice()  # Convert to watt hours

            # Acculate todays revenue onto the total revenue
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

        # Save the financial simulation results
        self.financialResults = {
            'days' : self.days,
            'netAssetValue' : netAssetValue,
            'loanValue' : loanValue,
            'accumulativeRevenue' : accumulativeRevenue,
            'baseCurrency' : self.parameters['Financial'].getBaseCurrency(),
            'arrayCost' : self.parameters['PVArray'].getCost().getAmount() * self.parameters['Site'].getArrayNum(),
            'DCCableCost' : (2 * self.parameters['DCCable'].getCost().getAmount()),
            'inverterCost' : self.parameters['Inverter'].getCost().getAmount() * self.parameters['Site'].getInverterNum(),
            'AC1CableCost' : 3 * self.parameters['AC1Cable'].getCost().getAmount(),
            'transformerCost' : self.parameters['Transformer'].getCost().getAmount() * self.parameters['Site'].getTransformerNum(),
            'AC2CableCost' : self.parameters['AC2Cable'].getCost().getAmount(),
            'siteCost' : self.parameters['Site'].getCost().getAmount()
        }



    def getFinancialResults(self):
        ''' Returns the financial results'''
        return self.financialResults
