import urllib2                    # For testing the internet connection
import sys
import wx
import SolarFarmGUI

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

	def __setLabelColour(self, colour):
		''' Sets the colour of the wxStaticText label, colour is a 3 or 4 length tuple
		of RGB or RGBA values between 0-255'''
		self.label.SetForegroundColour(colour)

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
			self.__setLabelColour(BLACK) 
			result = userInput

		except:
			# Something wasn't right about the number, mark the field as red and return 
			self.__setLabelColour(RED) 
			result = False

		return result

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
		self.inputFields['panelEffciency'] = InputField(self.panelEffciency_input, self.panelEffciency_label, lowerLimit=0, upperLimit=100)
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
		self.inputFields['inverterPowerFactor'] = InputField(self.inverterPowerFactor_input, self.inverterPowerFactor_label, lowerLimit=0, upperLimit=100)
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
		self.inputFields['TXCableLength'] = InputField(self.TXCableLength_input, self.TXCableLength_label, 'p')
		self.inputFields['TXCableCost'] = InputField(self.TXCableCost_input, self.TXCableCost_label, 'p')
		self.inputFields['TXCableDepreciation'] = InputField(self.TXCableDepreciation_input, self.TXCableDepreciation_label, lowerLimit=0, upperLimit=100)

		# CIRCUIT BREAKERS
		self.inputFields['circuitBreakerCost'] = InputField(self.circuitBreakerCost_input, self.circuitBreakerCost_label, 'p')
		self.inputFields['circuitBreakerDepreciation'] = InputField(self.circuitBreakerDepreciation_input, self.circuitBreakerDepreciation_label, lowerLimit=0, upperLimit=100)



		# ----- Save a reference to all the selector objects so we can quickly get their values
		self.selectors = {}

		# CURRENCIES
		self.selectors['siteCurrency'] = self.siteCost_currency
		self.selectors['financialCurrency'] = self.financialCurrency_currency
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
		

	def evt_closeApp_clicked( self, event ):
		''' Terminates the program when the red cross is clicked on the main window'''
		# DO ANY CLEAN UP HERE
		sys.exit()

	def evt_runSimulation_clicked( self, event ):
		
		# Check the internet is on, if not then display the No internet dialog
		# if not internet_on():
			# DialogBox_NoInternet()
			# return None
		
		for field in self.inputFields.values():
			field.validateField()
		# Otherwise try to validate the users data and if there is a problem, display
		# the invalid data dialog
		# if not validate_fields():
		# DialogBox_IncompleteForm()

	def evt_calculateOptimumAngle_checked( self, event ):
		''' Enables and disables the panel angle box when the "Calculate Optimum Angle" checkbox is toggled '''
		# Check if the checkbox is clicked or not to determine if the wxTextCtrl should be enabled
		isEnabled = True
		if event.IsChecked():
			isEnabled = False

		# Enable or disable the wxTextCtrl as appropriate
		self.panelAngle_input.Enable(isEnabled)

	
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