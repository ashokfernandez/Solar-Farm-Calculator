
import urllib2                    # For testing the internet connection
import sys
import wx

import SolarFarmGUI
import SolarSimulation
import SolarAssets
import PyExchangeRates
import ReverseGeocode
import Countries
import AverageTemperatureData

import numpy
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import datetime


	

# ------------------------------------------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------------------------------------------

RED = (255,0,0, 200)
BLACK = (0,0,0)
WHITE = (255,255,255,255)

# ------------------------------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------------------------------------


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

def get_currency_list():
	''' Returns a list of the avaliable currencies, as defined in currencyList.txt'''
	with open('currencyList.txt', 'r') as f:
		# Read the currencies into an array, the go through the array and remove the newlines
		currencies = f.readlines()
		currencies = [x.strip() for x in currencies]
		return currencies


def datepicker_to_datetime(datepicker):
	''' Takes a wxDateCtrl object and returns a datetime object of the date selected in the widget'''
	
	# Extract the date data from the wxDateCtrl object
	wxDate =  datepicker.GetValue()
	startYear = wxDate.GetYear()
	startMonth = wxDate.GetMonth() + 1 # Months are done from 0-11 in wxPython, datetime needs 1-12
	startDay = wxDate.GetDay()
	
	# Create the python datetime object and return it
	pyDate = datetime.date(startYear, startMonth, startDay)
	return pyDate

def FinancialFormatter(x, pos):
    '''Converts a money amount into millions or billions if the value is big enough.
       Used as a matplotlib axis formatter'''
    
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


FINANCIAL_RESULTS = None
POWER_RESULTS = None

def showResults():
	global POWER_RESULTS
	global FINANCIAL_RESULTS

	# Plot the results
	formatter = FuncFormatter(FinancialFormatter)

	plt.figure(1, figsize=(14, 11))
	plt.subplot(311)
	plt.plot(POWER_RESULTS['days'], POWER_RESULTS['averagePower'])
	plt.title('Average Power of the PV farm')
	plt.ylabel('Power (kW)')

	# plt.subplot(212)
	# plt.plot(POWER_RESULTS['days'], POWER_RESULTS['sunnyTime'], 'g')
	# plt.title('Electrical energy of the PV farm at GEP')
	# plt.ylabel('Energy (kWh)')

	a = plt.subplot(312)
	a.yaxis.set_major_formatter(formatter)
	p1, = plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['netAssetValue'], 'b') 
	p2, = plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['loanValue'], 'r')
	plt.title('Net Asset Value and Loan Value')
	plt.ylabel('(%s)' % FINANCIAL_RESULTS['baseCurrency'])
	plt.legend([p1, p2], ["Net Asset Value", "Loan Value"], loc=7)


	a = plt.subplot(313)
	a.yaxis.set_major_formatter(formatter)
	plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['accumulativeRevenue'], 'g')
	plt.title('Accumlated Revenue')
	plt.ylabel('(%s)' % FINANCIAL_RESULTS['baseCurrency'])
	# plt.figure(2)
	# a = plt.subplot(311)
	# a.yaxis.set_major_formatter(formatter)
	# plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['netAssetValue'])
	# plt.title('Net Asset Value')

	# a = plt.subplot(312)
	# a.yaxis.set_major_formatter(formatter)
	# plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['loanValue'], 'r')
	# plt.title('Loan Value')

	# a = plt.subplot(313)
	# a.yaxis.set_major_formatter(formatter)
	# plt.plot(FINANCIAL_RESULTS['days'], FINANCIAL_RESULTS['accumulativeRevenue'], 'g')
	# plt.title('Accumlative Revenue')
	
	# Output the peak currents in each conductor
	resultsText =   "--------------------------------------------\n"
	resultsText +=  "------------ POWER FLOW RESULTS ------------\n"
	resultsText +=  "--------------------------------------------\n\n"
	resultsText +=  "PEAK CURRENTS IN CONDUCTORS ----------------\n"
	resultsText +=  "Peak Current in DC Cable : \n    %.2f A\n" % POWER_RESULTS['peakDC']
	resultsText +=  "Peak Current in AC Cable : \n    %.2f A\n" % POWER_RESULTS['peakAC1']
	resultsText +=  "Peak Current in Transmission Cable : \n    %.2f A\n\n" % POWER_RESULTS['peakAC2']

	# Get the maximum average power output
	maxPower = max(POWER_RESULTS['averagePower'])
	minPower = min(POWER_RESULTS['averagePower'])
	resultsText += "AVERAGE DAILY POWER -------------------------\n"
	resultsText += "Maximum : \n    %.2f kW\n" % maxPower
	resultsText += "Minimum : \n    %.2f kW\n\n" % minPower

	# Accumulate the energy
	totalEnergy = sum(POWER_RESULTS['electricalEnergy']) / 1000.0
	averageEnergy = numpy.array(POWER_RESULTS['electricalEnergy'])
	averageEnergy = numpy.mean(averageEnergy) / 1000.0

	resultsText += "ENERGY EXPORTED TO GRID ---------------------\n"
	resultsText += "Accumulated Total : \n    %.2f MWh\n" % totalEnergy
	resultsText += "Daily Average : \n    %.2f MWh\n\n" % averageEnergy


	# Averate the effciencies
	electricalEfficiency = numpy.array(POWER_RESULTS['electricalEffciency'])
	totalEfficiency = numpy.array(POWER_RESULTS['totalEffciency'])

	electricalEfficiency = numpy.mean(electricalEfficiency)
	totalEfficiency = numpy.mean(totalEfficiency)

	resultsText += "EFFICIENCIES -------------------------------\n"
	resultsText += "Total efficiency (Sunlight energy to electricity) : \n    %.2f%% \n" % totalEfficiency
	resultsText += "Electrical efficiency (Panels output to grid connection) : \n    %.2f%% \n\n\n\n" % electricalEfficiency


	
	# Financial Results
	resultsText +=  "--------------------------------------------\n"
	resultsText +=  "----------- FINANCIAL INFORMATION ----------\n"
	resultsText +=  "--------------------------------------------\n\n"

	resultsText += "Initial Cost : \n    $ %.2f (%s)\n " % (FINANCIAL_RESULTS['loanValue'][0], FINANCIAL_RESULTS['baseCurrency'])
	resultsText += "Total Revenue : \n    $ %.2f (%s)\n " % (FINANCIAL_RESULTS['accumulativeRevenue'][-1], FINANCIAL_RESULTS['baseCurrency'])


	resultsBox = DialogBox_SimulationResults(resultsText)

	plt.show()


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
	MATERIALS['Copper'] = SolarAssets.Material(name='Cu', resistivity=1.68e-8, tempCoefficient=3.62e-3)
	MATERIALS['Aluminium'] = SolarAssets.Material(name='Al', resistivity=2.82e-8, tempCoefficient=3.9e-3)

	# Instantiate the panel object
	panel = SolarAssets.PVPanel(voltage=inputParameters['panelVoltage'], 
		 			rating=inputParameters['panelRating'], 
		 			degradationRate=inputParameters['panelDegradation'], 
		 			area=inputParameters['panelArea'], 
		 			cost=inputParameters['panelCost'], 
		 			currency=inputParameters['panelCurrency'],
		 			depRate=inputParameters['panelDepreciation'])

	module = SolarAssets.PVModule(panelType=panel, 
		 			  panelNum=inputParameters['siteNumPanels'])
	
	array = SolarAssets.PVArray(moduleType=module, 
					moduleNum=inputParameters['siteNumModules'], 
					arrayAngle=inputParameters['panelAngle'])

	

	dcCable = SolarAssets.DCCable(diameter=inputParameters['DCCableDiameter'], 
					  material=MATERIALS[inputParameters['DCCableMaterial']], 
					  length=inputParameters['DCCableLength'], 
					  costPerMeter=inputParameters['DCCableCost'], 
					  depRate=inputParameters['DCCableDepreciation'])	

	ac1Cable = SolarAssets.AC1Cable(strandNum=inputParameters['ACCableNumStrands'], 
						diameter=inputParameters['ACCableDiameter'], 
						material=MATERIALS[inputParameters['ACCableMaterial']], 
						length=inputParameters['ACCableLength'], 
						costPerMeter=inputParameters['ACCableCost'], 
						depRate=inputParameters['ACCableDepreciation'])

	ac2Cable = SolarAssets.AC2Cable(strandNum=inputParameters['TXCableNumStrands'], 
						diameter=inputParameters['TXCableDiameter'], 
						material=MATERIALS[inputParameters['TXCableMaterial']], 
						length=TXCableLength, 
						costPerMeter=inputParameters['TXCableCost'], 
						depRate=inputParameters['TXCableDepreciation'])

	inverter = SolarAssets.Inverter(powerFactor=inputParameters['inverterPowerFactor'], 
						efficiency=inputParameters['inverterEfficiency'], 
						voltage=inputParameters['inverterOutputVoltage'], 
						cost=inputParameters['inverterCost'] , 
						depRate=inputParameters['inverterDepreciation'])
	
	transformer = SolarAssets.Transformer(voltage=inputParameters['transformerOutputVoltage'], 
							  efficiency=inputParameters['transformerEfficiency'] , 
							  VARating=inputParameters['transformerRating'] , 
							  cost=inputParameters['transformerCost'] , 
							  depRate=inputParameters['transformerDepreciation'])

	circuitBreaker = SolarAssets.CircuitBreaker(cost=inputParameters['circuitBreakerCost'])

	site = SolarAssets.Site(transformerNum=inputParameters['siteNumTransformers'], 
				arrayNum=inputParameters['siteNumArrays'], 
				latitude=inputParameters['siteLatitude'], 
				longitude=inputParameters['siteLongitude'],
		  		circuitBreakerNum=inputParameters['siteNumCircuitBreakers'], 
		  		inverterNum=inputParameters['siteNumInverters'], 
		  		temperature=temperature, 
		  		landPrice=inputParameters['siteCost'],
		  		currency=inputParameters['siteCurrency'],
				landAppRate=inputParameters['siteAppreciation'])

	financial = SolarAssets.Financial(maintenance=inputParameters['financialMaintenance'], 
						  miscExpenses=inputParameters['financialMiscExpenses'], 
						  interestRate =inputParameters['financialInterestRate'],
						  powerPrice = inputParameters['financialPowerPrice'], 
						  baseCurrency=inputParameters['financialBaseCurrency'])

	simulation = SolarSimulation.Simulation(start=inputParameters['startDate'], finish=inputParameters['endDate'], 
							PVPanel=panel, PVModule=module, PVArray=array, 
		               		DCCable=dcCable, Inverter=inverter, AC1Cable=ac1Cable, Transformer=transformer, 
		                   	AC2Cable=ac2Cable, CircuitBreaker=circuitBreaker, Site=site, Financial=financial,
	                       	numThreads=50, simulationTimestepMins=60)

	return simulation




# ------------------------------------------------------------------------------------------------------
# DIALOG BOXES
# ------------------------------------------------------------------------------------------------------

# Implement the functionality of the 'No Internet' dialog box
class DialogBox_NoInternet(SolarFarmGUI.NoInternet):
	def __init__( self ):
		''' Creates the "No Internet" dialog box and shows it as a modal dialog which
			blocks the program until it is dismissed'''
		SolarFarmGUI.NoInternet.__init__(self, None)
		self.ShowModal()

	def evt_dialogOK_clicked( self, event ):
		''' Closes the window when the OK button is pressed'''
		self.EndModal(1)

# Implement the functionality of the 'Incomplete Form' dialog box
class DialogBox_IncompleteForm(SolarFarmGUI.IncompleteForm):
	def __init__( self ):
		''' Creates the "Incomplete Form" dialog box and shows it as a modal dialog which
			blocks the program until it is dismissed'''
		SolarFarmGUI.IncompleteForm.__init__(self, None)
		self.ShowModal()

	def evt_dialogOK_clicked( self, event ):
		''' Closes the window when the OK button is pressed'''
		self.EndModal(1)

# Implement the functionality of the 'Fatal Error' message dialog
class DialogBox_FatalError(SolarFarmGUI.FatalError):
	def __init__( self , errorMessage):
		''' Creates the "Fatal Error" dialog box and uses the given string as the error message.
		the program will quit when the dialog is dismissed'''
		SolarFarmGUI.FatalError.__init__(self, None)
		self.fatalErrorLabel.AppendText(errorMessage)
		self.ShowModal()

	def evt_dialogCloseProgram_clicked( self, event ):
		''' Terminates the program after the user has been notified of a fatal error'''
		self.EndModal(1)
		sys.exit()


# Implement the functionality of the GeoCode error message
class DialogBox_GeoCodeError(SolarFarmGUI.GeoCodeError):
	def __init__( self ):
		''' Creates the "GeoCode Error" dialog box and uses the given string as the error message.
		the program will quit when the dialog is dismissed'''
		SolarFarmGUI.GeoCodeError.__init__(self, None)
		self.ShowModal()

	def evt_dialogOK_clicked( self, event ):
		''' Closes the window when the OK button is pressed'''
		self.EndModal(1)


# Implement the functionality of the Date error message
class DialogBox_DateError(SolarFarmGUI.DateError):
	def __init__( self ):
		''' Creates the "Date Error" dialog box and uses the given string as the error message.
		the program will quit when the dialog is dismissed'''
		SolarFarmGUI.DateError.__init__(self, None)
		self.ShowModal()

	def evt_dialogOK_clicked( self, event ):
		''' Closes the window when the OK button is pressed'''
		self.EndModal(1)


# Implement the functionality of the 'Fatal Error' message dialog
class DialogBox_SimulationResults(SolarFarmGUI.SimulationResults):
	def __init__( self , simulationResults):
		''' Creates the "Fatal Error" dialog box and uses the given string as the error message.
		the program will quit when the dialog is dismissed'''
		SolarFarmGUI.SimulationResults.__init__(self, None)
		self.simulationResultsLabel.AppendText(simulationResults)
		self.Show()

	def evt_dialogOK_clicked( self, event ):
		''' Closes the window when the OK button is pressed'''
		self.Destroy()


# Class to show a progress dialog when the simulation is running
class DialogBox_ProgressDialog(object):
	def __init__(self, parent, maxItems=100):
		''' Dialog box to show while the simulation is in progress '''

		# Add 10% to the max items to account for the financial simulation
		maxItems *= 1.1
		maxItems = round(maxItems)

		# Create the progress dialog
		self.progressBox = wx.ProgressDialog("Running Simulation",
                               			"Simulating Power Generation",
                               maximum = maxItems,
                               parent=parent,
                               style = wx.PD_CAN_ABORT
                                | wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                #| wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME)
 		
	def update(self, itemsLeft, newMessage=None):
		''' Passes the dialog the updated amount of items left in the simulation queue '''
		
		# If we are 90% of the way through tell the user we are up to the financials
		if newMessage is not None:
			self.progressBox.Update(itemsLeft, newMessage)
		else:
			self.progressBox.Update(itemsLeft)

 	def closeDialog(self):
 		''' Closes the dialog box'''
		self.progressBox.Destroy()
		self.progressBox.EndModal(1)


# ------------------------------------------------------------------------------------------------------
# INPUT VALIDATION CLASS
# ------------------------------------------------------------------------------------------------------

# Encapsulate data entry and validation
class InputField(object):
	'''Stores an input field and corrsponding label and encapsulates validation of the input field'''
	RED = (255,0,0, 200)
	BLACK = (0,0,0)
	WHITE = (255,255,255,255)

	''' Holds an input field wxTextCtl and it's corrosponding label'''
	def __init__(self, field, label, condition='', upperLimit=False, lowerLimit=False):
		self.field = field
		self.label = label
		self.condition = condition.lower()
		self.upperLimit = upperLimit
		self.lowerLimit = lowerLimit

	def __getFieldValue(self):
		''' Returns the value of the wxTextCtl field'''
		return self.field.GetValue()

	def setLabelColour(self, colour):
		''' Sets the colour of the wxStaticText label, colour is a 3 or 4 length tuple
		of RGB or RGBA values between 0-255'''
		self.label.SetForegroundColour(colour)

	def setFieldValue(self, value):
		''' Allows an external program to set the value in the field for testing purposes '''
		self.field.AppendText(value)

	def validateField(self):
		''' Validates the input in the wxTextCtl inputField to be purely numeric. Condition can be either a string 
		containing "p" or "n" to contrain the inputField to positive or negative numbers respectivly, and can also
		contain "i" to specify the number must be an integer. These can be combined, for instance "pi" specifies a
		positive integer. If the field is valid the wxStaticText label fieldLabel's colour text is set to black,
		otherwise it is set to red. The funtion returns the fields value if the input was valid, otherwise it returns 
		false. '''
	
		userInput = self.__getFieldValue()
		result = None
		
		try:
			# Attempt to evalute the users input as a mathmatical expression
			userInput = eval(userInput)

			# Check the value is an integer if it is supposed to be
			if 'i' in self.condition:
				if not isinstance(userInput,int):
					raise TypeError

			# Check the value if positive if it's supposed to be
			if 'p' in self.condition:
				if userInput < 0:
					raise ValueError

			# Check the value if negative if it's supposed to be
			if 'n' in self.condition:
				if userInput > 0:
					raise ValueError

			# Check the number if below it's upper limit
			if self.upperLimit is not False:
				if userInput > self.upperLimit:
					raise ValueError				

			if self.lowerLimit is not False:
				if userInput < self.lowerLimit:
					raise ValueError								
			
			# Otherwise the value is all good, set the fields to their appropriate colours
			# and mark valid as true
			self.setLabelColour(BLACK) 
			result = userInput

		except:
			# Something wasn't right about the number, mark the field as red and return 
			self.setLabelColour(RED) 
			result = False

		return result

# Special case when an input field is automatically calculated from other data
class OptionalInputField(InputField):
	def __init__(self, field, label, checkbox, condition='', upperLimit=False, lowerLimit=False):
		''' Initialises the input field superclass and saves the checkbox '''
		# Initialise superclass stuff	
		InputField.__init__(self, field, label, condition, upperLimit, lowerLimit)

		# Save a reference to the checkbox
		self.checkbox = checkbox

	def getCheckboxState(self):
		''' Returns the state of the checkbox so the simulation can be told wether or not the value is valid
		    or needs to be calculated. True if the checkbox is checked, otherwise False.'''
		return self.checkbox.IsChecked()

	def validateField(self):
		'''If the field is to be calculated from other field values return a placeholder value, otherwise
		   validate like normal. The placeholder value is required as the fields that depend on this one
		   need to be validated first'''
		# If the checkbox is ticked ensure the field label is black and return the placeholder 
		if self.checkbox.IsChecked():
			self.setLabelColour(InputField.BLACK)
			return None
		# Otherwise validate as usual
		else:
			return InputField.validateField(self)

# ------------------------------------------------------------------------------------------------------
# MAIN APPLICATION FRAME
# ------------------------------------------------------------------------------------------------------

# Inherit from the ApplicationFrame created in wxFowmBuilder and create the SolarFarmCalculator
# class which implements the data processing of the GUI
class SolarFarmCalculator(SolarFarmGUI.ApplicationFrame):

	def __init__(self,parent):
		''' Intialises the main parent window of the program'''
		#initialize parent class
		SolarFarmGUI.ApplicationFrame.__init__(self,parent)

		# Attempt to load the list of avaliable currencies
		try:
			currencies = get_currency_list()
		except:
			DialogBox_FatalError("Unable to load the list of currencies from currencyList.txt")

		# Set the values of all the currencie lists to the list of avaliable currencies
		self.siteCost_currency.SetItems(currencies)
		self.financialCurrency_currency.SetItems(currencies)
		self.panelCost_currency.SetItems(currencies)
		self.circuitBreakerCost_currency.SetItems(currencies)
		self.DCCableCost_currency.SetItems(currencies)
		self.inverterCost_currency.SetItems(currencies)
		self.ACCableCost_currency.SetItems(currencies)
		self.transformerCost_currency.SetItems(currencies)
		self.TXCableCost_currency.SetItems(currencies)




		# ----- Save a reference to all the input fields and their labels
		self.inputFields = {}
		self.optionalInputFields = {}
		
		# SITE VARIABLES
		self.inputFields['siteCost'] = InputField(self.siteCost_input, self.siteCost_label, 'p')
		self.inputFields['siteAppreciation'] = InputField(self.siteAppreciation_input, self.siteAppreciation_label)
		self.inputFields['siteLatitude'] = InputField(self.siteLatitude_input, self.siteLatitude_label, upperLimit=90, lowerLimit=-90)
		self.inputFields['siteLongitude'] = InputField(self.siteLongitude_input, self.siteLongitude_label, upperLimit=180, lowerLimit=-180)
		self.inputFields['siteGridLatitude'] = InputField(self.siteGridLatitude_input, self.siteGridLatitude_label, upperLimit=90, lowerLimit=-90)
		self.inputFields['siteGridLongitude'] = InputField(self.siteGridLongitude_input, self.siteGridLongitude_label, upperLimit=180, lowerLimit=-180)
		self.inputFields['siteNumPanels'] = InputField(self.siteNumPanels_input, self.siteNumPanels_label, 'pi')
		self.inputFields['siteNumModules'] = InputField(self.siteNumModules_input, self.siteNumModules_label, 'pi')
		self.inputFields['siteNumArrays'] = InputField(self.siteNumArrays_input, self.siteNumArrays_label, 'pi')
		self.inputFields['siteNumTransformers'] = InputField(self.siteNumTransformers_input, self.siteNumTransformers_label, 'pi')
		self.inputFields['siteNumInverters'] = InputField(self.siteNumInverters_input, self.siteNumInverters_label, 'pi')
		self.inputFields['siteNumCircuitBreakers'] = InputField(self.siteNumCircuitBreakers_input, self.siteNumCircuitBreakers_label, 'pi')

		# FINANCIAL VARIABLES
		self.inputFields['financialInterestRate'] = InputField(self.financialInterestRate_input, self.financialInterestRate_label)
		self.inputFields['financialMiscExpenses'] = InputField(self.financialMiscExpenses_input, self.financialMiscExpenses_label, 'p')
		self.inputFields['financialMaintenance'] = InputField(self.financialMaintenance_input, self.financialMaintenance_label, 'p')
		self.inputFields['financialPowerPrice'] = InputField(self.financialPowerPrice_input, self.financialPowerPrice_label, 'p')

		# PANEL VARIABLES
		self.inputFields['panelVoltage'] = InputField(self.panelVoltage_input, self.panelVoltage_label, 'p')
		self.inputFields['panelAngle'] = InputField(self.panelAngle_input, self.panelAngle_label, 'p')
		self.inputFields['panelRating'] = InputField(self.panelRating_input, self.panelRating_label, 'p')
		self.inputFields['panelDegradation'] = InputField(self.panelDegradation_input, self.panelDegradation_label, lowerLimit=0, upperLimit=100)
		self.inputFields['panelArea'] = InputField(self.panelArea_input, self.panelArea_label, 'p')
		self.inputFields['panelCost'] = InputField(self.panelCost_input, self.panelCost_label, 'p')
		self.inputFields['panelDepreciation'] = InputField(self.panelDepreciation_input, self.panelDepreciation_label, lowerLimit=0, upperLimit=100)

		# DC CABLE VARIABLES
		self.inputFields['DCCableDiameter'] = InputField(self.DCCableDiameter_input, self.DCCableDiameter_label, 'p')
		self.inputFields['DCCableLength'] = InputField(self.DCCableLength_input, self.DCCableLength_label, 'p')
		self.inputFields['DCCableCost'] = InputField(self.DCCableCost_input, self.DCCableCost_label, 'p')
		self.inputFields['DCCableDepreciation'] = InputField(self.DCCableDepreciation_input, self.DCCableDepreciation_label, lowerLimit=0, upperLimit=100)

		# INVERTER VARIABLES
		self.inputFields['inverterPowerFactor'] = InputField(self.inverterPowerFactor_input, self.inverterPowerFactor_label, lowerLimit=0, upperLimit=1)
		self.inputFields['inverterEfficiency'] = InputField(self.inverterEfficiency_input, self.inverterEfficiency_label, lowerLimit=0, upperLimit=100)
		self.inputFields['inverterOutputVoltage'] = InputField(self.inverterOutputVoltage_input, self.inverterOutputVoltage_label, 'p')
		self.inputFields['inverterCost'] = InputField(self.inverterCost_input, self.inverterCost_label, 'p')
		self.inputFields['inverterDepreciation'] = InputField(self.inverterDepreciation_input, self.inverterDepreciation_label, lowerLimit=0, upperLimit=100)

		# AC CABLE VARIABLES
		self.inputFields['ACCableDiameter'] = InputField(self.ACCableDiameter_input, self.ACCableDiameter_label, 'p')
		self.inputFields['ACCableNumStrands'] = InputField(self.ACCableNumStrands_input, self.ACCableNumStrands_label, 'pi')
		self.inputFields['ACCableLength'] = InputField(self.ACCableLength_input, self.ACCableLength_label, 'p')
		self.inputFields['ACCableCost'] = InputField(self.ACCableCost_input, self.ACCableCost_label, 'p')
		self.inputFields['ACCableDepreciation'] = InputField(self.ACCableDepreciation_input, self.ACCableDepreciation_label, lowerLimit=0, upperLimit=100)

		# TRANSFORMER VARIABLES
		self.inputFields['transformerOutputVoltage'] = InputField(self.transformerOutputVoltage_input, self.transformerOutputVoltage_label, 'p')
		self.inputFields['transformerEfficiency'] = InputField(self.transformerEfficiency_input, self.transformerEfficiency_label, lowerLimit=0, upperLimit=100)
		self.inputFields['transformerRating'] = InputField(self.transformerRating_input, self.transformerRating_label, 'p')
		self.inputFields['transformerCost'] = InputField(self.transformerCost_input, self.transformerCost_label, 'p')
		self.inputFields['transformerDepreciation'] = InputField(self.transformerDepreciation_input, self.transformerDepreciation_label, lowerLimit=0, upperLimit=100)

		# TX CABLE VARIABLES
		self.inputFields['TXCableDiameter'] = InputField(self.TXCableDiameter_input, self.TXCableDiameter_label, 'p')
		self.inputFields['TXCableNumStrands'] = InputField(self.TXCableNumStrands_input, self.TXCableNumStrands_label, 'pi')
		self.optionalInputFields['TXCableLength'] = OptionalInputField(self.TXCableLength_input, self.TXCableLength_label, self.TXCableCalculateLength_checkBox, 'p')
		self.inputFields['TXCableCost'] = InputField(self.TXCableCost_input, self.TXCableCost_label, 'p')
		self.inputFields['TXCableDepreciation'] = InputField(self.TXCableDepreciation_input, self.TXCableDepreciation_label, lowerLimit=0, upperLimit=100)

		# CIRCUIT BREAKERS
		self.inputFields['circuitBreakerCost'] = InputField(self.circuitBreakerCost_input, self.circuitBreakerCost_label, 'p')
		self.inputFields['circuitBreakerDepreciation'] = InputField(self.circuitBreakerDepreciation_input, self.circuitBreakerDepreciation_label, lowerLimit=0, upperLimit=100)



		# ----- Save a reference to all the selector objects so we can quickly get their values
		self.selectors = {}

		# CURRENCIES
		self.selectors['siteCurrency'] = self.siteCost_currency
		self.selectors['financialBaseCurrency'] = self.financialCurrency_currency
		self.selectors['panelCurrency'] = self.panelCost_currency
		self.selectors['circuitBreakerCurrency'] = self.circuitBreakerCost_currency
		self.selectors['DCCableCurrency'] = self.DCCableCost_currency
		self.selectors['inverterCurrency'] = self.inverterCost_currency
		self.selectors['ACCableCurrency'] = self.ACCableCost_currency
		self.selectors['transformerCurrency'] = self.transformerCost_currency
		self.selectors['TXCableCurrency'] = self.TXCableCost_currency

		# MATERIALS
		self.selectors['DCCableMaterial'] = self.DCCableMaterial_input
		self.selectors['ACCableMaterial'] = self.ACCableMaterial_input
		self.selectors['TXCableMaterial'] = self.TXCableMaterial_input

		# USED FOR TESTING PURPOSES
		self.__loadDemoSimulation()

	
	def __loadDemoSimulation(self):
		''' Loads demo values into the simulation fields for testing purposes '''	
		# SITE VARIABLES
		self.inputFields['siteCost'].setFieldValue('10000000')
		self.inputFields['siteAppreciation'].setFieldValue('1.03')
		self.inputFields['siteLatitude'].setFieldValue('-21.0928')
		self.inputFields['siteLongitude'].setFieldValue('-175.1050')
		self.inputFields['siteGridLatitude'].setFieldValue('-21.0910')
		self.inputFields['siteGridLongitude'].setFieldValue('-175.1102')
		self.inputFields['siteNumPanels'].setFieldValue('30')
		self.inputFields['siteNumModules'].setFieldValue('7')
		self.inputFields['siteNumArrays'].setFieldValue('30')
		self.inputFields['siteNumTransformers'].setFieldValue('1')
		self.inputFields['siteNumInverters'].setFieldValue('2')
		self.inputFields['siteNumCircuitBreakers'].setFieldValue('15')

		# FINANCIAL VARIABLES
		self.inputFields['financialInterestRate'].setFieldValue('6')
		self.inputFields['financialMiscExpenses'].setFieldValue('100000')
		self.inputFields['financialMaintenance'].setFieldValue('25000')
		self.inputFields['financialPowerPrice'].setFieldValue('0.25')

		# PANEL VARIABLES
		self.inputFields['panelVoltage'].setFieldValue('30.5')
		self.inputFields['panelAngle'].setFieldValue('21')
		self.inputFields['panelRating'].setFieldValue('230')
		self.inputFields['panelDegradation'].setFieldValue('0.4')
		self.inputFields['panelArea'].setFieldValue('1.63')
		self.inputFields['panelCost'].setFieldValue('50')
		self.inputFields['panelDepreciation'].setFieldValue('6')

		# DC CABLE VARIABLES
		self.inputFields['DCCableDiameter'].setFieldValue('20')
		self.inputFields['DCCableLength'].setFieldValue('100')
		self.inputFields['DCCableCost'].setFieldValue('100')
		self.inputFields['DCCableDepreciation'].setFieldValue('6')

		# INVERTER VARIABLES
		self.inputFields['inverterPowerFactor'].setFieldValue('1.00')
		self.inputFields['inverterEfficiency'].setFieldValue('95')
		self.inputFields['inverterOutputVoltage'].setFieldValue('400')
		self.inputFields['inverterCost'].setFieldValue('10000')
		self.inputFields['inverterDepreciation'].setFieldValue('6')

		# AC CABLE VARIABLES
		self.inputFields['ACCableDiameter'].setFieldValue('6')
		self.inputFields['ACCableNumStrands'].setFieldValue('5')
		self.inputFields['ACCableLength'].setFieldValue('100')
		self.inputFields['ACCableCost'].setFieldValue('100')
		self.inputFields['ACCableDepreciation'].setFieldValue('6')

		# TRANSFORMER VARIABLES
		self.inputFields['transformerOutputVoltage'].setFieldValue('11e3')
		self.inputFields['transformerEfficiency'].setFieldValue('98.9')
		self.inputFields['transformerRating'].setFieldValue('1')
		self.inputFields['transformerCost'].setFieldValue('10000')
		self.inputFields['transformerDepreciation'].setFieldValue('6')

		# TX CABLE VARIABLES
		self.inputFields['TXCableDiameter'].setFieldValue('2')
		self.inputFields['TXCableNumStrands'].setFieldValue('5')
		self.optionalInputFields['TXCableLength'].setFieldValue('1000')
		self.inputFields['TXCableCost'].setFieldValue('100')
		self.inputFields['TXCableDepreciation'].setFieldValue('6')

		# CIRCUIT BREAKERS
		self.inputFields['circuitBreakerCost'].setFieldValue('4000')
		self.inputFields['circuitBreakerDepreciation'].setFieldValue('6')


	def evt_closeApp_clicked( self, event ):
		''' Terminates the program when the red cross is clicked on the main window'''
		# DO ANY CLEAN UP HERE
		sys.exit()

	def evt_runSimulation_clicked( self, event ):
		''' Event that is run when the "Run Simulation" button is clicked. This will validate all the inputs, check for
		an internet connection and run the simulation if all the inputs are correct. Otherwise an error dialog is shown
		telling the user what they did wrong'''

		# Check the internet is on, if not then display the No internet dialog
		if not internet_on():
			DialogBox_NoInternet()
			return None
		

		# Save the validated input data to a dictionary
		inputData = {}

		# Validate the required input fields
		for key in self.inputFields.keys():
			inputData[key] = self.inputFields[key].validateField()

		# Check the optional input fields
		optionalData = {}
		for key in self.optionalInputFields.keys():
			optionalData[key] = self.optionalInputFields[key].validateField()	

		# Check if the inputs are valid or not
		inputsValid = (False not in inputData.values()) or (False not in optionalData.values())

		# If the inputs aren't valid, abort the simulation with an error message
		if not inputsValid:
			DialogBox_IncompleteForm()
			return None



		# Check the dates are valid
		startDate = datepicker_to_datetime(self.simulationStart_input)
		endDate = datepicker_to_datetime(self.simulationEnd_input)

		# If the dates are invalid throw an exception
		if (endDate - startDate).days <= 0:
			DialogBox_DateError()
			return None

		# Otherwise save the dates
		else:
			inputData['startDate'] = startDate
			inputData['endDate'] = endDate



		# Get the value of the selector boxes
		for key in self.selectors.keys():
			
			# Get the index and value of the option currently selected - convert from unicode to str
			index = self.selectors[key].GetCurrentSelection()	
			value = self.selectors[key].GetString(index)
			value = str(value)

			# If the key is a currency, strip the name of the currency off so just the code remains
			if 'Currency' in key:
				valueBits = value.split(':')
				value = valueBits[0]
			
			# Save the selection
			inputData[key] = value


		# Try to run the simulation, catching any errors that may occur
		try:
			# Create a simulation
			simulation = CreateSimulation(inputData, optionalData)
			
			# Create a progress dialog
			progressDialog = DialogBox_ProgressDialog(self)

			# Start the simulation and update the progress box
			simulation.runPower()
			powerProgress = simulation.getPowerProgress()

			# Keep checking the power progress and update the dialog box
			while powerProgress < 95:
				wx.MilliSleep(150)
				progressDialog.update(powerProgress)
				powerProgress = simulation.getPowerProgress()

			# Wait for the power to finish the run the financial
			global POWER_RESULTS
			global FINANCIAL_RESULTS
			POWER_RESULTS = simulation.getPowerResults()
			progressDialog.update(98, "Running Financial Simulations")
			
			# This will block until it is done
			simulation.runFinancial()

			# Get the financial results and close the progress dialog
			FINANCIAL_RESULTS = simulation.getFinancialResults()
				
			# Close the progress dialog
			progressDialog.closeDialog()
			
			# self.showResults(powerResults, financialResults)
			wx.CallLater(100, showResults)

			return None

		except ReverseGeocode.CountryNotFound:
			DialogBox_GeoCodeError()
			return None
		# except:
			# DialogBox_FatalError("Something went wrong in the simulation, the program will terminate now.\n Goodbye.")
			
			
	

		
		

	
	def evt_calculateTXCableLength_checked( self, event ):
		''' Enables and disables the tx cable length text ctrl when the "Calculate Cable Length" checkbox is toggled '''
		# Check if the checkbox is clicked or not to determine if the wxTextCtrl should be enabled
		isEnabled = True
		if event.IsChecked():
			isEnabled = False

		# Enable or disable the wxTextCtrl as appropriate
		self.TXCableLength_input.Enable(isEnabled)

		




# ------------------------------------------------------------------------------------------------------
# BOOTSTRAP MAIN PROGRAM
# ------------------------------------------------------------------------------------------------------

# Mandatory in wx, create an app, False stands for not deteriction stdin/stdout
# Refer manual for details
app = wx.App(False)
 
# Create an object of Solar Farm Calculator
frame = SolarFarmCalculator(None)

# Show the frame
frame.Show(True)

# Start the application
app.MainLoop()