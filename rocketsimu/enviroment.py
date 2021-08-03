import numpy as np

# GRS80地球楕円体モデル
# a:長半径[m], b:短半径(極半径)[m]
EARTH_RADIUS_A = 6378137
EARTH_RADIUS_B = 6356752
# e: 離心率
EARTH_ECCENTRICITY = 0.081819191042815790
# 地球回転角速度[rad/s]
EARTH_OMEGA = 0.000072722052166


def reduced_latitude(latitude_deg:float)->float:
    '''
    地理緯度から更正緯度を求める
    '''
    return np.arctan(np.sqrt(1-EARTH_ECCENTRICITY**2)*np.tan(np.deg2rad(latitude_deg)))


def calc_earth_radius_at(latitude_deg:float)->float:
    reduced_lat = reduced_latitude(latitude_deg)
    earth_r = np.sqrt((EARTH_RADIUS_A * np.cos(reduced_lat))**2 +\
                (EARTH_RADIUS_B * np.sin(reduced_lat))**2)
    return earth_r


def get_deg2rect_coeff(latitude):
    deg2rad = np.pi / 180

    # 射点緯度経度における楕円体半径[m]
    earth_r = calc_earth_radius_at(latitude)
    lat2met = deg2rad * earth_r
    return lat2met


def xy_to_latlon(
        point_from_coord0:np.ndarray,
        latitude:float, longitude:float,
        mag_deg:float=0.0
    ):
    '''
    Arguments:
        point_from_coord0: np.ndarray ([N,]2),
        latitude:float, degree
        longitude:float, degree
        mag_deg:float
    '''
    deg2rad = np.pi / 180

    # 射点緯度経度における楕円体半径[m]
    earth_r = calc_earth_radius_at(latitude)
    lat2met = deg2rad * earth_r
    lon2met = deg2rad * earth_r * np.cos(np.deg2rad(latitude))
    point2coord = np.array([1/lon2met, 1/lat2met])

    # magnetic declination
    mag_dec_rad = np.deg2rad(mag_deg)
    magsin = np.sin(mag_dec_rad)
    magcos = np.cos(mag_dec_rad)
    mat_rot = np.array([[magcos, -magsin],
                        [magsin, magcos]])
    point_true_north = np.dot(mat_rot, point_from_coord0.T).T

    lonlat = point_true_north * point2coord + np.array([longitude, latitude])
    if len(lonlat.shape) == 1:
        latlon = lonlat[::-1]
    else:
        latlon = lonlat[:, ::-1]
    return latlon


class Enviroment:
    def __init__(
            self,
            latitude,
            longitude,
            altitude=0,
            magnetic_gap_deg=0.0
        ):
        self.latitude = latitude
        self.longitude = longitude
        self.alt_launcher = altitude
        self.magnetic_gap_deg = magnetic_gap_deg

        # 射点緯度経度における楕円体半径[m]
        self.earth_r = calc_earth_radius_at(self.latitude)

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
        self.omega_earth_local = np.dot(self.Tel.T, np.array([0., 0., EARTH_OMEGA]))

    def xy2latlon(self, point:np.ndarray)->np.ndarray:
        '''
        Arguments:
            point: np.ndarray ([N, ]2)
        '''
        return xy_to_latlon(point, self.latitude, self.longitude, self.magnetic_gap_deg)

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