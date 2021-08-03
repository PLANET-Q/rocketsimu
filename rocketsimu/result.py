from typing import Dict, Tuple
from matplotlib.pyplot import axis
import numpy as np
import quaternion
import json
from .air import Air


def get_max_t_values(t:np.ndarray, v:np.ndarray):
    max_idx = np.argmax(v)
    return t[max_idx], v[max_idx]


def analyze_trajectory(
        q:np.ndarray,
        x:np.ndarray,
        v_body:np.ndarray,
        air:Air
    )->Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Arguments:
        q: ndarray (N, 4)
        x: ndarray (N, 3)
        v_body: ndarray (N, 3)
        air: Air instance

    Output:
        Mach
        Dynamic_pressure
        V_air_body: air velocity vector in body coord.
        wind_local: wind vector in local coord.
    '''
    quat = quaternion.as_quat_array(q)

    air_vec = np.vectorize(air.standard_air)
    wind_vec = np.vectorize(lambda h: tuple(air.wind(h)))
    # print(X.shape)
    wind = np.array(wind_vec(x[:, 2])).T
    _, _, rho, acoustic_speed = air_vec(x[:,2])
    # print(time.shape, T.shape, P.shape, rho.shape)

    Tbl_array = quaternion.as_rotation_matrix(np.conj(quat))
    v_air_body = np.empty_like(v_body)
    for i, Tbl, w, v in zip(range(len(x)),Tbl_array, wind, v_body):
        v_air_body[i] = -v + np.dot(Tbl, w)

    v_air_norm = np.linalg.norm(v_air_body, axis=1)

    mach = v_air_norm / acoustic_speed
    dynamic_pressure = 0.5 * rho * v_air_norm**2

    return mach, dynamic_pressure, v_air_body, wind


class FlightEvents:
    def __init__(self) -> None:
        self._events = {}

    def events(self)->Dict[str, Dict[str, float]]:
        return self._events.copy()

    def add_event(self, name:str, t:float, exist_ok:bool=False, **kwargs):
        event = { 't': t }
        event.update(kwargs)
        if exist_ok is False and name in self._events:
            raise KeyError(f"Event name '{name}' is already exists. To ignore this, argument `exist_ok` should be `True` in `add_event`")
        self._events[name] = event

    def to_json(self, filename:str):
        with open(filename, 'w') as f:
            json.dump(self._events, f, indent=4)


class TrajectoryResult:
    def __init__(
            self,
            events:FlightEvents,
            t: np.ndarray,
            solution: np.ndarray,
            air: Air) -> None:
        self.events = events
        self.t = t
        self.x = solution[:3]
        self.v_body = solution[3:6]
        self.q = solution[6:10]
        self.w = solution[10:]

        # t_alt, max_alt = np.max(self.x[2])
        self.mach, self.dynamic_pressure, self.v_air_body, self.wind_local =\
            analyze_trajectory(self.q.T, self.x.T, self.v_body.T, air)

        t_max_mach, max_mach = get_max_t_values(t, self.mach)
        t_max_Q, max_Q = get_max_t_values(t, self.dynamic_pressure)
        t_max_speed, max_speed = get_max_t_values(t, np.linalg.norm(self.v_air_body, axis=1))
        self.events.add_event('max_mach', t_max_mach, mach=max_mach)
        self.events.add_event('max_Q', t_max_Q, Q=max_Q)
        self.events.add_event('max_air_speed', t_max_speed, air_speed=max_speed)
