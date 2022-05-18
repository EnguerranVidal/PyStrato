######################## IMPORTS ########################
import os
import numpy as np
import pandas as pd
import time as t
import matplotlib.pyplot as plt

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.parameters import load, save

######################## CLASSES ########################


class MessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = self.layout()
        qt_msgboxex_icon_label = self.findChild(QLabel, "qt_msgboxex_icon_label")
        qt_msgboxex_icon_label.deleteLater()
        qt_msgbox_label = self.findChild(QLabel, "qt_msgbox_label")
        qt_msgbox_label.setAlignment(Qt.AlignCenter)
        grid_layout.removeWidget(qt_msgbox_label)
        qt_msgbox_buttonbox = self.findChild(QDialogButtonBox, "qt_msgbox_buttonbox")
        grid_layout.removeWidget(qt_msgbox_buttonbox)
        grid_layout.addWidget(qt_msgbox_label, 0, 0)
        grid_layout.addWidget(qt_msgbox_buttonbox, 1, 0, alignment=Qt.AlignCenter)


class CentralWidget(QWidget):
    def __init__(self, path, parent=None):
        super(QWidget, self).__init__(parent)
        ###### DATA VARIABLES
        self.y_extT = None
        self.x_extT = None
        #####################
        self.parameters = None
        self.load_parameters()
        self.current_dir = path
        self.data_path = os.path.join(self.current_dir, "data")
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet('QTabBar { font-size: 12pt; font-family: Arial; }')
        self.A_tab = QWidget()
        self.B_tab = QWidget()
        self.Light_tab = QWidget()
        self.RSSI_tab = QWidget()
        self.tabs.resize(300, 200)
        # Add tabs
        self.tabs.addTab(self.A_tab, "Balloon A")
        self.tabs.addTab(self.B_tab, "Balloon B")
        self.tabs.addTab(self.Light_tab, "Light Sensor")
        self.tabs.addTab(self.RSSI_tab, "RSSI")
        # Tabs Layout
        self.A_layout = QGridLayout(self)
        self.A_tab.setLayout(self.A_layout)
        self.B_layout = QGridLayout(self)
        self.B_tab.setLayout(self.B_layout)
        self.Light_layout = QGridLayout(self)
        self.Light_tab.setLayout(self.Light_layout)
        self.RSSI_layout = QGridLayout(self)
        self.RSSI_tab.setLayout(self.RSSI_layout)

        # Dock Area ------------------------------------- A
        self.tabA_area = DockArea()
        self.A_layout.addWidget(self.tabA_area)
        # Creating A docks
        self.d_exT = Dock("External T°", size=(500, 500))
        self.d_P = Dock("Pressure", size=(500, 500))
        self.d_H = Dock("Humidity", size=(500, 500))
        self.d_gases = Dock("Trace Gases", size=(500, 500))
        self.d_particles = Dock("Fine Particles", size=(500, 500))

        # Add docks to tab A
        self.tabA_area.addDock(self.d_gases, 'right')
        self.tabA_area.addDock(self.d_exT, 'left', self.d_gases)
        self.tabA_area.addDock(self.d_P, 'bottom', self.d_exT)
        self.tabA_area.addDock(self.d_H, 'bottom', self.d_P)
        self.tabA_area.addDock(self.d_particles, 'right', self.d_gases)

        # Dock Area ------------------------------------- B
        self.tabB_area = DockArea()
        self.B_layout.addWidget(self.tabB_area)

        # Creating B docks
        self.d_GyroX = Dock("Gyro X", size=(500, 500))
        self.d_GyroY = Dock("Gyro Y", size=(500, 500))
        self.d_GyroZ = Dock("Gyro Z", size=(500, 500))

        # Add docks to tab B
        self.tabB_area.addDock(self.d_GyroX, 'right')
        self.tabB_area.addDock(self.d_GyroY, 'bottom', self.d_GyroX)
        self.tabB_area.addDock(self.d_GyroZ, 'bottom', self.d_GyroX)

        # Dock Area ------------------------------------- Light Sensor
        self.tabLight_area = DockArea()
        self.Light_layout.addWidget(self.tabLight_area)
        # Creating B docks
        self.d_LightA = Dock("Light Level A", size=(500, 500))
        self.d_LightB = Dock("Light Level B", size=(500, 500))

        # Add docks to tab B
        self.tabLight_area.addDock(self.d_LightA, 'right')
        self.tabLight_area.addDock(self.d_LightB, 'right', self.d_LightA)

        # Dock Area ------------------------------------- RSSI
        self.tabRSSI_area = DockArea()
        self.RSSI_layout.addWidget(self.tabRSSI_area)
        # Creating B docks
        self.d_RSSI_A = Dock("RSSI A", size=(500, 500))
        self.d_RSSI_B = Dock("RSSI B", size=(500, 500))

        # Add docks to tab B
        self.tabRSSI_area.addDock(self.d_RSSI_A, 'right')
        self.tabRSSI_area.addDock(self.d_RSSI_B, 'right', self.d_RSSI_A)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Temperature Plot ------------------------------ A
        self.x_T, self.y_T = self.select_data(0, "T external")
        self.extT = pg.PlotWidget(title="External Temperature", axisItems={'bottom': pg.DateAxisItem()})
        self.extT.plot(x=self.x_T, y=self.y_T, pen=(255, 0, 0))
        self.d_exT.addWidget(self.extT)

        # Pressure Plot ------------------------------ A
        self.x_P, self.y_P = self.select_data(0, "Pressure")
        self.P = pg.PlotWidget(title="Pressure", axisItems={'bottom': pg.DateAxisItem()})
        self.P.plot(x=self.x_P, y=self.y_P, pen=(255, 0, 0))
        self.d_P.addWidget(self.P)

        # Humidity Plot ------------------------------ A
        self.x_H, self.y_H = self.select_data(0, "Humidity Percentage")
        self.H = pg.PlotWidget(title="Humidity", axisItems={'bottom': pg.DateAxisItem()})
        self.H.plot(x=self.x_H, y=self.y_H, pen=(255, 0, 0))
        self.d_H.addWidget(self.H)

        # Gases Plot ------------------------------ A
        self.gases_list = ["CO", "O3", "CO2", "HCOH", "CH4", "NH3", "NO2", "H2", "C3H8", "C4H10", "C2H6OH"]
        color = self.color_code(len(self.gases_list))
        self.gases = pg.PlotWidget(title="Gases", axisItems={'bottom': pg.DateAxisItem()})
        self.gases.addLegend()
        self.x_gases, self.y_gases = [], []
        for i in range(len(self.gases_list)):
            x, y = self.select_data(0, self.gases_list[i] + ' Level')
            self.x_gases.append(x)
            self.y_gases.append(y)
            self.gases.plot(x=self.x_gases[i], y=self.y_gases[i], pen=color[i][:-1], name=self.gases_list[i])
        self.d_gases.addWidget(self.gases)

        # Fine Particles Plot ---------------------- A
        self.particles = pg.PlotWidget(title="Gases", axisItems={'bottom': pg.DateAxisItem()})
        self.particles.addLegend()
        color = self.color_code(2)
        x25, y25 = self.select_data(0, "p25 Level")
        x10, y10 = self.select_data(0, "p10 Level")
        self.x_particles, self.y_particles = [x25, x10], [y25, y10]
        self.particles.plot(x=self.x_particles[0], y=self.y_particles[0], pen=color[0][:-1], name="p25")
        self.particles.plot(x=self.x_particles[1], y=self.y_particles[1], pen=color[1][:-1], name="p10")
        self.d_particles.addWidget(self.particles)

        # Gyro X Plot ----------------------------- B
        self.x_gyroX, self.y_gyroX = self.select_data(1, "Gyro X")
        self.gyroX = pg.PlotWidget(title="Gyro X", axisItems={'bottom': pg.DateAxisItem()})
        self.gyroX.plot(x=self.x_gyroX, y=self.y_gyroX, pen=(255, 0, 0))
        self.d_GyroX.addWidget(self.gyroX)

        # Gyro Y Plot ----------------------------- B
        self.x_gyroY, self.y_gyroY = self.select_data(1, "Gyro Y")
        self.gyroY = pg.PlotWidget(title="Gyro Y", axisItems={'bottom': pg.DateAxisItem()})
        self.gyroY.plot(x=self.x_gyroY, y=self.y_gyroY, pen=(255, 0, 0))
        self.d_GyroY.addWidget(self.gyroY)

        # Gyro Z Plot ----------------------------- B
        self.x_gyroZ, self.y_gyroZ = self.select_data(1, "Gyro Z")
        self.gyroZ = pg.PlotWidget(title="Gyro Z", axisItems={'bottom': pg.DateAxisItem()})
        self.gyroZ.plot(x=self.x_gyroZ, y=self.y_gyroZ, pen=(255, 0, 0))
        self.d_GyroZ.addWidget(self.gyroZ)

        # Light Sensor ----------------------------- A
        self.x_lightA, self.y_lightA = self.select_data(0, "Light Level")
        self.lightA = pg.PlotWidget(title="Light Level A", axisItems={'bottom': pg.DateAxisItem()})
        self.lightA.plot(x=self.x_lightA, y=self.y_lightA, pen=(255, 0, 0))
        self.d_LightA.addWidget(self.lightA)

        # Light Sensor ----------------------------- B
        self.x_lightB, self.y_lightB = self.select_data(1, "Light Level")
        self.lightB = pg.PlotWidget(title="Light Level B", axisItems={'bottom': pg.DateAxisItem()})
        self.lightB.plot(x=self.x_lightB, y=self.y_lightB, pen=(255, 0, 0))
        self.d_LightB.addWidget(self.lightB)

        # RSSI ----------------------------- A
        self.x_rssiA, self.y_rssiA = self.select_data(0, "RSSI")
        self.rssiA = pg.PlotWidget(title="RSSI A", axisItems={'bottom': pg.DateAxisItem()})
        self.rssiA.plot(x=self.x_rssiA, y=self.y_rssiA, pen=(255, 0, 0))
        self.d_RSSI_A.addWidget(self.rssiA)

        # RSSI ----------------------------- B
        self.x_rssiB, self.y_rssiB = self.select_data(1, "RSSI")
        self.rssiB = pg.PlotWidget(title="RSSI B", axisItems={'bottom': pg.DateAxisItem()})
        self.rssiB.plot(x=self.x_rssiB, y=self.y_rssiB, pen=(255, 0, 0))
        self.d_RSSI_B.addWidget(self.rssiB)

        # Update Timer
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(500)

    def get_CSV_length(self, i):
        try:
            df = pd.read_csv(os.path.join(self.data_path, self.parameters["save_files"][i]))
        except FileNotFoundError:  # Creating a "false" datafile if the file is non-existent
            return 0
        return df.shape[0]

    def select_data(self, i, column, start_date="", finish_date=""):
        try:
            df = pd.read_csv(os.path.join(self.data_path, self.parameters["save_files"][i]))
        except FileNotFoundError:  # Creating a "false" datafile if the file is non-existent
            df = {"UNIX": t.time(), column: np.nan}
            df = pd.DataFrame(list(df.items()), columns=list(df.keys()))
            return np.array(df["UNIX"]), np.array(df[column])
        if len(df["UNIX"]) == 0:
            df = {"UNIX": t.time(), column: np.nan}
            df = pd.DataFrame(list(df.items()), columns=list(df.keys()))
            return np.array(df["UNIX"]), np.array(df[column])
        if start_date == "":
            start_date = np.array(df["UNIX"])[0]
        if finish_date == "":
            finish_date = np.array(df["UNIX"])[-1]
        time_mask = (df["UNIX"] >= start_date) & (df["UNIX"] <= finish_date)
        data = df.loc[time_mask]
        zeros_mask = data[column] == 0.0
        data = data.loc[~zeros_mask]
        return np.array(data["UNIX"]), np.array(data[column])

    @staticmethod
    def color_code(n):
        return plt.cm.rainbow(np.linspace(0, 1, n)) * 255

    def update_plots(self):
        self.load_parameters()
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            self.x_extT, self.y_extT = self.select_data(0, "T external")
            self.extT.plot(self.x_extT, self.y_extT, clear=True, pen=(255, 0, 0))
            self.x_P, self.y_P = self.select_data(0, "Pressure")
            self.P.plot(self.x_P, self.y_P, clear=True, pen=(255, 0, 0))
            self.x_H, self.y_H = self.select_data(0, "Humidity Percentage")
            self.H.plot(self.x_H, self.y_H, clear=True, pen=(255, 0, 0))
            n = len(self.gases_list)
            color = self.color_code(n)
            self.gases.clear()
            for i in range(n):
                self.x_gases[i], self.y_gases[i] = self.select_data(0, self.gases_list[i] + ' Level')
                self.gases.plot(self.x_gases[i], self.y_gases[i], pen=color[i][:-1], name=self.gases_list[i])
            self.particles.clear()
            x25, y25 = self.select_data(0, "p25 Level")
            x10, y10 = self.select_data(0, "p10 Level")
            self.x_particles, self.y_particles = [x25, x10], [y25, y10]
            self.particles.plot(x=self.x_particles[0], y=self.y_particles[0], pen=color[0][:-1], name="p25")
            self.particles.plot(x=self.x_particles[1], y=self.y_particles[1], pen=color[1][:-1], name="p10")
            if self.parameters["autoscale"]:
                self.extT.enableAutoRange('xy', True)
                self.P.enableAutoRange('xy', True)
                self.H.enableAutoRange('xy', True)
                self.gases.enableAutoRange('xy', True)
                self.particles.enableAutoRange('xy', True)
        if tab_index == 1:
            self.x_gyroX, self.y_gyroX = self.select_data(1, "Gyro X")
            self.gyroX.plot(x=self.x_gyroX, y=self.y_gyroX, pen=(255, 0, 0), clear=True)
            self.x_gyroY, self.y_gyroY = self.select_data(1, "Gyro Y")
            self.gyroY.plot(x=self.x_gyroY, y=self.y_gyroY, pen=(255, 0, 0), clear=True)
            self.x_gyroZ, self.y_gyroZ = self.select_data(1, "Gyro Z")
            self.gyroZ.plot(x=self.x_gyroZ, y=self.y_gyroZ, pen=(255, 0, 0), clear=True)
            if self.parameters["autoscale"]:
                self.gyroX.enableAutoRange('xy', True)
                self.gyroY.enableAutoRange('xy', True)
                self.gyroZ.enableAutoRange('xy', True)
        if tab_index == 2:
            self.x_lightA, self.y_lightA = self.select_data(0, "Light Level")
            self.lightA.plot(x=self.x_lightA, y=self.y_lightA, pen=(255, 0, 0), clear=True)
            self.x_lightB, self.y_lightB = self.select_data(1, "Light Level")
            self.lightB.plot(x=self.x_lightB, y=self.y_lightB, pen=(255, 0, 0), clear=True)
            if self.parameters["autoscale"]:
                self.lightA.enableAutoRange('xy', True)
                self.lightB.enableAutoRange('xy', True)
        if tab_index == 3:
            self.x_rssiA, self.y_rssiA = self.select_data(0, "RSSI")
            self.rssiA.plot(x=self.x_rssiA, y=self.y_rssiA, pen=(255, 0, 0), clear=True)
            self.x_rssiB, self.y_rssiB = self.select_data(1, "RSSI")
            self.rssiB.plot(x=self.x_rssiB, y=self.y_rssiB, pen=(255, 0, 0), clear=True)
            if self.parameters["autoscale"]:
                self.rssiA.enableAutoRange('xy', True)
                self.rssiB.enableAutoRange('xy', True)

    def load_parameters(self):
        self.parameters = {}
        with open("parameters", "r") as file:
            lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i].split(';')
            if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
                bauds = line[1].split(',')
                for j in range(len(bauds)):
                    bauds[j] = bauds[j].rstrip("\n")
                self.parameters[line[0]] = bauds
            elif line[0] == "rssi" or line[0] == "autoscroll" or line[0] == "autoscale":
                self.parameters[line[0]] = bool(int(line[1].rstrip("\n")))
            else:
                self.parameters[line[0]] = line[1].rstrip("\n")

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


