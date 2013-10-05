# --------------------------------------------------------------------------------------------------
# SolarAssets : Solar farm Assets
# --------------------------------------------------------------------------------------------------
# Author: Darren O'Neill
# Author: Jarrad Raumati 
# Author: Ashok Fernandez
# Date: 20/09/2013
#
# This module contains the asset classes for use with SolarSimulation
# --------------------------------------------------------------------------------------------------

import PyExchangeRates

# Create a currency exchange
CURRENCY_EXCHANGE = PyExchangeRates.Exchange('843ce8fdc22c47779fb3040c2ba9a586')

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
        super(PVModule, self).__init__(panelType.getCost().getAmount() * panelNum, panelType.getCurrency(),
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
        super(PVArray, self).__init__(moduleType.getCost().getAmount() * moduleNum, moduleType.getCurrency(),
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