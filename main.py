from sources.PyGS import *
import sys


def test_pyqt5(style):
    app = QApplication(sys.argv)
    # Force the style to be the same on all OSs:
    app.setStyle('Windows')
    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(56, 56, 56))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(56, 56, 56))
    palette.setColor(QPalette.AlternateBase, QColor(63, 63, 63))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(56, 56, 56))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, QColor(0, 128, 152))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(0, 128, 152))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.Window, QColor(51, 51, 51))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(111, 111, 111))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(122, 118, 113))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(122, 118, 113))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(32, 32, 32))
    if style:
        app.setPalette(palette)
    path = os.path.dirname(os.path.realpath(__file__))
    ex = PyGS(path)
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_pyqt5(True)

