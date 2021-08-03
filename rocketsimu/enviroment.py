import numpy as np
import numpy.linalg as LA
import quaternion
from . import wind
from .launcher import Launcher
from .air import Air


class Enviroment:
    def __init__(
            self,
            latitude,
            longitude,
            altitude=0
        ):
        self.latitude = latitude
        self.longitude = longitude
        self.alt_launcher = altitude

        # GPS80地球楕円体モデル
        # a:長半径[m], b:短半径(極半径)[m]
        self.earth_a = 6378137
        self.earth_b = 6356752

        # 地球回転角速度[rad/s]
        self.omega_earth = 0.000072722052166

        # 射点緯度経度における楕円体半径[m]
        self.earth_r = self.earth_a * np.cos(np.deg2rad(self.latitude)) +\
                        self.earth_b * np.sin(np.deg2rad(self.latitude))

        # 射点静止座標系→地球中心回転座標系への変換行列Tel
        sinlat = np.sin(np.deg2rad(self.latitude))
        coslat = np.cos(np.deg2rad(self.latitude))
        sinlon = np.sin(np.deg2rad(self.longitude))
        coslon = np.cos(np.deg2rad(self.longitude))
        self.Tel = np.array([
            [  -sinlon, -sinlat*coslon, coslat*coslon],
            [   coslon, -sinlat*sinlon, coslat*sinlon],
            [      0.0,         coslat,        sinlat]
            ])

        # 射点静止座標系における自転角速度ベクトル
        # 地球回転座標系での自転角速度を射点静止座標系に変換して求めている
        self.omega_earth_local = np.dot(self.Tel.T, np.array([0., 0., self.omega_earth]))

    def g(self, h):
        # TODO: 重力を高度hの関数にする。
        # 緯度経度から標高を算出する必要がある
        return np.array([0.0, 0.0, -9.81])

    def Coriolis(self, v_body, Tbl, mass=1.0):
        # =======================================
        # INPUT:  v_body = velocity in body coord.
        #         Tbl = tranformation matrix from local coord. to body coord.
        # OUTPUT: Fcor = Coriolis force vector in body coord.
        # =======================================

        # Coriolis  force in body coord. note that self.omega_earth, omega of earth-spin, is given in local coord.
        Fcor = 2.0*mass*np.cross(np.dot(Tbl, self.omega_earth_local), v_body)
        return Fcor