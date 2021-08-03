from abc import abstractmethod
from typing import List, Literal
from .enviroment import get_deg2rect_coeff
import numpy as np


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
            ymin = min(p0[1], p1[1])
            ymax = max(p0[1], p1[1])
            if lon == p0[1]:
                if lat < p0[0]:
                    # the ray crosses p0
                    cross_num += 1
            elif ymin < lon < ymax:
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]
                if dy == 0.0:
                    pass
                elif dx == 0.0:
                    if lat < p0[0]:
                        # print(f' > crosses: {p0}->{p1}')
                        cross_num += 1
                else:
                    # y = ax+b
                    a = dy/dx
                    b = p0[1] - a * p0[0]
                    raycast_point_x = (lon-b)/a
                    if lat < raycast_point_x:
                        # print(f' > crosses: {p0}->{p1}')
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


def load_restricted_area(area_info:dict)->RestrictedArea:
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
    else:
        raise ValueError(f'invalid info type: `{area_info["type"]}`')

    return restrict


class InsideAreaJudgement:
    def __init__(self, restricts_info:List[dict]) -> None:
        restricts = []
        for restrict_info in restricts_info:
            restricts.append(load_restricted_area(restrict_info))
        self._restricts = restricts

    def __call__(self, lat:float, lon:float):
        judge_results = np.array([r.judge(lat, lon) for r in self._restricts])
        return judge_results.all()
