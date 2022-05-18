from objloader import OBJ
from OpenGL.GL import*


box = OBJ('cube.obj')
glPushMatrix()
glTranslatef(1, 1, 1)
box.render()
glPopMatrix()