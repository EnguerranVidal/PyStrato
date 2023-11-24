from sources.PyStrato import *
import sys


def main(*args):
    app = QApplication(sys.argv)
    currentDirectory = os.path.dirname(os.path.realpath(__file__))
    splashScreenPath = os.path.join(currentDirectory, "sources/icons/SplashScreen.png")
    splashScreen = LoadingSplashScreen(splashScreenPath, currentDirectory)
    pyStratoGui = PyStratoGui(currentDirectory)

    def showPyStratoGui(loadingData):
        pyStratoGui.initializeUI(loadingData)
        if pyStratoGui.settings['MAXIMIZED']:
            pyStratoGui.showMaximized()
        else:
            pyStratoGui.showNormal()
        pyStratoGui.show()
        splashScreen.close()

    splashScreen.workerFinished.connect(showPyStratoGui)
    splashScreen.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

