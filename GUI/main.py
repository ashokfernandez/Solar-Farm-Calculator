import wx
import SolarFarmGUI

# Inherit from the ApplicationFrame created in wxFowmBuilder and create the SolarFarmCalculator
# class which implements the data processing of the GUI
class SolarFarmCalculator(SolarFarmGUI.ApplicationFrame):
	#constructor
	def __init__(self,parent):
		#initialize parent class
		SolarFarmGUI.ApplicationFrame.__init__(self,parent)
 


# Mandatory in wx, create an app, False stands for not deteriction stdin/stdout
# Refer manual for details
app = wx.App(False)
 
# Create an object of Solar Farm Calculator
frame = SolarFarmCalculator(None)

# Show the frame
frame.Show(True)

# Start the application
app.MainLoop()