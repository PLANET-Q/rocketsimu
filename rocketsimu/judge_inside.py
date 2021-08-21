from abc import abstractmethod
from typing import List, Literal, Tuple, Union
from .enviroment import get_deg2rect_coeff
import numpy as np


def raycast_to_x_positive(
        x: float, y:float,
        line_p0:np.ndarray,
        line_p1:np.ndarray,
        segment_mode:bool=True)->bool:
    ymin = min(line_p0[1], line_p1[1])
    ymax = max(line_p0[1], line_p1[1])
    if y == line_p0[1]:
        if x < line_p0[0]:
            # the ray crosses p0
            return True
    elif (ymin < y < ymax) or (not segment_mode):
        dx = line_p1[0] - line_p0[0]
        dy = line_p1[1] - line_p0[1]
        if dy == 0.0:
            return False
        elif dx == 0.0:
            if x < line_p0[0]:
                # print(f' > crosses: {p0}->{p1}')
                return True
        else:
            # y = ax+b
            a = dy/dx
            b = line_p0[1] - a * line_p0[0]
            raycast_point_x = (y-b)/a
            if x < raycast_point_x:
                # print(f' > crosses: {p0}->{p1}')
                return True
    return False


class RestrictedArea:
    @property
    def name(self)->str:
        return ""

    @abstractmethod
    def judge(self, lat:float, lon:float)->bool:
        pass


class RestrictedCircle(RestrictedArea):
    def __init__(self,
            name:str,
            center_pos:np.ndarray,
            radius:float,
            mode:Literal['inside', 'outside']='inside'
        ) -> None:
        super().__init__()
        self._name = name
        self._center_latlon = center_pos
        self.radius = float(radius)
        if mode == 'inside':
            self.inside_mode = True
        elif mode == 'outside':
            self.inside_mode = False
        else:
            raise ValueError('Argument `mode` must be "inside" or "outside".')

    @property
    def name(self):
        return self._name

    def judge(self, lon:float, lat:float)->bool:
        p = np.array([lon, lat])
        # print(f' > center: {self._center_latlon}, point: {p}')
        deg2rect = get_deg2rect_coeff(self._center_latlon[0])
        distance = np.linalg.norm((p-self._center_latlon)*deg2rect)
        if self.inside_mode:
            # print(f'inside mode: {distance}, {self.radius}')
            return distance < self.radius
        else:
            # print(f'outside mode: {distance}, {self.radius}')
            return distance > self.radius


class RestrictedLine(RestrictedArea):
    def __init__(self,
            name:str,
            line_p0_latlng:np.ndarray,
            line_p1_latlng:np.ndarray,
            rail_latlng:np.ndarray,
            mode:Literal['over', 'under']='over'
        ) -> None:
        super().__init__()
        self._name = name
        self._p0_latlng = line_p0_latlng
        self._p1_latlng = line_p1_latlng
        self._rail_coord = rail_latlng
        if mode == 'over':
            self._over_mode = True
        elif mode == 'under':
            self._over_mode = False
        else:
            raise ValueError('Argument `mode` must be "over" or "under".')

    @property
    def name(self):
        return self._name

    def judge(self, lat:float, lng:float)->bool:
        rail_raycast = raycast_to_x_positive(
                            self._rail_coord[0],
                            self._rail_coord[1],
                            self._p0_latlng,
                            self._p1_latlng,
                            segment_mode=False
                        )
        drop_raycast = raycast_to_x_positive(
                            lat,
                            lng,
                            self._p0_latlng,
                            self._p1_latlng,
                            segment_mode=False
                        )
        return rail_raycast ^ drop_raycast


class RestrictedAreaPolygon(RestrictedArea):
    def __init__(self,
            name:str,
            points:np.ndarray,
            mode:Literal['inside', 'outside']='inside'
        ) -> None:
        super().__init__()
        self._name = name
        self._points = points
        if mode == 'inside':
            self.inside_mode = True
        elif mode == 'outside':
            self.inside_mode = False
        else:
            raise ValueError('Argument `mode` must be "inside" or "outside".')

    @property
    def name(self):
        return self._name

    def judge(self, lat:float, lon:float)->bool:
        # judge the point inside the polygon range, by raycasting method
        # In this method, lat-positive direction ray is cast from the check point.
        # https://www.hiramine.com/programming/graphics/2d_ispointinpolygon.html
        # cross_num = np.zeros(len(point))
        cross_num = 0
        # print(f'judge {lat} {lon}')
        for p0, p1 in zip(self._points[:-1], self._points[1:]):
            if raycast_to_x_positive(lat, lon, p0, p1, segment_mode=True):
                cross_num += 1

        if np.mod(cross_num, 2) == 0:
            # outside of polygon
            # print(f'outside of polygon {cross_num}')
            if self.inside_mode == False:
                return True
        else:
            # inside of polygon
            # print(f'inside of polygon {cross_num}')
            if self.inside_mode == True:
                return True
        return False


def load_restricted_area(
            area_info:dict,
            latitude:float,
            longitude:float)->RestrictedArea:
    if area_info['type'] == 'circle':
        restrict = RestrictedCircle(
                    area_info['name'],
                    np.array(area_info['center']),
                    radius=area_info['radius'],
                    mode=area_info['mode']
                )
    elif area_info['type'] == 'polygon':
        restrict = RestrictedAreaPolygon(
                    area_info['name'],
                    np.array(area_info['points']),
                    area_info['mode']
        )
    elif area_info['type'] == 'line':
        restrict = RestrictedLine(
                    area_info['name'],
                    area_info['point1'],
                    area_info['point2'],
                    rail_latlng=[latitude, longitude],
                    mode=area_info['mode']
                )
    else:
        raise ValueError(f'invalid info type: `{area_info["type"]}`')

    return restrict


class InsideAreaJudgement:
    def __init__(self, restricts_info:List[dict], rail_latlng:Union[List, Tuple, np.ndarray]) -> None:
        restricts = []
        for restrict_info in restricts_info:
            restricts.append(load_restricted_area(restrict_info, rail_latlng[0], rail_latlng[1]))
        self._restricts = restricts

    def __call__(self, lat:float, lon:float):
        judge_results = np.array([r.judge(lat, lon) for r in self._restricts])
        return judge_results.all()
