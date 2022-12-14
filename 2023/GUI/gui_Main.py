'''
Main GUI Window 
All GUI setup and computation is done here

If you are planning on reading this code, you better buckle up

@TODO
Change how indexing currently works, it currently is a bunch of for loops and a bunch of misc lists 
Sensor Units :'(
Synthesis

References:
pyqtgraph/examples/MultiplePlotAxes.py
pyqtgraph/examples/MultiPlotWidget.py
'''
# Import
# Custom Imports
from gui_layout import Ui_UDIP_Viewer

# GUI and Threading stuff (Threading was a now-crushed dream)
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
        self.sensor_time = []
        self.constant_time = []
        self.sweep_time = []

        # Number of plots that are currently displayed in the PlotLayoutWidget
        self.NumPlots = 0

        # List of colors used for plotting. feel free to change
        self.color_cycle = [[227,26,28], [51,160,44], [31,120,180], [106,61,154], [166,206,227], [178,223,138], [251,154,153], [253,191,111], [255,127,0], [202,178,214], [255,255,153], [177,89,40]]

        # Load Data
        self.Load_data()

        # Logging
        print("Initialized")

    def setupui(self, MainWindow: QtWidgets.QMainWindow):
        """"
        Sets up the gui and adds functionality to the buttons and such
        """
        # Import Layout from Designer
        super().setupUi(MainWindow)

        # Init the plotting window
        self.Add_Plot()

        # Add functionality to GUI Buttons
        self.PlotButton.clicked.connect(lambda: self.SendPlot())        # Plot Button Pushes Selection To Plot
        self.NextButton.clicked.connect(lambda: self.IndexSelectionCombo.setCurrentIndex(self.IndexSelectionCombo.currentIndex() + 1))
        self.PreviousButton.clicked.connect(lambda: self.IndexSelectionCombo.setCurrentIndex(self.IndexSelectionCombo.currentIndex() - 1))
        self.NextButton.clicked.connect(lambda: self.SendPlot())
        self.PreviousButton.clicked.connect(lambda: self.SendPlot())
        self.TimeMono.editingFinished.connect(lambda: self.SendPlot())
        self.StartTime.editingFinished.connect(lambda: self.SendPlot())
        self.EndTime.editingFinished.connect(lambda: self.SendPlot())
        self.AddPlotButton.clicked.connect(lambda: self.Add_Plot())
        self.RemovePlotButton.clicked.connect(lambda: self.Remove_Plot())

        # If a GUI Element is Updated, refresh the display
        self.TimeIndexButton.toggled.connect(lambda: self.updGui())
        self.IndexIndexButton.toggled.connect(lambda: self.updGui())
        self.SweepTypeCombo.currentIndexChanged.connect(lambda: self.updGui())
        self.PlotSelectionCombo.currentIndexChanged.connect(lambda: self.updGui())
        
        # Update the GUI Logic ()
        # self.IndexSelectionCombo.currentIndexChanged.connect(lambda: self.SendPlot())
        self.updGui()

    # We do some logic updating
    def updGui(self):
        """
        Used to Update the GUI's logic and display
        """
        # Radio Button Logic
        self.SweepTimeBox.setEnabled(self.TimeIndexButton.isChecked())                 
        self.IndexSelectionBox.setEnabled(self.IndexIndexButton.isChecked())

        # Sweep Type Logic: Constant vs Dynamic
        i = self.IndexSelectionCombo.currentIndex()
        self.IndexSelectionCombo.clear()
        self.IndexSelectionCombo.setCurrentText("")
        if self.SweepTypeCombo.currentIndex() == 0:
            self.ConstantSelectionBox.setVisible(False)
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_medium])
        elif self.SweepTypeCombo.currentIndex() == 1:
            self.ConstantSelectionBox.setVisible(True)
            self.IndexSelectionCombo.addItems([str(x) for x in self.ind_constant])
        self.IndexSelectionCombo.setCurrentIndex(i)

        # Plot type logic: Sweep vs Sensor
        if self.ControlTabs.currentIndex == 1:
            self.SensorDataBox.setVisible(True)
        elif self.ControlTabs.currentIndex == 0:
            self.SensorDataBox.setVisible(True)

        # Set the currently selected plot
        self.SelectedPlot = self.PlotSelectionCombo.currentData()

    # Main Plotting Function
    def SendPlot(self):
        """
        Master plotting function, prepares and calls the appropriate plot functions
        """
        # try:
        if True:
            # He will never be debugging
            # print("SendPlot Received")

            # Clear Current Plot
            self.SelectedPlot.clear()

            # Due to pyqtgraph things some of the labeling needs to be added at different stages of plotting
            # The first part is here, but most is done after plotting
            self.SelectedPlot.addLegend()

            # Plot the appropriate sweep
            if self.ControlTabs.currentIndex() == 1:
                indexNums = [self.find_closest("Sensor",self.StartTime.value()),self.find_closest("Sensor",self.EndTime.value())]
                # Plot Constant
                self.Plot_Sensor(indexNums)
            elif self.SweepTypeCombo.currentIndex() == 1:
                # Find The Correct Index
                if self.TimeIndexButton.isChecked():
                    indexNum = self.find_closest("Constant",self.TimeMono.value())
                else:
                    indexNum = int(self.IndexSelectionCombo.currentText())
                # Plot Sweep
                self.Plot_Constant(indexNum)
            else:
                # Find The Corrext Index
                if self.TimeIndexButton.isChecked():
                    indexNum = self.find_closest("Sweep",self.TimeMono.value())
                else:
                    indexNum = int(self.IndexSelectionCombo.currentText())
                # Plot Sweep
                self.Plot_sweep(indexNum)
        # except:
        #     pass

    # Loads and indexes the data
    def Load_data(self):
        # Pull the data from UDIP_Lib
        # Load the UDIP Data
        print("Loading Data")
        self.packets = np.array(UDIP_Lib.readFile(self.filename))

        # Catalogs all packets i is index, p is the packet
        print("Indexing Packets")
        for i, p in enumerate(self.packets):
            if(p.pcktType == 0x01):           # Sensor Packet Type
                # Add the sensor info into a list of dictionary
                self.sensor_time.append({"time": p.tInitial,"index": i})
                # This isn't used anywhere ... yet
                self.ind_sensor.append(i)
            elif(p.pcktType == 0x10):         # Medium Sweep Packet Type
                # Add to time dictionary
                self.sweep_time.append({"time": p.tInitial, "index": i})
                # Add to list of index
                self.ind_medium.append(i)
            elif(p.pcktType == 0x30):         # Constant Sweep Packet Type
                self.constant_time.append({"time": p.tInitial, "index": i})
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
        i = {"index": 0}
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
                for i in self.sensor_time:
                    # once the time of the current selection is bigger than the requested time, return the previous one
                    if i["time"] > time*1000:
                        return i["index"]
            # Does the same thing as sweep but from the constant one; not implimented yet
            if type == "Constant":
                # Goes through the list of times
                for i in self.data_sensor:
                    # once the time of the current selection is bigger than the requested time, return the previous one
                    if i["time"] > time:
                        return self.constant_time[i]["index"]

            # if the provided time is larger than any possible time, return the final index
            return i["index"]
        except:
            pass

    def Plot_sweep(self, indexNum):    
        # Using the chosen packet number, we plot the corresponding sweep
        Selection = self.packets[indexNum]

        # Update GUI Logic and display relevant sensor data
        self.TimeMono.setValue(Selection.tInitial/1000)
        for i, p in enumerate(self.sweep_time):
            if p["index"] == indexNum:
                self.IndexSelectionCombo.setCurrentIndex(i)
                break

        # Index for Color Cycle
        colorNum = 0
        
        self.IndexSelectionCombo.setCurrentIndex(self.ind_medium.index(indexNum))

        # There are two sensor packets retrieved here, but the desision was made to use only the inital one at it matches the final 99% of the time
        SensInit = self.packets[self.find_closest("Sensor", Selection.tInitial/1000)]
        # SensFinal = self.packets[self.find_closest("Sensor", Selection.tFinal/1000)]

        # Sensor Things
        self.SensorInitialTable.item(0,0).setText(str(round(SensInit.accX,3)))
        self.SensorInitialTable.item(1,0).setText(str(round(SensInit.accY,3)))
        self.SensorInitialTable.item(2,0).setText(str(round(SensInit.accZ,3)))
        self.SensorInitialTable.item(3,0).setText(str(round(SensInit.accH,3)))
        self.SensorInitialTable.item(4,0).setText(str(round(SensInit.gyroX,3)))
        self.SensorInitialTable.item(5,0).setText(str(round(SensInit.gyroY,3)))
        self.SensorInitialTable.item(6,0).setText(str(round(SensInit.gyroZ,3)))
        self.SensorInitialTable.item(7,0).setText(str(round(SensInit.magX,3)))
        self.SensorInitialTable.item(8,0).setText(str(round(SensInit.magY,3)))
        self.SensorInitialTable.item(9,0).setText(str(round(SensInit.magZ,3)))
        self.SensorInitialTable.item(10,0).setText(str(round(SensInit.temperature_d,3)))
        self.SensorInitialTable.item(11,0).setText(str(round(SensInit.temperature_p,3)))
        self.SensorInitialTable.item(12,0).setText(str(round(SensInit.temperature_s,3)))
        self.SensorInitialTable.item(13,0).setText(str(round(SensInit.pd_1,3)))
        self.SensorInitialTable.item(14,0).setText(str(round(SensInit.pd_2,3)))


        # self.SensorFinalTable.item(0,0).setText(str(round(SensFinal.accX,3)))
        # self.SensorFinalTable.item(1,0).setText(str(round(SensFinal.accY,3)))
        # self.SensorFinalTable.item(2,0).setText(str(round(SensFinal.accZ,3)))
        # self.SensorFinalTable.item(3,0).setText(str(round(SensFinal.accH,3)))
        # self.SensorFinalTable.item(4,0).setText(str(round(SensFinal.gyroX,3)))
        # self.SensorFinalTable.item(5,0).setText(str(round(SensFinal.gyroY,3)))
        # self.SensorFinalTable.item(6,0).setText(str(round(SensFinal.gyroZ,3)))
        # self.SensorFinalTable.item(7,0).setText(str(round(SensFinal.magX,3)))
        # self.SensorFinalTable.item(8,0).setText(str(round(SensFinal.magY,3)))
        # self.SensorFinalTable.item(9,0).setText(str(round(SensFinal.magZ,3)))
        # self.SensorFinalTable.item(10,0).setText(str(round(SensFinal.temperature_d,3)))
        # self.SensorFinalTable.item(11,0).setText(str(round(SensFinal.temperature_p,3)))
        # self.SensorFinalTable.item(12,0).setText(str(round(SensFinal.temperature_s,3)))
        # self.SensorFinalTable.item(13,0).setText(str(round(SensFinal.pd_1,3)))
        # self.SensorFinalTable.item(14,0).setText(str(round(SensFinal.pd_2,3)))

        # X is voltage always
        x = Selection.sweep.sweepVoltage

        # The current was amplified three times, user can choose amp level to display (or multiple)
        if self.SweepAmp0.isChecked():
            if self.RemoveHystCheck.isChecked():
                x0, y0 = self.remove_hyst(x, Selection.sweep.adc0Curr)
            else:
                x0 = x
                y0 = Selection.sweep.adc0Curr
            
            self.SelectedPlot.plot(x0,y0,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 0")
            colorNum += 1

            if self.PlotFitCheck.isChecked():
                t, m ,popt,pcov = self.fit_sweep(x0,y0)
                self.SelectedPlot.plot(t,m,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 0 Fit")
                colorNum += 1

        if self.SweepAmp1.isChecked():
            if self.RemoveHystCheck.isChecked():
                x1, y1 = self.remove_hyst(x, Selection.sweep.adc1Curr)
            else:
                x1 = x
                y1 = Selection.sweep.adc1Curr
            
            self.SelectedPlot.plot(x1,y1,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 1")
            colorNum += 1

            if self.PlotFitCheck.isChecked():
                t, m ,popt,pcov = self.fit_sweep(x1,y1)
                self.SelectedPlot.plot(t,m,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 1 Fit")
                colorNum += 1

        if self.SweepAmp2.isChecked():
            if self.RemoveHystCheck.isChecked():
                x2, y2 = self.remove_hyst(x, Selection.sweep.adc2Curr)
            else:
                x2 = x
                y2 = Selection.sweep.adc2Curr

            self.SelectedPlot.plot(x2,y2,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 2")
            colorNum += 1

            if self.PlotFitCheck.isChecked():
                t, m ,popt,pcov = self.fit_sweep(x2,y2)
                self.SelectedPlot.plot(t,m,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 2 Fit")
                colorNum += 1

        # We do some Labeling
        self.SelectedPlot.setTitle(title=f"Sweep {indexNum} at {round(Selection.tInitial/1000,2)} seconds")
        self.SelectedPlot.setLabel("bottom",text="Voltage",units="V")
        self.SelectedPlot.setLabel("left",text="Current",units="I")

    def Plot_Constant(self, indexNum):
        # Using the chosen packet number, we plot the corresponding sweep
        Selection = self.packets[indexNum]

        # Update GUI Logic and display relevant sensor data
        self.TimeMono.setValue(Selection.tInitial/1000)
        for i, p in enumerate(self.constant_time):
            if p["index"] == indexNum:
                self.IndexSelectionCombo.setCurrentIndex(i)
                break

        self.IndexSelectionCombo.setCurrentIndex(self.ind_constant.index(indexNum))
        
        SensInit = self.packets[self.find_closest("Sensor", Selection.tInitial/1000)]
        SensFinal = self.packets[self.find_closest("Sensor", Selection.tFinal/1000)]

        self.SensorInitialTable.item(0,0).setText(str(round(SensInit.accX,3)))
        self.SensorInitialTable.item(1,0).setText(str(round(SensInit.accY,3)))
        self.SensorInitialTable.item(2,0).setText(str(round(SensInit.accZ,3)))
        self.SensorInitialTable.item(3,0).setText(str(round(SensInit.accH,3)))
        self.SensorInitialTable.item(4,0).setText(str(round(SensInit.gyroX,3)))
        self.SensorInitialTable.item(5,0).setText(str(round(SensInit.gyroY,3)))
        self.SensorInitialTable.item(6,0).setText(str(round(SensInit.gyroZ,3)))
        self.SensorInitialTable.item(7,0).setText(str(round(SensInit.magX,3)))
        self.SensorInitialTable.item(8,0).setText(str(round(SensInit.magY,3)))
        self.SensorInitialTable.item(9,0).setText(str(round(SensInit.magZ,3)))
        self.SensorInitialTable.item(10,0).setText(str(round(SensInit.temperature_d,3)))
        self.SensorInitialTable.item(11,0).setText(str(round(SensInit.temperature_p,3)))
        self.SensorInitialTable.item(12,0).setText(str(round(SensInit.temperature_s,3)))
        self.SensorInitialTable.item(13,0).setText(str(round(SensInit.pd_1,3)))
        self.SensorInitialTable.item(14,0).setText(str(round(SensInit.pd_2,3)))

        self.SensorFinalTable.item(0,0).setText(str(round(SensFinal.accX,3)))
        self.SensorFinalTable.item(1,0).setText(str(round(SensFinal.accY,3)))
        self.SensorFinalTable.item(2,0).setText(str(round(SensFinal.accZ,3)))
        self.SensorFinalTable.item(3,0).setText(str(round(SensFinal.accH,3)))
        self.SensorFinalTable.item(4,0).setText(str(round(SensFinal.gyroX,3)))
        self.SensorFinalTable.item(5,0).setText(str(round(SensFinal.gyroY,3)))
        self.SensorFinalTable.item(6,0).setText(str(round(SensFinal.gyroZ,3)))
        self.SensorFinalTable.item(7,0).setText(str(round(SensFinal.magX,3)))
        self.SensorFinalTable.item(8,0).setText(str(round(SensFinal.magY,3)))
        self.SensorFinalTable.item(9,0).setText(str(round(SensFinal.magZ,3)))
        self.SensorFinalTable.item(10,0).setText(str(round(SensFinal.temperature_d,3)))
        self.SensorFinalTable.item(11,0).setText(str(round(SensFinal.temperature_p,3)))
        self.SensorFinalTable.item(12,0).setText(str(round(SensFinal.temperature_s,3)))
        self.SensorFinalTable.item(13,0).setText(str(round(SensFinal.pd_1,3)))
        self.SensorFinalTable.item(14,0).setText(str(round(SensFinal.pd_2,3)))

        # X is the number of computer clock steps (100)
        x = np.arange(0, Selection.nSteps, 1)
        
        # Color Cycle Num
        colorNum = 0

        # Plot what the user requests
        if self.PD1ConstCheck.isChecked():
            yPD1 = Selection.sweep.adcPD1Volt
            self.SelectedPlot.plot(x,yPD1,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="PD1")
            colorNum += 1
        if self.PD2ConstCheck.isChecked():
            yPD2 = Selection.sweep.adcPD2Volt
            self.SelectedPlot.plot(x,yPD2,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="PD2")
            colorNum += 1
        if self.SweepAmp0.isChecked():
            y0 = Selection.sweep.adc0Curr
            self.SelectedPlot.plot(x,y0,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 0")
            colorNum += 1
        if self.SweepAmp1.isChecked():
            y1 = Selection.sweep.adc1Curr
            self.SelectedPlot.plot(x,y1,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 1")
            colorNum += 1
        if self.SweepAmp2.isChecked():
            y2 = Selection.sweep.adc2Curr
            self.SelectedPlot.plot(x,y2,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Amp 2")
            colorNum += 1

        # Labeling
        self.SelectedPlot.setTitle(title=f"Sweep {indexNum} at {round(Selection.tInitial/1000,2)} seconds")
        self.SelectedPlot.setLabel("bottom",text="?")
        self.SelectedPlot.setLabel("left",text="?")
        
    def Plot_Sensor(self, indexNums):
        # Plotting lists that are sent to pyqtgraph
        timeSens = []       # Time will always be the x value (I think)

        accXList = []
        accYList = []
        accZList = []
        accHList = []
        gyrXList = []
        gyrYList = []
        gyrZList = []
        magXList = []
        magYList = []
        magZList = []
        tmpDList = []
        tmpPList = []
        tmpSList = []
        pd1List = []
        pd2List = []

        # i value used for cycling through the color_cycle
        colorNum = 0
        
        # This plot works by gathering all sensor packets within the provided the time, and seperating all of the information
        for i in self.ind_sensor:
            # Kill the loop after the desired time
            if i > indexNums[1]:
                break
            # If the index is between the start and stop
            if (i >= indexNums[0]) and (i <= indexNums[1]):
                # Pull the packet
                packet = self.packets[i]

                # Pull the time; change it from ms to s
                timeSens.append(packet.tInitial/1000)

                # Puts data into respective list
                accXList.append(packet.accX)
                accYList.append(packet.accY)
                accZList.append(packet.accZ)
                accHList.append(packet.accH)
                gyrXList.append(packet.gyroX)
                gyrYList.append(packet.gyroY)
                gyrZList.append(packet.gyroZ)
                magXList.append(packet.magX)
                magYList.append(packet.magY)
                magZList.append(packet.magZ)
                tmpDList.append(packet.temperature_d)
                tmpPList.append(packet.temperature_p)
                tmpSList.append(packet.temperature_s)
                pd1List.append(packet.pd_1)
                pd2List.append(packet.pd_2)
        

        # Plot Based on User Selection
        if self.XAccelCheck.isChecked():
            self.SelectedPlot.plot(timeSens, accXList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Accel X")
            colorNum += 1
        if self.YAccelCheck.isChecked():
            self.SelectedPlot.plot(timeSens, accYList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Accel Y")
            colorNum += 1
        if self.ZAccelCheck.isChecked():
            self.SelectedPlot.plot(timeSens, accZList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Accel Z")
            colorNum += 1
        if self.ZAnaAccelCheck.isChecked():
            self.SelectedPlot.plot(timeSens, accHList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Accel H")
            colorNum += 1
        
        if self.XGyroCheck.isChecked():
            self.SelectedPlot.plot(timeSens, gyrXList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Gyro X")
            colorNum += 1
        if self.YGyroCheck.isChecked():
            self.SelectedPlot.plot(timeSens, gyrYList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Gyro Y")
            colorNum += 1
        if self.ZGyroCheck.isChecked():
            self.SelectedPlot.plot(timeSens, gyrZList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Gyro Z")
            colorNum += 1
        
        if self.XMagCheck.isChecked():
            self.SelectedPlot.plot(timeSens, magXList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Mag X")
            colorNum += 1
        if self.YMagCheck.isChecked():
            self.SelectedPlot.plot(timeSens, magYList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Mag Y")
            colorNum += 1
        if self.ZMagCheck.isChecked():
            self.SelectedPlot.plot(timeSens, magZList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Mag Z")
            colorNum += 1

        if self.DTempCheck.isChecked():
            self.SelectedPlot.plot(timeSens, tmpDList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Temp D")
            colorNum += 1
        if self.PTempCheck.isChecked():
            self.SelectedPlot.plot(timeSens, tmpPList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Temp P")
            colorNum += 1
        if self.STempCheck.isChecked():
            self.SelectedPlot.plot(timeSens, tmpSList,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="Temp S")
            colorNum += 1
        
        if self.PD1Check.isChecked():
            self.SelectedPlot.plot(timeSens, pd1List,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="PD1")
            colorNum += 1
        if self.PD2Check.isChecked():
            self.SelectedPlot.plot(timeSens, pd2List,pen=pyqtgraph.mkColor(self.color_cycle[colorNum]), name="PD2")
            colorNum += 1

    def fit_sweep(self, x, y):
        # Function that is given a sweep x and y and fits it to a langmuir thing
        def model(x,xa,b,m1,n,t,V0):
            #electron retardation
            ret = np.zeros(len(x))
            ret[x <= xa] = seg1(x[x <= xa],m1) - seg1(xa, m1) + b
            ret[x > xa] = seg2(x[x > xa],n,t,V0) - seg2(xa,n,t,V0) + seg1(xa,m1) - seg1(xa, m1) + b
            return ret
            
        def seg1(x,m):#linear--full model square root
            return m * x

        def seg2(x,n,t,V0):# square root
            q_e = 1.602 * 10**-19 #C                charge of an electron
            K_b = 1.381 * 10**-23 #m^2*kg/(s^2*K)   boltzman constant
            m_e = 9.109 * 10**-31 #kg               mass of an electron
            R = (3./16.) * 0.0254 #radius of probe
            L = (3.25) * 0.0254 #length of probe
            A = 2. * np.pi * R * L + np.pi * (R ** 2) #area of probe cylinder with out a bottom
            
            k = q_e / (K_b * t)
            I0 =n * q_e * np.sqrt(K_b * t / (2. * np.pi * m_e)) * A / (10**-9)
            return I0 * np.sqrt(1 + k*(x + V0))

        def get_fit(x,y):
            g = [0.6,-14,80, 5*(10**10),1000,-0.5]    #intial guess
            b = ((-3,-np.inf,-np.inf,0,0,-3),(3,np.inf,np.inf,np.inf,10000,3)) #bounds
            popt, pcov = optimize.curve_fit(model,x,y,g,bounds=b)
            #print(popt)
            max_1 = max(x)
            min_1 = min(x)
            t = np.linspace(min_1,max_1,num=60)
            return t, model(t,*popt),popt,pcov #popt[0:xa,1:b,2:m1,3:n,4:t,5:V0]

        return get_fit(x,y)
        
    def remove_hyst(self, x1,y1):
        # +6v range: 1 -> 131
        # 0v = 0, 132,264
        # -6v range: 133 -> 263

        x2 = []
        y2 = []

        # +6v side
        a = range(1,132)
        b = np.flip(a)
        i = 0
        while i < len(a) - 1:
            x2.append((x1[a[i]] + x1[b[i]])/2)
            y2.append((y1[a[i]] + y1[b[i]])/2)

            i += 1

        # -6v side
        a = range(133, 264)
        b = np.flip(a)
        i = 0
        while i < len(a) - 1:
            x2.append((x1[a[i]] + x1[b[i]])/2)
            y2.append((y1[a[i]] + y1[b[i]])/2)

            i += 1

        return x2, y2

    # -- Helper Functions -- (Mainly for Gui logic)
    # Add a plot to the display
    def Add_Plot(self):
        self.NumPlots += 1
        self.PlotSelectionCombo.addItem(f"{self.NumPlots}", self.GraphicsLayout.addPlot())
        self.PlotSelectionCombo.setCurrentIndex(self.PlotSelectionCombo.count() - 1)
    
    # Remove a plot from the display
    def Remove_Plot(self):
        self.GraphicsLayout.removeItem(self.PlotSelectionCombo.currentData())
        self.PlotSelectionCombo.removeItem(self.PlotSelectionCombo.currentIndex())
        self.PlotSelectionCombo.setCurrentIndex(self.PlotSelectionCombo.count() - 1)
        
        
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