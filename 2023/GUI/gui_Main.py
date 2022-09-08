'''
Main GUI Window all GUI setup and computation is done here
'''
# Import
# Custom Imports
from gui_layout import Ui_UDIP_Viewer

# GUI and Threading stuff
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *

# General Imports
import UDIP_Lib_V20 as UDIP_Lib
import pyqtgraph
import numpy as np
from scipy import optimize
from scipy import stats

# Define Main_Window
class MasterWindow(Ui_UDIP_Viewer):
    """
    Main GUI Window
    """

    def __init__(self):
        """
        Initializes the UDIP GUI, and, in extension, the UDIP Library and Handler(not yet though)
        """
        # Pull init values from the layout
        Ui_UDIP_Viewer.__init__(self)

        # Global Variables
        self.filename = "UDIP0000.DAT"
        self.Outpath = "Output/"

        # Arrays used to collect relevant indexies for each packet
        self.packets = []
        self.ind_sensor = []
        self.ind_medium = []
        self.ind_large = []
        self.ind_burst = []
        self.ind_constant = []

        
        # Load the UDIP Data
        self.Load_data()

    def setupui(self, MainWindow: QtWidgets.QMainWindow):
        """"
        Sets up the gui and adds functionality to the buttons and such
        """
        # Import Layout from Designer
        super().setupUi(MainWindow)

        # Add functionality to GUI Buttons
        self.PlotButton.clicked.connect(lambda: self.SendPlot())        # Plot Button Pushes Selection To Plot
        self.NextButton.clicked.connect(lambda: self.IndexSelectionCombo.setCurrentIndex(self.IndexSelectionCombo.currentIndex() + 1))
        self.PreviousButton.clicked.connect(lambda: self.IndexSelectionCombo.setCurrentIndex(self.IndexSelectionCombo.currentIndex() - 1))

        # If a GUI Button is Updated, refresh the display
        self.TimeIndexButton.toggled.connect(lambda: self.updGui())
        self.IndexIndexButton.toggled.connect(lambda: self.updGui())
        self.PlotTypeCombo.activated.connect(lambda: self.updGui())
        
        # Update the GUI Logic ()
        self.updGui()

        

    def updGui(self):
        """
        Used to Update the GUI's logic and display

        Partly aesthetic, critical controls start hidden and are revealed depending on the plot type
        If almost any GUI Button is CLicked or GUI Element Updated, it should point here to update the logic
        """
        # This whole section edits the gui to display the currently selected indexing method (direct index or time-based)
        self.TimeSelectionBox.setEnabled(self.TimeIndexButton.isChecked())                 
        self.IndexSelectionBox.setEnabled(self.IndexIndexButton.isChecked())

        # Modify the gui to display sweep or sensor/constant stuff
        if self.PlotTypeCombo.currentText() == ("Constant" or "Sensor"):
            # Set the time controls to A->B and not point
            self.TimeMonoBox.setVisible(False)
            self.TimeStartStopBox.setVisible(True)

            # Sets Amp Control to not visible (Or Visible)
            self.SweepSettingsBox.setVisible(False)
        else:
            # Same as above but inverse
            self.TimeMonoBox.setVisible(True)
            self.TimeStartStopBox.setVisible(False)
            
            self.SweepSettingsBox.setVisible(True)

        
        # Populate GUI With Relevant Data Information
        self.IndexSelectionCombo.clear()
        if self.PlotTypeCombo.currentText() == "Medium Sweep":
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_medium])
        elif self.PlotTypeCombo.currentText() == "Burst Sweep":
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_burst])
        elif self.PlotTypeCombo.currentText() == "Large Sweep":
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_large])
        elif self.PlotTypeCombo.currentText() == "Sensor":
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_sensor])
        elif self.PlotTypeCombo.currentText() == "Constant":
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_sensor])

    # Main Plotting Function
    def SendPlot(self):
        """
        Master plotting function, manages and calls all other plot functions
        """
        # print("SendPlot Received")

        # Clear Current Plot
        self.PlotDisplay.plotItem.clear()

        # Does one of three things: 
        # 1) Creates a dict of the "start" or "stop" times for a constant/sensor plot                 
        # 2) Finds the closest sweep index for the provided time                      
        # 3) Grabs the user-selected index from the IndexSelectionCombo ComboBox
        # 
        # This information is then used to inform the relevent plotting function on what to display
        if self.TimeIndexButton.isChecked() and (self.PlotTypeCombo.currentText() == ("Constant" or "Sensor")):
            indexNum = {"start": self.find_closest(self.StartTime.text()), "stop": self.find_closest(self.EndTime.text())}
        elif self.TimeIndexButton.isChecked():
            indexNum = self.find_closest(self.TimeMono.text())
        else:
            indexNum = int(self.IndexSelectionCombo.currentText())

        # Plot the appropriate sweep
        if self.PlotTypeCombo.currentText() == ("Constant" or "Sensor"):
            self.Plot_const(indexNum)
        else:
            self.Plot_sweep(indexNum)
            

    # Loads and indexes the data
    def Load_data(self):
        self.packets = np.array(UDIP_Lib.readFile(self.filename))

        # Indexes all packets
        for i, p in enumerate(self.packets):
            if(p.pcktType == 0x01):           # Sensor Packet Type
                self.ind_sensor.append(i)
            elif(p.pcktType == 0x10):         # Medium Sweep Packet Type
                self.ind_medium.append(i)
            elif(p.pcktType ==  0x11):        # Large Sweep Packet Type
                self.ind_large.append(i)
            elif(p.pcktType == 0x20):         # Burst Sweep Packet Type
                self.ind_burst.append(i)
            elif(p.pcktType == 0x30):         # Constant Sweep Packet Type
                self.ind_constant.append(i)
  
    # ---Functions used to parse the packets and display the data---

    # finds the packet that is closest to the selected time
    def find_closest(self, time):
        #returns index in array that is closest to the user provided time
        



        n = len(array)
        if (time < self.packets[array[0]].tInitial):
            return 0
        elif (time > self.packets[array[-1]].tInitial):
            return n-1
        else:
            b = self.packets[array[0]].tInitial
            a = self.packets[array[0]].tInitial
            i = 1
            while (a < time):
                b = a
                a = self.packets[array[i + 1]].tInitial
                i = i + 1
            if (time - b < a - time):
                return i - 1
            else:
                return i

    def Plot_sweep(self, indexNum):    
        # Using the chosen packet number, we plot the corresponding sweep
        Selection = self.packets[indexNum]

        # Define the plotted variables
        x = Selection.sweep.sweepVoltage

        # The current was amplified three times, user can choose amp level to display (or multiple)
        if self.SweepAmp0.isChecked():
            y0 = Selection.sweep.adc0Curr
            self.PlotDisplay.plot(x,y0,pen="g", name="Amp 0")
        if self.SweepAmp1.isChecked():
            y1 = Selection.sweep.adc1Curr
            self.PlotDisplay.plot(x,y1,pen="b", name="Amp 1")
        if self.SweepAmp2.isChecked():
            y2 = Selection.sweep.adc2Curr
            self.PlotDisplay.plot(x,y2,pen="r", name="Amp 2")

    def Plot_const(self, indexNum):
        # Using the chosen packet number, we plot the corresponding sweep
        SelectionStart = self.packets[indexNum[0]]
        SelectionEnd = self.packets[indexNum[1]]

        # Define the plotted variables
        x = Selection.sweep.sweepVoltage

        # The current was amplified three times, user can choose amp level to display (or multiple)
        if self.SweepAmp0.isChecked():
            y0 = Selection.sweep.adc0Curr
            self.PlotDisplay.plot(x,y0,pen="g", name="Amp 0")
        if self.SweepAmp1.isChecked():
            y1 = Selection.sweep.adc1Curr
            self.PlotDisplay.plot(x,y1,pen="b", name="Amp 1")
        if self.SweepAmp2.isChecked():
            y2 = Selection.sweep.adc2Curr
            self.PlotDisplay.plot(x,y2,pen="r", name="Amp 2")




            




# Main        
import sys

# Create GUI application
app = QtWidgets.QApplication(sys.argv)

# Order:
# 1) Get the default QT main window   2) Initialize the gui (Main_Window) defined in this file   3) run the setupui function   4) actually display the window
MainWindow = QtWidgets.QMainWindow()
gui = MasterWindow()
gui.setupui(MainWindow)
MainWindow.show()

app.exec_()