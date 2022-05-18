######################## IMPORTS ########################
import os
import shutil
import sys
import time as t
import subprocess

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSlot, QTimer, Qt

# --------------------- Sources ----------------------- #
from sources.common.widgets import MessageBox
from sources.common.parameters import load, save

######################## CLASSES ########################


class Balloon_GUI(QMainWindow):
    def __init__(self, path):
        super().__init__()
        ##################  PARAMETERS  ###################
        self.pid = None
        self.serial = None
        self.current_dir = path
        self.data_path = os.path.join(self.current_dir, "data")
        self.backup_path = os.path.join(self.data_path, "backups")
        self.setGeometry(500, 500, 1000, 600)
        self.setWindowTitle('Balloon Ground Station')
        self.setWindowIcon(QIcon('PyGS.jpg'))
        self.statusBar().showMessage('Ready')
        self.center()
        self.parameters = {}
        self.load_parameters()
        ##################  MENUBAR  ##################
        self.menubar = self.menuBar()
        # FILE MENU
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.aboutToShow.connect(self.check_file_menu)
        # new format
        new_formatAct = QAction('&New Format', self)
        new_formatAct.setStatusTip('Create New Packet Format')
        new_formatAct.triggered.connect(self.new_format)
        self.fileMenu.addAction(new_formatAct)
        # edit format
        open_formatAct = QAction('&Open Format', self)
        open_formatAct.setStatusTip('Edit Existing Packet Format')
        open_formatAct.triggered.connect(self.open_format)
        self.fileMenu.addAction(open_formatAct)
        self.fileMenu.addSeparator()
        # Archive Data
        self.archiveMenu = QMenu('&Archive', self)
        self.fileMenu.addMenu(self.archiveMenu)
        self.fileMenu.addSeparator()
        # exit action
        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        self.fileMenu.addAction(exitAct)
        # EDIT MENU
        self.editMenu = self.menubar.addMenu('&Edit')
        # change header
        change_headerAct = QAction('&Change Header', self)
        change_headerAct.setStatusTip('Change Packets Header')
        change_headerAct.triggered.connect(self.change_header)
        self.editMenu.addAction(change_headerAct)
        # TOOLS MENU
        self.toolsMenu = self.menubar.addMenu('&Tools')
        # Run Serial Code
        self.run_serialAct = QAction('&Run', self)
        self.run_serialAct.setStatusTip('Run Serial Listener')
        self.run_serialAct.triggered.connect(self.start_serial)
        self.toolsMenu.addAction(self.run_serialAct)
        # Stop Serial Code
        self.stop_serialAct = QAction('&Stop', self)
        self.stop_serialAct.setStatusTip('Stop Serial Listener')
        self.stop_serialAct.triggered.connect(self.stop_serial)
        self.toolsMenu.addAction(self.stop_serialAct)
        # Port Menu
        self.portMenu = QMenu('&Port', self)
        self.toolsMenu.addMenu(self.portMenu)
        self.available_ports = None
        self.toolsMenu.aboutToShow.connect(self.check_tools_menu)
        # Baud Menu
        baud_rates = self.parameters["available_bauds"]
        id_baud = baud_rates.index(str(self.parameters["selected_baud"]))
        self.baudMenu = QMenu('&Baud    ' + baud_rates[id_baud], self)
        baud_group = QActionGroup(self.baudMenu)
        for baud in baud_rates:
            action = QAction(baud, self.baudMenu, checkable=True, checked=baud == baud_rates[id_baud])
            self.baudMenu.addAction(action)
            baud_group.addAction(action)
        baud_group.setExclusive(True)
        baud_group.triggered.connect(self.select_baud)
        self.toolsMenu.addMenu(self.baudMenu)
        # Rssi
        self.rssiAct = QAction('&RSSI', self, checkable=True, checked=self.parameters["rssi"])
        self.rssiAct.setStatusTip('Toggle RSSI Retrieval')
        self.rssiAct.triggered.connect(self.set_rssi)
        self.toolsMenu.addAction(self.rssiAct)
        # HELP MENU
        self.helpMenu = self.menubar.addMenu('&Help')
        # Visit github page
        githubAct = QAction('&Visit Github', self)
        githubAct.setStatusTip('Visit Github Page')
        githubAct.triggered.connect(self.github_page)
        self.helpMenu.addAction(githubAct)

        ##################  VARIABLES  ##################
        if not os.path.exists("output"):
            file = open("output", "w").close()
        self.table_widget = CentralWidget(parent=self, path=self.current_dir)
        self.setCentralWidget(self.table_widget)
        self.table_widget.textedit.setDisabled(True)
        self.table_widget.textedit.setReadOnly(True)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_subprocess)
        self.output_lines = 0
        self.monitor_timer.start(100)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
            elif line[0] == "rssi" or line[0] == "autoscroll":
                self.parameters[line[0]] = bool(int(line[1].rstrip("\n")))
            else:
                self.parameters[line[0]] = line[1].rstrip("\n")

    def save_parameters(self):
        with open("parameters", "r") as file:
            lines = file.readlines()
        with open("parameters", "w") as file:
            for i in range(len(lines)):
                line = lines[i].split(';')
                if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
                    file.write(lines[i])
                elif line[0] == "rssi" or line[0] == "autoscroll":
                    file.write(line[0] + ';' + str(int(self.parameters[line[0]])) + '\n')
                else:
                    file.write(line[0] + ';' + str(self.parameters[line[0]]) + '\n')

    def check_file_menu(self):
        self.portMenu.setTitle('&Port')
        directory = os.path.join(self.current_dir, "data")
        file_names = [name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))]
        if len(file_names) == 0:
            self.archiveMenu.setDisabled(True)
        else:
            self.archiveMenu.clear()
            archive_group = QActionGroup(self.portMenu)
            for i in range(len(file_names)):
                archiveAct = QAction(file_names[i], self)
                archiveAct.setStatusTip('Archive ' + file_names[i])
                self.archiveMenu.addAction(archiveAct)
                archive_group.addAction(archiveAct)
            archive_group.triggered.connect(self.archive_save)

    def check_tools_menu(self):
        self.portMenu.setTitle('&Port')
        self.portMenu.setDisabled(False)
        import serial.tools.list_ports
        self.available_ports = [comport.device for comport in serial.tools.list_ports.comports()]
        if len(self.available_ports) == 0:
            self.stop_serialAct.setDisabled(True)
            self.portMenu.setDisabled(True)
            self.parameters["selected_port"] = ""
            self.save_parameters()
        else:
            self.portMenu.clear()
            port_group = QActionGroup(self.portMenu)
            selection = self.parameters["selected_port"]
            if selection in self.available_ports:
                for port in self.available_ports:
                    action = QAction(port, self.portMenu, checkable=True, checked=port == selection)
                    self.portMenu.addAction(action)
                    port_group.addAction(action)
                self.portMenu.setTitle('&Port    ' + selection)
            else:
                for port in self.available_ports:
                    action = QAction(port, self.portMenu, checkable=True, checked=port == self.available_ports[0])
                    self.portMenu.addAction(action)
                    port_group.addAction(action)
                self.portMenu.setTitle('&Port    ' + self.available_ports[0])
                self.parameters["selected_port"] = self.available_ports[0]
                self.save_parameters()
            port_group.setExclusive(True)
            port_group.triggered.connect(self.select_port)
        if self.serial is None:
            self.stop_serialAct.setDisabled(True)
            self.run_serialAct.setDisabled(False)
        else:
            self.stop_serialAct.setDisabled(False)
            self.run_serialAct.setDisabled(True)

    def select_baud(self, action):
        self.baudMenu.setTitle('&Baud    ' + action.text())
        self.parameters["selected_baud"] = action.text()
        self.save_parameters()
        # Restart Serial Connection if on
        if self.serial is not None:
            self.stop_serial()
            self.start_serial()

    def change_header(self):
        header_dialog = QInputDialog(self)
        header_dialog.setInputMode(QInputDialog.TextInput)
        header_dialog.setWindowTitle("Changing Header")
        header_dialog.setLabelText("Current  Header -> " + self.parameters["header"])
        header_dialog.resize(500, 100)
        okPressed = header_dialog.exec_()
        text = header_dialog.textValue()
        if okPressed and text != "":
            self.parameters["header"] = text
            self.save_parameters()
        elif okPressed and text == "":
            print("bruh")

    def new_format(self):
        pass

    def open_format(self):
        f_name = QFileDialog.getOpenFileName(self, "Open Format File", os.path.join(self.current_dir, "formats"))
        print(f_name[0])

    def save_format(self):
        pass

    def preferences(self):
        pass

    def archive_save(self, action):
        message = "File : " + action.text() + "\nThis remove its data, continue?"
        file_name = action.text()[:-4]
        print(file_name)
        msg = MessageBox()
        msg.setWindowIcon(QIcon('PyGS.jpg'))
        msg.setWindowTitle("Archiving File")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setStyleSheet("QLabel{min-width: 200px;}")
        msg.exec_()
        button = msg.clickedButton()
        sb = msg.standardButton(button)
        if sb == QMessageBox.Yes:
            old_path = os.path.join(self.data_path, action.text())
            new_path = os.path.join(self.backup_path, "backup_" + action.text())
            i = 1
            while os.path.exists(new_path):
                new_path = os.path.join(self.backup_path, "backup_" + file_name + "(" + str(i) + ")" + ".csv")
                i = i + 1
            shutil.move(old_path, new_path)

    def select_port(self, action):
        self.portMenu.setTitle('&Port    ' + action.text())
        self.parameters["selected_port"] = action.text()
        self.save_parameters()
        # Stop Serial Connection if on
        if self.serial is not None:
            self.stop_serial()

    def set_rssi(self, action):
        self.parameters["rssi"] = action
        self.save_parameters()
        # Restart Serial Connection if on
        if self.serial is not None:
            self.stop_serial()
            self.start_serial()

    def start_serial(self):
        message = "Port : " + self.parameters["selected_port"] + "  Baud : " + \
                  self.parameters["selected_baud"] + "\nDo you wish to continue ?"
        msg = MessageBox()
        msg.setWindowIcon(QIcon('PyGS.jpg'))
        msg.setWindowTitle("Running Warning")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setStyleSheet("QLabel{min-width: 200px;}")
        msg.exec_()
        button = msg.clickedButton()
        sb = msg.standardButton(button)
        if sb == QMessageBox.Yes:
            serial_file_path = os.path.dirname(os.path.realpath(__file__))
            if os.path.exists(os.path.join(serial_file_path, "SerialGS.py")):
                self.serial = subprocess.Popen([sys.executable, os.path.join(serial_file_path, "SerialGS.py")])
                self.pid = self.serial.pid
                self.table_widget.textedit.setDisabled(False)
            else:
                cancelling = MessageBox()
                cancelling.setWindowIcon(QIcon('PyGS.jpg'))
                cancelling.setWindowTitle("Error")
                cancelling.setText("SerialGS.py not found.")
                cancelling.setStandardButtons(QMessageBox.Ok)
                cancelling.setStyleSheet("QLabel{min-width: 200px;}")
                cancelling.exec_()

    def stop_serial(self):
        if self.serial is not None:
            self.serial.kill()
            self.serial.terminate()
            t.sleep(0.5)
            self.table_widget.textedit.setDisabled(True)
            self.serial = None

    def check_subprocess(self):
        self.load_parameters()
        if self.serial is not None and self.serial.poll() is not None:
            self.stop_serial()
            self.table_widget.textedit.setDisabled(True)
        elif self.serial is not None and self.serial.poll() is None:
            with open(self.parameters["output_file"], "r") as file:
                lines = file.readlines()
            if len(lines) != self.output_lines:
                self.table_widget.textedit.append(lines[-1])
                self.output_lines = len(lines)
            if bool(self.parameters["autoscroll"]):
                self.table_widget.textedit.moveCursor(QTextCursor.End)
            else:
                self.table_widget.textedit.moveCursor(QTextCursor.Start)
        else:
            pass

    @staticmethod
    def github_page():
        import webbrowser
        webbrowser.open("https://github.com/EnguerranVidal/WeatherBalloon-GroundStation")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stop_serial()
            os.remove("output")
            for window in QApplication.topLevelWidgets():
                window.close()
            event.accept()

        else:
            event.ignore()


class CentralWidget(QWidget):
    def __init__(self, path, parent=None):
        super(QWidget, self).__init__(parent)
        self.parameters = None
        self.load_parameters()
        self.resize(1000, 1000)
        self.current_dir = path
        self.data_path = os.path.join(self.current_dir, "data")
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        # Loading parameters
        self.parameters = {}
        self.load_parameters()
        # Text edit box
        self.textedit = QTextEdit(self)
        self.textedit.setText('Run Serial listening to display incoming info ...')
        self.textedit.setStyleSheet('font-size:15px')
        self.layout.addWidget(self.textedit, 1, 1, 1, 2)
        # Autoscroll Che-box
        self.autoscroll_box = QCheckBox("Autoscroll")
        self.autoscroll_box.setChecked(bool(self.parameters["autoscroll"]))
        self.autoscroll_box.stateChanged.connect(self.change_autoscroll)
        self.layout.addWidget(self.autoscroll_box, 2, 1)
        # Clearing Output Button
        self.clearButton = QPushButton("Clear Output")
        self.clearButton.clicked.connect(self.clear_output)
        self.layout.addWidget(self.clearButton, 2, 2)

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
            elif line[0] == "rssi" or line[0] == "autoscroll":
                self.parameters[line[0]] = bool(int(line[1].rstrip("\n")))
            else:
                self.parameters[line[0]] = line[1].rstrip("\n")

    def save_parameters(self):
        with open("parameters", "r") as file:
            lines = file.readlines()
        with open("parameters", "w") as file:
            for i in range(len(lines)):
                line = lines[i].split(';')
                if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
                    file.write(lines[i])
                elif line[0] == "rssi" or line[0] == "autoscroll":
                    file.write(line[0] + ';' + str(int(self.parameters[line[0]])) + '\n')
                else:
                    file.write(line[0] + ';' + str(self.parameters[line[0]]) + '\n')

    def change_autoscroll(self):
        self.parameters["autoscroll"] = int(not bool(self.parameters["autoscroll"]))
        self.save_parameters()
        self.autoscroll_box.setChecked(bool(self.parameters["autoscroll"]))

    @staticmethod
    def clear_output(self):
        file = open("output", "w").close()

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())