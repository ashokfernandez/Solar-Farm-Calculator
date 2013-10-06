import urllib2                    # For testing the internet connection
import sys
import wx
import SolarFarmGUI


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
# MAIN APPLICATION FRAME
# ------------------------------------------------------------------------------------------------------


# Inherit from the ApplicationFrame created in wxFowmBuilder and create the SolarFarmCalculator
# class which implements the data processing of the GUI
class SolarFarmCalculator(SolarFarmGUI.ApplicationFrame):

	def __init__(self,parent):
		''' Intialises the main parent window of the program'''
		#initialize parent class
		SolarFarmGUI.ApplicationFrame.__init__(self,parent)

		# Attempt to load the list of currencies
		try:
			currencies = get_currency_list()
		except:
			DialogBox_FatalError("Unable to load the list of currencies from currencyList.txt")

		print currencies

	def evt_closeApp_clicked( self, event ):
		''' Terminates the program when the red cross is clicked on the main window'''
		# DO ANY CLEAN UP HERE
		sys.exit()

	def evt_runSimulation_clicked( self, event ):
		
		# Check the internet is on, if not then display the No internet dialog
		# if not internet_on():
			# DialogBox_NoInternet()
			# return None
		
		# Otherwise try to validate the users data and if there is a problem, display
		# the invalid data dialog
		# DialogBox_IncompleteForm()
		DialogBox_FatalError(" Foo Bar Hoo Haa a fatal error has occured. Thats not nice. Goodbye!")
		



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