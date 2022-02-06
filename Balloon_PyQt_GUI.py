from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSlot


class Balloon_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        ##################  PARAMETERS  ###################
        self.setGeometry(500, 500, 500, 300)
        self.setWindowTitle('Balloon Ground Station')
        self.setWindowIcon(QIcon('logo.jpg'))
        self.statusBar().showMessage('Ready')
        self.center()
        ##################  MENUBAR  ##################
        menubar = self.menuBar()
        # FILE MENU
        fileMenu = menubar.addMenu('&File')
        # exit action
        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        ##################  VARIABLES  ##################
        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class MyTableWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.A_tab = QWidget()
        self.B_tab = QWidget()
        self.tabs.resize(300, 200)
        # Add tabs
        self.tabs.addTab(self.A_tab, "Balloon A")
        self.tabs.addTab(self.B_tab, "Balloon B")
        # Create first tab
        self.A_tab.layout = QVBoxLayout(self)
        self.pushButton1 = QPushButton("Random button")
        self.A_tab.layout.addWidget(self.pushButton1)
        self.A_tab.setLayout(self.A_tab.layout)
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())