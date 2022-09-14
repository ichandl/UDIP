'''
Main GUI Window 
All GUI setup and computation is done here

If you are planning on reading this code, you better buckle up
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

        # List of dictionaries used to do some things
        self.data_sensor = []
        self.data_constant = []
        self.sweep_time = []
 
        # Load the UDIP Data
        print("Loading Data")

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
        self.TimeMono.editingFinished.connect(lambda: self.SendPlot())
        self.StartTime.editingFinished.connect(lambda: self.SendPlot())
        self.EndTime.editingFinished.connect(lambda: self.SendPlot())

        # If a GUI Button is Updated, refresh the display
        self.TimeIndexButton.toggled.connect(lambda: self.updGui())
        self.IndexIndexButton.toggled.connect(lambda: self.updGui())
        
        # Update the GUI Logic ()
        self.IndexSelectionCombo.addItems([str(x) for x in self.ind_medium])
        self.IndexSelectionCombo.currentIndexChanged.connect(lambda: self.SendPlot())
        self.updGui()

    # We do some logic updating
    def updGui(self):
        """
        Used to Update the GUI's logic and display

        This whole function is retarded ... for now
        """
        # This whole section edits the gui to display the currently selected indexing method (direct index or time-based)
        self.SweepTimeBox.setEnabled(self.TimeIndexButton.isChecked())                 
        self.IndexSelectionBox.setEnabled(self.IndexIndexButton.isChecked())

    # Main Plotting Function
    def SendPlot(self):
        """
        Master plotting function, prepares and calls the appropriate plot functions
        """
        try:
            # He will never be debugging
            # print("SendPlot Received")

            # Clear Current Plot
            self.PlotDisplay.plotItem.clear()

            # Plot the appropriate sweep
            if self.ControlTabs.currentIndex() == 1:
                indexNums = [self.find_closest("Sweep",self.StartTime.value()),self.find_closest("Sweep",self.EndTime.value())]
                # Plot Constant
                self.Plot_const()
            else:
                # Plot Sweep
                # Find The Corrext Index
                if self.TimeIndexButton.isChecked():
                    indexNum = self.find_closest("Sweep",self.TimeMono.value())
                else:
                    indexNum = int(self.IndexSelectionCombo.currentText())
                
                self.Plot_sweep(indexNum)
        except:
            pass

    # Loads and indexes the data
    def Load_data(self):
        # This is the only thing I use the UDIP_Lib for, don't want to move all of that stuff over
        self.packets = np.array(UDIP_Lib.readFile(self.filename))

        # Catalogs all packets i is index, p is the packet
        for i, p in enumerate(self.packets):
            if(p.pcktType == 0x01):           # Sensor Packet Type
                # Add the sensor info into a list of dictionary
                self.data_sensor.append({"time": p.tInitial,"index": i,"accY": p.accX,"accY": p.accY,"accZ": p.accZ,"accH": p.accH,"gyroX": p.gyroX, "gyroY": p.gyroY, "gyroZ": p.gyroZ,"magX": p.magX,"magY": p.magY,"magZ": p.magZ,"tmpD": p.temperature_d,"tmpP": p.temperature_p,"tmpS": p.temperature_s})
                # This isn't used anywhere ... yet
                self.ind_sensor.append(i)
            elif(p.pcktType == 0x10):         # Medium Sweep Packet Type
                # Add to time dictionary
                self.sweep_time.append({"time": p.tInitial, "index": i})
                # Add to list of index
                self.ind_medium.append(i)
            elif(p.pcktType == 0x30):         # Constant Sweep Packet Type
                self.ind_constant.append(i)
            # These Two Arent Used
            elif(p.pcktType ==  0x11):        # Large Sweep Packet Type
                self.ind_large.append(i)
            elif(p.pcktType == 0x20):         # Burst Sweep Packet Type
                self.ind_burst.append(i)
            else:
                print("How?")
            
    # finds the packet that is closest to the selected time(s)
    def find_closest(self, type: str, time: float):
        #returns index in array that is closest to the user provided time
        # Really jank could be improved
        try:
            if type == "Sweep":
                # Goes through the list of times
                for i in self.sweep_time:
                    # once the time of the current selection is bigger than the requested time, return the previous one
                    if i["time"] > time*1000:
                        return i["index"]
            # Does the same thing as sweep but from the sensor one
            elif type == "Sensor":
                # Goes through the list of times
                for i in self.data_sensor:
                    # once the time of the current selection is bigger than the requested time, return the previous one
                    if i["time"] > time*1000:
                        return i["index"]
            # Does the same thing as sweep but from the constant one; not implimented yet
            # if type == "Constant":
            #     # Goes through the list of times
            #     for i in self.data_sensor:
            #         # once the time of the current selection is bigger than the requested time, return the previous one
            #         if i["time"] > time:
            #             return self.sweep_time[i]["index"]

            # if the provided time is larger than any possible time, return the final index
            return i["index"]
        except:
            pass

    def Plot_sweep(self, indexNum):    
        # Using the chosen packet number, we plot the corresponding sweep
        Selection = self.packets[indexNum]

        # Define the plotted variables
        print(Selection.sweep.sweepVoltage)
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

    def Plot_const(self, indexNums):
        # Using the chosen packet number, we plot the corresponding sweep
        SelectionStart = self.packets[indexNums[0]]
        SelectionEnd = self.packets[indexNums[1]]

        # This plot is always over time, so x is the range between the start and stop
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




            




# -- Main --       
import sys
# GUI Setup Process via PyQt5
# 0) Start a PyQt app, required to do anything else
app = QtWidgets.QApplication(sys.argv)
# 1) Get the default QT main window
MainWindow = QtWidgets.QMainWindow()
# 2) Initialize the gui (The class that is defined in this file) (Also runs the init function)
gui = MasterWindow()
# 3) Run the setupui function, described there
gui.setupui(MainWindow)
# 4) Actually display the window
MainWindow.show()
# 5) No Idea
app.exec_()