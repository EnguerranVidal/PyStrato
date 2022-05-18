import sys
import math
import pygame
from pygame.locals import K_UP, K_DOWN, K_RIGHT, K_LEFT
from operator import itemgetter


class Point3D:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def rotateX(self, angle):
        rad = angle * math.pi / 180
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        y = self.y * cos_a - self.z * sin_a
        z = self.y * sin_a + self.z * cos_a
        return Point3D(self.x, y, z)

    def rotateY(self, angle):
        rad = angle * math.pi / 180
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        z = self.z * cos_a - self.x * sin_a
        x = self.z * sin_a + self.x * cos_a
        return Point3D(x, self.y, z)

    def rotateZ(self, angle):
        # determines radians
        rad = angle * math.pi / 180
        # cos of radians
        cosa = math.cos(rad)
        # sin of radians
        sina = math.sin(rad)
        # calculate new x value
        x = self.x * cosa - self.y * sina
        # calculate new y value
        y = self.x * sina + self.y * cosa
        # return Point3D (rotating around Z axis, therefore no change in Z value)
        return Point3D(x, y, self.z)

    def project(self, win_width, win_height, fov, viewer_distance):
        # factor using field of vision
        factor = fov / (viewer_distance + self.z)
        # x value
        x = self.x * factor + win_width / 2
        # y value
        y = -self.y * factor + win_height / 2
        # return Point3D (2D point, z=1)
        return Point3D(x, y, self.z)


class Simulation:
    def __init__(self, win_width=640, win_height=480):
        pygame.init()
        # set screen to certain width and height
        self.screen = pygame.display.set_mode((win_width, win_height))
        # set caption
        pygame.display.set_caption("Simulation of 3D Cube Rotation")
        # system clock time
        self.clock = pygame.time.Clock()
        # create box vertices
        self.vertices = [Point3D(-1, 1, -2), Point3D(1, 1, -2), Point3D(1, -1, -2),
                         Point3D(-1, -1, -2), Point3D(-1, 1, 2), Point3D(1, 1, 2),
                         Point3D(1, -1, 2), Point3D(-1, -1, 2)]
        # Faces correspond to 4 Point3Ds
        self.faces = [(0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6), (4, 0, 3, 7), (0, 4, 5, 1), (3, 2, 6, 7)]
        # Define colors for each face
        self.colors = [(255, 0, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 255, 0)]
        self.angleX, self.angleY, self.angleZ = 0, 0, 0

    def rotate(self, direction):
        # It will hold transformed vertices.
        vertices = []
        for vertex in self.vertices:
            # Rotate the point around X axis, then around Y axis, and finally around Z axis.
            rotation = vertex.rotateX(self.angleX).rotateY(self.angleY).rotateZ(self.angleZ)
            # Transform the point from 3D to 2D
            projection = rotation.project(self.screen.get_width(), self.screen.get_height(), 256, 4)
            # Put the point in the list of transformed vertices
            vertices.append(projection)
        # Calculate the average Z values of each face.
        avgZ = []
        i = 0
        for f in self.faces:
            z = (vertices[f[0]].z + vertices[f[1]].z + vertices[f[2]].z + vertices[f[3]].z) / 4.0
            avgZ.append([i, z])
            i = i + 1
        # Sort the "z" values in reverse and display the foremost faces last
        for zVal in sorted(avgZ, key=itemgetter(1), reverse=True):
            fIndex = zVal[0]
            f = self.faces[fIndex]
            points = [(vertices[f[0]].x, vertices[f[0]].y), (vertices[f[1]].x, vertices[f[1]].y),
                      (vertices[f[1]].x, vertices[f[1]].y), (vertices[f[2]].x, vertices[f[2]].y),
                      (vertices[f[2]].x, vertices[f[2]].y), (vertices[f[3]].x, vertices[f[3]].y),
                      (vertices[f[3]].x, vertices[f[3]].y), (vertices[f[0]].x, vertices[f[0]].y)]
            pygame.draw.polygon(self.screen, self.colors[fIndex], points)
        # increment angles to simulate rotation in the given direction
        if direction == "UP":
            self.angleX += 2
        elif direction == "DOWN":
            self.angleX -= 2
        elif direction == "LEFT":
            self.angleY += 2
        elif direction == "RIGHT":
            self.angleY -= 2
        # updates display surface to screen
        pygame.display.flip()

    def run(self):
        # starting background color
        black = [0, 0, 0]
        # fade in color background
        # fadeInColor = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        # fill background
        self.screen.fill(black)
        # initial display
        self.rotate("UP")
        # updates display surface to screen
        pygame.display.flip()
        while 1:
            self.screen.fill(black)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            # delay
            self.clock.tick(50)
            # grabs the pressed keys
            keys = pygame.key.get_pressed()
            if keys[K_UP]:
                self.rotate("UP")
            if keys[K_DOWN]:
                self.rotate("DOWN")
            if keys[K_LEFT]:
                self.rotate("LEFT")
            if keys[K_RIGHT]:
                self.rotate("RIGHT")


if __name__ == "__main__":
    Simulation().run()
