# -------------------------------------------------------------------------------------------------------------------
# PyExchangeRates : An unoffcial interface to the Open Exchange Rates API
# -------------------------------------------------------------------------------------------------------------------
# 
# Author: Ashok Fernandez - https://github.com/ashokfernandez/
# Date  : 23 / 09 / 2013
# 
# Description: 
# Downloads the latest exchange rates from http://openexchangerates.org/ and saves them to a file. If the file can be
# found the module will load the rates from the file if the file is less than one day old. Otherwise the file is updated
# with the newest rates. There are money objects which can be manipulated with addition, substraction, multiplication
# and division - with the results always being in USD. Money values can be converted to other currencies. See the example
# below for more details
# 
# Usage example: 
# >>> import PyExchangeRates
# >>> exchange = PyExchangeRates.Exchange('YOUR API KEY HERE')
# >>> a = exchange.withdraw(1000, 'USD')
# >>> b = exchange.withdraw(1000, 'EUR')
# >>> print a + b
# 2352.363797 USD
#
# >>> print a - b
# -352.363797 USD
#
# >>> print a * b
# 1352363.796680 USD
#
# >>> print a * 2
# 2000.000000 USD
#
# >>> print a + b
# 2352.363797 USD
#
# >>> print b / 2
# 500.000000 USD
#
# >>> print a.convert('AUD')
# 1061.079000 AUD
# -------------------------------------------------------------------------------------------------------------------

import urllib2                    # For downloading the currency data
import json                       # Allows the data to be decoded
from datetime import datetime     # For timestamping
import time                       # For timestamping

import sys                        # Fixes Unicode encoding error
reload(sys)                       # ...
sys.setdefaultencoding("utf-8")   # ...

# --------------------------------------------------------------------------------------------------------------------
# CONSTANTS
# --------------------------------------------------------------------------------------------------------------------

UPDATE_THRESHOLD_DAYS = 1                           # Updates the currencies once a day
BASE_URL = 'http://openexchangerates.org/api/'      # Base API for the Open Exchange Rates API
GET_LATEST = 'latest.json'                          # Add this to the Base URL for the lastest rates
GET_NAMES = 'currencies.json'                       # Add this to the Base URL for the names of the currencies
UNITED_STATES_DOLLARS_KEY = 'USD'                   # Currency key for United States Dollars
DEBUG_MODE = False                                  # Set to False to turn off debugging messages

# --------------------------------------------------------------------------------------------------------------------
# MISC FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------

def internet_on():
    ''' Returns True if the internet is avaliable, otherwise returns false'''
    connectionAvaliable = False
    try:
        # Check if Google is online, use the direct IP to avoid DNS lookup delays
        response = urllib2.urlopen('http://74.125.228.100',timeout=5)
        connectionAvaliable = True
    except urllib2.URLError as err: 
        # Connection failed, either Google is down or more likely the internet connection is down
        pass
    
    return connectionAvaliable


def debug(message):
    ''' Prints debugging messages if debug mode is set to true'''
    if DEBUG_MODE:
        print message

# --------------------------------------------------------------------------------------------------------------------
# EXCEPTIONS
# --------------------------------------------------------------------------------------------------------------------
# 
class AccessDataFailure(Exception):
    ''' Exception for when there is no data on the currencies - either from file or from the internet   '''
    pass

class BadAppID(Exception):
    ''' Thrown when the app id for the open currency exchange is invalid'''
    pass

class InvalidCurrencyKey(Exception):
    ''' Thrown when a currency key is given that is not in the Exchange '''
    pass

# --------------------------------------------------------------------------------------------------------------------
# CLASSES
# --------------------------------------------------------------------------------------------------------------------

class SimpleObjectEncoder(json.JSONEncoder):
    ''' Allows simple objects which contain no methods to be encoded by returning them as a dictionary '''
    def default(self, obj):
        return obj.__dict__


class Currency(object):
    ''' Class to store information about a currency '''
    def __init__(self, key, baseKey, rate, name):
        ''' Initialise a currency object'''
        self.key = key           # Key to identify the currency (i.e UNITED_STATES_DOLLARS_KEY for United States Dollars)
        self.baseKey = baseKey   # Key of the base currency that this currency is measured against
        self.rate = rate         # Value of the currency in relation to the base
        self.name = name         # String which contains the name of the currency (i.e 'United States Dollars' for UNITED_STATES_DOLLARS_KEY)

    def __str__(self):
        return "%s (%s) - %f [base is %s]" % (self.name, self.key, self.rate, self.baseKey)

class Money(object):
    ''' Object to represent a certain amount of a currency withdrawn from an exchange '''
    def __init__(self, amount, currencyKey, exchange):
        self.amount = amount              # Amount
        self.currencyKey = currencyKey    # Currency key
        self.exchange = exchange          # Pointer to the exchange from which the money was withdrawn

    def getAmount(self):
        ''' Returns the amount '''
        return self.amount

    def setAmount(self, amount):
        ''' Sets the amount '''
        self.amount = amount

    def getCurrencyKey(self):
        ''' Returns the currency key '''
        return self.currencyKey

    def getExchange(self):
        ''' Returns the pointer to the exhange that the money was withdrawn from '''
        return self.exchange

    def convert(self, currencyKey):
        ''' Takes a given currency key and returns a new Money object of the given currency'''
        
        # Convert the key to uppercase
        currencyKey = currencyKey.upper()        

        # Check if the given currencies are valid
        if currencyKey not in self.exchange.currencies.keys():
            raise InvalidCurrencyKey("%s was not found in the exchange" % currencyKey)
        elif self.getCurrencyKey() not in self.exchange.currencies.keys():
            raise InvalidCurrencyKey("%s was not found in the exchange" % self.getCurrencyKey())
        
        # If they are, convert the amount and return the new Money object
        else:
            # Get the two currency objects
            oldCurrency = self.exchange.currencies[self.getCurrencyKey()]
            newCurrency = self.exchange.currencies[currencyKey]

            # Convert the old amount to the new amount
            oldAmount = self.getAmount()
            newAmount = oldAmount * (newCurrency.rate / oldCurrency.rate)

            # Create the new Money object with the appropriate currency and amount
            return Money(newAmount, currencyKey, self.exchange)
            
    def __str__(self):
        ''' Allows the object to be printed using "print" '''
        return "%f %s" % (self.amount, self.currencyKey)

    def __add__(self, other):
        ''' Adds two currencies together. The resulting currency is United States Dollars'''
        if isinstance(other, Money):
            firstAmount = self.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            secondAmount = other.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            finalAmount = firstAmount + secondAmount
            return Money(finalAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)

        # Throw an exception if an amount is given that isn't a Money object
        else:
            raise TypeError("unsupported operand type(s) for +: '%s' and '%s'" % (type(self), type(other)))

    def __sub__(self, other):
        ''' Subtracts two currencies together. The resulting currency is United States Dollars'''
        if isinstance(other, Money):
            firstAmount = self.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            secondAmount = other.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            finalAmount = firstAmount - secondAmount
            return Money(finalAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)

        # Throw an exception if an amount is given that isn't a Money object
        else:
            raise TypeError("unsupported operand type(s) for -: '%s' and '%s'" % (type(self), type(other)))

    def __mul__(self, other):
        ''' Multiplies currencies together. The resulting currency is United States Dollars by default'''
        if isinstance(other,Money):
            firstAmount = self.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            secondAmount = other.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            finalAmount = firstAmount * secondAmount
            return Money(finalAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)

        # Allow scalar multiplication 
        elif isinstance(other,int) or isinstance(other,float):
            currentAmount = self.getAmount()
            newAmount = currentAmount * other
            return Money(newAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)
        
        # Throw an exception if an amount is given that isn't a Money object
        else:
            raise TypeError("unsupported operand type(s) for *: '%s' and '%s'" % (type(self), type(other)))
    
    # Allow the Money object to come second in scalar multiplication i.e 2 * Money()
    __rmul__ = __mul__

    def __div__(self, other):
        ''' Divides two currencies together. The resulting currency is United States Dollars by default'''
        if isinstance(other,Money):
            firstAmount = self.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            secondAmount = other.convert(UNITED_STATES_DOLLARS_KEY).getAmount()
            finalAmount = firstAmount / secondAmount
            return Money(finalAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)

        # Allow scalar multiplication 
        elif isinstance(other,int) or isinstance(other,float):
            currentAmount = self.getAmount()
            newAmount = currentAmount / other
            return Money(newAmount, UNITED_STATES_DOLLARS_KEY, self.exchange)
        
        # Throw an exception if an amount is given that isn't a Money object
        else:
            raise TypeError("unsupported operand type(s) for /: '%s' and '%s'" % (type(self), type(other)))

    



class Exchange(object):
    ''' Object to store currencies and update them with the OpenExchangeRates API'''

    def __init__(self, appID):
        self.appID = appID                # The OpenExchangeRates API key to use
        self.filename = appID + '.json'   # Filename where the exchange rates are stored
        self.currencies = {}              # Stores the currencies
        self.lastUpdated = None
        
        # Load currencies from a JSON file that is storing the latest versions of the currencies if it exists
        fileFound = self.__loadFromFile()

        if fileFound:
            debug("Currency file found")

            # Check timestamp is above threshold
            now = datetime.fromtimestamp(time.time())
            difference = now - self.lastUpdated

            # If the last time the file was updated was greater than the threshold, update the exhange rates
            if difference.days > UPDATE_THRESHOLD_DAYS:
                debug("Timestamp shows file is %d days old, which is older than %d day, updating the Exchange data..." % (difference.days, UPDATE_THRESHOLD_DAYS))
                self.__loadFromOpenExhangeRatesAPI()
                self.__saveToFile()
            else:
                debug("Timestamp shows file is %d days old, which is less than %d day, loading Exchange data from file..." % (difference.days, UPDATE_THRESHOLD_DAYS))


        else: # No currency file found
            # If the internet is connected, download the exhange rates and save them to a file
            if internet_on():
                debug("Internet connection found!")
                self.__loadFromOpenExhangeRatesAPI()
                self.__saveToFile()
            else: # No currency file and no internet, thrown an exception 
                raise AccessDataFailure("No currency file or internet connection avaliable - cannot retreive currency data")
        

    def __saveToFile(self):
        ''' Saves the current exchange to file '''
        debug("Saving data to Exchange file")

        # Get the currency data, convert to a JSON string 
        jsonExchange = json.dumps(self.currencies, cls=SimpleObjectEncoder)
        
        # Remove the last bracket from the json and add on the timestamp
        timestamp = json.dumps({'timestamp': time.time()})
        jsonExchange = jsonExchange[:-1] + ',' + timestamp[1:]
        
        # Write exchange data to a file
        with open(self.filename, 'w') as f:
            f.write(jsonExchange)
            f.close()

    def __loadFromFile(self):
        ''' Loads the latest currency data from the input file '''
        debug("Loading data from Exchange file")

        # Keep track of wether the file exists or not
        fileFound = True
        
        try:
            # If the file exists open it
            with open(self.filename, 'r') as f:
                # Read the lines of the files and concatenate them into a single string
                lines = f.readlines()
                jsonExchange = ''.join(lines)

                # Decode the JSON into a dictionary
                decodedFile = json.loads(jsonExchange)
                
                # Convert the dictionary items to currency objects
                for key in decodedFile.keys():

                    # Check if the item isn't the timestamp
                    if key != 'timestamp':
                    
                        # Get the parameters for the currency from the file
                        rate = float(decodedFile[key]['rate'])
                        name = str(decodedFile[key]['name'])
                        baseKey = str(decodedFile[key]['baseKey'])
                
                        # Add the currency to the Exchange            
                        self.currencies[key] = Currency(key, baseKey, rate, name)
                    
                    else: # It's the timestamp of the file
                        self.lastUpdated = datetime.fromtimestamp(decodedFile[key])

        except IOError:
            # Otherwise mark that the file wasn't found
            fileFound = False

        return fileFound

    def __loadFromOpenExhangeRatesAPI(self):
        debug("Loading data from Open Exchange Rates API")

        # Access variables from API
        API_KEY = '?app_id=' + self.appID

        # Get the latest currency rates from the API
        try:
            # Get the latest rates
            latestValues = urllib2.urlopen(BASE_URL + GET_LATEST + API_KEY)
            latestValuesJSON = latestValues.read()
            latestValuesDecoded = json.loads(latestValuesJSON)

            # Get the names for the rates
            currencyNames = urllib2.urlopen(BASE_URL + GET_NAMES + API_KEY)
            currencyNamesJSON = currencyNames.read()
            currencyNamesDecoded = json.loads(currencyNamesJSON)
            
            # Extract the base curreny name
            baseKey = latestValuesDecoded['base']
            
            # Iterate over the currency keys 
            for key in latestValuesDecoded['rates'].keys():

                # Get the name and rate of each currency code
                rate = float(latestValuesDecoded['rates'][key])
                name = str(currencyNamesDecoded[key])
                
                # Create a currency object for each currency, then store it in the exchange
                currency = Currency(key, baseKey, rate, name)
                self.currencies[key] = currency

            # Add the current timestamp to the currency dictionary so we know when it was updated
            self.lastUpdated = time.time()

        # Handle bad app ID keys
        except urllib2.HTTPError as e:
            if e.code == 401:
                raise BadAppID("%s is an invalid app ID for openexchangerates.org" % self.appID)

    def withdraw(self, amount, currencyKey):
        ''' Creates a money object that points to this exchange with the given amount of the given currency '''
        
        # Convert the key to uppercase
        currencyKey = currencyKey.upper()

        # Check if the given currency are valid
        if currencyKey not in self.currencies.keys():
            raise InvalidCurrencyKey("%s was not found in the exchange" % currencyKey)
        
        # If it is return the Money requested
        else:
            return Money(amount, currencyKey, self)
        
        

    
    
    