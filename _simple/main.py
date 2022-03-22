from Balloon_PyQt_GUI import*
import sys


def launch_pyqt5():
    app = QApplication(sys.argv)
    # Force the style to be the same on all OSs:
    ex = Balloon_GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    launch_pyqt5()

