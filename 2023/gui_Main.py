'''
Main GUI Window all setup is done here, computation is done via (no idea)
'''
# Import
# Custom Imports
from gui_layout import Ui_UDIP_Viewer
from mplwidget import MplCanvas

# GUI and Threading stuff
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *

# General Imports
import UDIP_Lib_V20 as UDIP_Lib
import matplotlib.pyplot as plt
from matplotlib import gridspec
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
        self.data = {"x": 5, "y": 4}       # Will be the plot data sent to the plotter
        self.filename = "UDIP0000.DAT"
        self.Outpath = "Deez/"

        self.UDIP_packets = []
        self.ind_sensor = []
        self.ind_medium = []
        self.ind_large = []
        self.ind_burst = []
        self.ind_constant = []

    def setupui(self, MainWindow: QtWidgets.QMainWindow):
        super().setupUi(MainWindow)

        self.Load_data()
        self.Plot_sweep(time=70)

        self.PlotButton.clicked.connect(lambda: self.SendPlot(self.data))

    
    # Functions that update the master window
    def Load_data(self):
        self.UDIP_read(self.filename)
        self.Find_Indexs()
        return

    def UDIP_read(self, filename):
        global UDIP_packets 
        UDIP_packets = np.array(UDIP_Lib.readFile(filename))

    def SendPlot(self, plot): #data: dict[list, list],
        self.PlotDisplay.canvas.ax.plot(plot)

    def Packet_test(self):
        #test to see if UDIP_packets is loaded
        if (UDIP_packets == []):
            self.Load_data()
    
    def Find_Indexs(self):
        i = 0
        #pcktType
        typeSens = 0x01
        typeMed = 0x10
        typeLrg = 0x11
        typeBrst = 0x20
        typeCst = 0x30
        
        for obj in UDIP_packets:
            if(obj.pcktType == typeSens):
                self.ind_sensor.append(i)
            elif(obj.pcktType == typeMed):
                self.ind_medium.append(i)
            elif(obj.pcktType == typeLrg):
                self.ind_large.append(i)
            elif(obj.pcktType == typeBrst):
                self.ind_burst.append(i)
            elif(obj.pcktType == typeCst):
                self.ind_constant.append(i)
            i=i+1
    def Plot_sweep(self,time=None,index=None,fit=False,hysteresis=False):
        self.Packet_test()#load data only if needed
        if (time != None) or (index != None):
            if (index == None):
                ind = self.find_closest(time, self.ind_medium)
            else:
                ind = index
            ind = self.ind_medium[ind] #get index of medium packet
            packet = UDIP_packets[ind] #get medium packet
            
            #adc0
            x0 = packet.sweep.sweepVoltage
            y0 = packet.sweep.adc0Curr
            
            #adc1
            x1 = packet.sweep.sweepVoltage
            y1 = packet.sweep.adc1Curr
            
            #adc2
            x2 = packet.sweep.sweepVoltage
            y2 = packet.sweep.adc2Curr
            
            #photo diodes
            #i_pd_1 = packet.sweep.i_pd_1
            #i_pd_2 = packet.sweep.i_pd_2
            #f_pd_1 = packet.sweep.f_pd_1
            #f_pd_2 = packet.sweep.f_pd_2
            
            fig = self.PlotDisplay.canvas.fig
            
            ax1 = fig.add_axes([0.3, 0.09, 0.6, 0.25])
            ax2 = fig.add_axes([0.3, 0.37, 0.6, 0.25])
            ax3 = fig.add_axes([0.3, 0.65, 0.6, 0.25])
            
            ax1.plot(x0, y0, 'firebrick', linewidth=1.6)#, label='Low Gain')
            if (fit):
                t, m ,popt,pcov = self.fit_sweep(x0, y0, hysteresis)
                ax1.plot(t,m,label='Model',linewidth=3)
            ax2.plot(x1,y1, 'violet', linewidth=1.6)#, label='Mid Gain')
            ax3.plot(x2,y2, 'olive', linewidth=1.6)#, label='High Gain')
            
            #ax1.legend(loc="upper left")
            #ax2.legend(loc="upper left")
            #ax3.legend(loc="upper left")
            
            ax1.set_ylabel(r'Probe Current, $I_{\rm probe}$ (nA)' '\n' r'Low Gain', fontsize=12, color='black')
            ax2.set_ylabel(r'Probe Current, $I_{\rm probe}$ (nA)' '\n' r'Mid Gain', fontsize=12, color='black')
            ax3.set_ylabel(r'Probe Current, $I_{\rm probe}$ (nA)' '\n' r'High Gain', fontsize=12, color='black')


            
            ax1.set_xlabel(r'Sweep Voltage, $V_{\rm sweep} (V)$', fontsize=12, color='black')
            
            #dashed line at x=0
            ax1.axvline(x= 0, color ="lightgray", linewidth=1.7, linestyle =":")
            ax2.axvline(x= 0, color ="lightgray", linewidth=1.7, linestyle =":")
            ax3.axvline(x= 0, color ="lightgray", linewidth=1.7, linestyle =":")
            
            #dashed line at y=0
            ax1.axhline(y= 0, color ="lightgray", linewidth=1.7, linestyle =":")
            ax2.axhline(y= 0, color ="lightgray", linewidth=1.7, linestyle =":")
            ax3.axhline(y= 0, color ="lightgray", linewidth=1.7, linestyle =":")

        
    def find_closest(self,time,array):
        #returns index in array that is closest to the given time
        n = len(array)
        if (time < UDIP_packets[array[0]].tInitial):
            return 0
        elif (time > UDIP_packets[array[-1]].tInitial):
            return n-1
        else:
            b = UDIP_packets[array[0]].tInitial
            a = UDIP_packets[array[0]].tInitial
            i = 1
            while (a < time):
                b = a
                a = UDIP_packets[array[i + 1]].tInitial
                i = i + 1
            if (time - b < a - time):
                return i - 1
            else:
                return i



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