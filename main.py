from sources.PyGS import *
import sys


def test_pyqt5(*args):
    app = QApplication(sys.argv)
    # Force the style to be the same on all OSs:
    app.setStyle('Windows')
    path = os.path.dirname(os.path.realpath(__file__))
    ex = PyGS(path)
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_pyqt5()

