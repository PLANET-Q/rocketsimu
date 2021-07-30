import numpy as np
import quaternion
from .rocket import Rocket

class Launcher:
    def __init__(
                self,
                length,
                azimuth_deg,
                elevation_deg
                ):
        self.length = length
        self.azimuth = azimuth_deg * (np.pi / 180.0)
        self.elevation = elevation_deg * (np.pi / 180.0)
        self.rocket = None

    def setRocket(self, rocket:Rocket):
        self.rocket = rocket
        distance_1stlug_off =\
            self.length - (self.rocket.CG_rocket_init - self.rocket.lug_1st)
        self.height_1stlug_off = distance_1stlug_off * np.sin(self.elevation)
        distance_2ndlug_off =\
            self.length + (self.rocket.lug_2nd - self.rocket.CG_rocket_init)
        self.height_2ndlug_off = distance_2ndlug_off * np.sin(self.elevation)

        angle_z = (np.pi/2 - self.azimuth)
        qz = np.quaternion(np.cos(angle_z/2.0), 0.0, 0.0, np.sin(angle_z/2.0))
        angle_y = -self.elevation
        qy = np.quaternion(np.cos(angle_y/2.0), 0.0, np.sin(angle_y/2.0), 0.0)
        q0 = qz * qy

        self.rocket.x = np.zeros((3))
        self.rocket.v = np.zeros((3))
        self.rocket.omega = np.zeros((3))
        self.rocket.q = q0

    def is1stlugOff(self):
        if self.rocket is None:
            raise AttributeError('Class valiable "rocket" must be assigned.')

        if self.rocket.x[2] > self.height_1stlug_off:
            return True
        else:
            return False

    def is2ndlugOff(self):
        if self.rocket is None:
            raise AttributeError('Class valiable "rocket" must be assigned.')

        if self.rocket.x[2] > self.height_2ndlug_off:
            return True
        else:
            return False
