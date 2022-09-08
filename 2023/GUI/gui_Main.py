'''
Main GUI Window all setup is done here, computation is done via (no idea)
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

        self.packets = []
        self.ind_sensor = []
        self.ind_medium = []
        self.ind_large = []
        self.ind_burst = []
        self.ind_constant = []

    def setupui(self, MainWindow: QtWidgets.QMainWindow):
        """"
        Sets up the gui and adds functionality to the buttons and such
        """
        # Import Layout from Designer
        super().setupUi(MainWindow)

        # Load the UDIP Data
        self.Load_data()

        # Add functionality to GUI Buttons
        self.PlotButton.clicked.connect(lambda: self.SendPlot())

        # ---Update the GUI Logic---
        # This whole section edits the gui to display the currently selected indexing method (direct index or time-based)
        self.TimeSelectionBox.setVisible(self.TimeIndexButton.isChecked())                 
        self.IndexSelectionBox.setVisible(self.IndexIndexButton.isChecked())
        self.TimeIndexButton.toggled.connect(lambda: self.TimeSelectionBox.setVisible(self.TimeIndexButton.isChecked()))
        self.IndexIndexButton.toggled.connect(lambda: self.IndexSelectionBox.setVisible(self.IndexIndexButton.isChecked()))

        # Defines the radio-button exclusivity
        self.TimeIndexButton.clicked.connect(lambda: self.IndexIndexButton.setChecked(self.TimeIndexButton.toggled()))


        
    # GUI Functions that perfoms plotting and other stuff
    def SendPlot(self):
        """
        Master plotting function, manages and calls all other plot functions
        """
        print("SendPlot Received")

        # Clear Current Plot
        self.PlotDisplay.plotItem.clear()

        # Grab the correct index to plot

        # Plot the appropriate sweep
        if self.BurstSweepButton.isChecked():
            
            self.Plot_sweep(index=int(self.SweepNumber.value()))
        elif self.MediumSweepButton.isChecked():
            
            self.Plot_sweep(index=int(self.SweepNumber.value()))
        elif self.LargeSweepButton.isChecked():
            
            self.Plot_sweep(index=int(self.SweepNumber.value()))
        elif self.SensorSweepButton.isChecked():
            
            self.Plot_sweep(index=int(self.SweepNumber.value()))


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
  
    # Functions used to parse the packets and display the data

    # finds the packet that is closest to the selected time
    def find_closest(self,time,array):
        #returns index in array that is closest to the given time
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

    def Plot_sweep(self,time=None,index=None):
        print("test 1")
        if (index == None):
            ind = self.find_closest(time, self.ind_medium)
        else:
            ind = index
        
        ind = self.ind_medium[ind] #get index of medium packet
        Selection = self.packets[ind] #get the selected sweep
        
        print("test 2")
        #adc0
        x = Selection.sweep.sweepVoltage
        y = Selection.sweep.adc0Curr

        self.PlotDisplay.plot(x,y,pen=None, symbol='o')

        print("test 3")



            




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