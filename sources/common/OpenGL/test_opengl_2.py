from PyQt5 import QtCore      # core Qt functionality
from PyQt5 import QtGui       # extends QtCore with GUI functionality
from PyQt5 import QtOpenGL    # provides QGLWidget, a special OpenGL QWidget
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import OpenGL.GL as gl        # python wrapping of OpenGL
from OpenGL import GLU        # OpenGL Utility Library, extends OpenGL functionality

import sys                    # we'll need this later to run our Qt application
from OpenGL.arrays import vbo
import numpy as np


class Window(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("gl box")
        self.setGeometry(0, 0, 300, 300)
        self.glWidget = GLWidget
        self.initGUI()
        timer = QtCore.QTimer(self)
        timer.setInterval(20)  # period, in milliseconds
        timer.timeout.connect(self.glWidget.updateGL)
        timer.start()

    def initGUI(self):
        glWidget = GLWidget(self)
        self.s1 = QSlider(Qt.Horizontal)
        self.s1.valueChanged.connect(lambda val: glWidget.setRotX(val))
        self.s1.setMaximum(360)
        self.s1.setMinimum(0)
        self.s2 = QSlider(Qt.Horizontal)
        self.s2.valueChanged.connect(lambda val: glWidget.setRotY(val))
        self.s2.setMaximum(360)
        self.s2.setMinimum(0)
        self.s3 = QSlider(Qt.Horizontal)
        self.s3.valueChanged.connect(lambda val: glWidget.setRotZ(val))
        self.s3.setMaximum(360)
        self.s3.setMinimum(0)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(glWidget)
        layout.addWidget(self.s1)
        layout.addWidget(self.s2)
        layout.addWidget(self.s3)

        self.glWidget = GLWidget(self)
        # self.initGUI()
        self.show()

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        self.parent = parent
        QtOpenGL.QGLWidget.__init__(self, parent)

    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0, 0))  # initialize the screen to blue
        gl.glEnable(gl.GL_DEPTH_TEST)  # enable depth testing

        self.initGeometry()

        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = width / float(height)

        GLU.gluPerspective(45.0, aspect, 1.0, 200.0)
        GLU.gluLookAt(10, 0, 0, 0, 0, 0, 0, 0, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def initGeometry(self):
        self.cubeVtxArray = np.array([[0.0, 0.0, -0.5], [1.0, 0.0, -0.5], [1.0, 1.0, -0.5], [0.0, 1.0, -0.5],
                                      [0.0, 0.0, 1.5], [1.0, 0.0, 1.5], [1.0, 1.0, 1.5], [0.0, 1.0, 1.5]])
        self.vertVBO = vbo.VBO(np.reshape(self.cubeVtxArray, (1, -1)).astype(np.float32))
        self.vertVBO.bind()

        self.cubeClrArray = np.array([[0.0, 0.0, -0.5], [1.0, 0.0, -0.5], [1.0, 1.0, -0.5], [0.0, 1.0, -0.5],
                                      [0.0, 0.0, 1.5], [1.0, 0.0, 1.5], [1.0, 1.0, 1.5], [0.0, 1.0, 1.5]])
        self.colorVBO = vbo.VBO(np.reshape(self.cubeClrArray, (1, -1)).astype(np.float32))
        self.colorVBO.bind()

        self.cubeIdxArray = np.array([0, 1, 2, 3, 3, 2, 6, 7, 1, 0, 4, 5, 2, 1, 5, 6, 0, 3, 7, 4, 7, 6, 5, 4])

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glPushMatrix()  # push the current matrix to the current stack

        gl.glTranslate(-80.0, 0.0, 0.0)  # third, translate cube to specified depth
        gl.glScale(20.0, 20.0, 20.0)  # second, scale cube
        # gl.glRotated(30, 0.5, 0.0, 0.0)
        gl.glRotated(self.rotX, 1.0, 0.0, 0.0)
        gl.glRotated(self.rotY, 0.0, 1.0, 0.0)
        gl.glRotated(self.rotZ, 0.0, 0.0, 1.0)
        gl.glTranslate(-0.5, -0.5, -0.5)  # first, translate cube center to origin


        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, self.vertVBO)
        gl.glColorPointer(3, gl.GL_FLOAT, 0, self.colorVBO)

        gl.glDrawElements(gl.GL_QUADS, len(self.cubeIdxArray), gl.GL_UNSIGNED_INT, self.cubeIdxArray)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)

        gl.glPopMatrix()  # restore the previous modelview matrix

    def setRotX(self, val):
        self.rotX = val
        self.update()

    def setRotY(self, val):
        self.rotY = val
        self.update()

    def setRotZ(self, val):
        self.rotZ = val
        self.update()


app = QtWidgets.QApplication(sys.argv)
w = Window()
app.exec_()
sys.exit()