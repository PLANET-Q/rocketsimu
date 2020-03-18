# -*- coding:utf-8 -*-
import json
import numpy as np
from .enviroment import Enviroment
from .launcher import Launcher
from .rocket import Rocket
from .engine import RocketEngine
from .air import Air
from .wind import createWind
from .parachute import Parachute
from .solver import TrajectorySolver

__author__ = 'Yusuke YAMAMOTO <motsulab@gmail.com>'
__status__ = 'debug'
__version__ = '0.0.1'
__date__ = '8 Apl 2019'

'''
シミュレーションインターフェース関数をまとめたスクリプト
'''

def simulate(parameters_filename):
    '''
    INPUT
        parameters_filename: ロケットのパラメータが格納されているJSONファイル名
    OUTPUT
        タプル(t, x, v, q, omega)
        t: time arrray
        x: 各時刻におけるランチャからの位置ベクトル
        v: 各時刻における地球から見た機体座標系での速度ベクトル
        q: 各時刻における姿勢クオータニオン
        omega: 各時刻における機体座標系各軸周りの各速度ベクトル
    '''

    with open(parameters_filename, 'r') as f:
        params = json.load(f)
    
    rocket = Rocket(params)
    engine = RocketEngine(params)
    engine.loadThrust(params['thrust_curve_csv'], params['thrust_dt'])

    if params['is_drogue'] is True:
        drogue = Parachute(params['Cd_drogue'], params['S_drogue'])
    para = Parachute(params['Cd_para'], params['S_para'])

    # set trigger of the droguechute's deployment
    if params['is_drogue'] is True:
        drogue_triggers_dict = params['drogue_trigger']
        if 'flight_time' in drogue_triggers_dict:
            drogue.setFlightTimeTrigger(drogue_triggers_dict['flight_time'])
        if 'fall_time' in drogue_triggers_dict:
            drogue.setFallTimeTrigger(drogue_triggers_dict['fall_time'])
        if 'altitude' in drogue_triggers_dict:
            drogue.setAltitudeTrigger(drogue_triggers_dict['altitude'])

    # set trigger of the parachute's deployment
    para_triggers_dict = params['para_trigger']
    if 'flight_time' in para_triggers_dict:
        para.setFlightTimeTrigger(para_triggers_dict['flight_time'])
    if 'fall_time' in para_triggers_dict:
        para.setFallTimeTrigger(para_triggers_dict['fall_time'])
    if 'altitude' in para_triggers_dict:
        para.setAltitudeTrigger(para_triggers_dict['altitude'])

    if params['is_drogue'] is True:
        rocket.joinDroguechute(drogue)
    rocket.joinParachute(para)
    rocket.joinEngine(engine, position=params['CG_prop'])

    wind = createWind(params['wind_model'], params['wind_parameters'])
    rocket.air = Air(wind)
    rocket.launcher = Launcher(params['rail_length'], params['azimuth'], params['elev_angle'])
    rocket.enviroment = Enviroment(params['latitude'], params['longitude'], params['alt_launcher'])

    rocket.setRocketOnLauncher()

    solver = TrajectorySolver(rocket, dt=params['dt'], max_t=params['t_max'])
    
    solution = solver.solve().T

    # landingまでの時刻を切り出し
    t_landing = solver.solver_log['landing']['t']
    t_valid = solver.t[solver.t < t_landing]

    # landingまでに切り出し
    x_sol = solution[:3].T[solver.t < t_landing].T
    v_sol = solution[3:6].T[solver.t < t_landing].T
    q_sol = solution[6:10].T[solver.t < t_landing].T
    omega_sol = solution[10:].T[solver.t < t_landing].T

    # MaxQ, MaxMach, MaxVなどの導出
    speed = np.linalg.norm(v_sol, axis=0)
    a_speed = np.zeros((len(t_valid)))
    rho = np.zeros((len(t_valid)))
    p = np.zeros((len(t_valid)))
    T = np.zeros((len(t_valid)))
    for i, alt in enumerate(x_sol[2]):
        T[i], p[i], rho[i], a_speed[i] = rocket.air.standard_air(alt)
    mach = speed / a_speed

    Q = 0.5 * rho * speed**2
    Q_max_idx = np.argmax(Q)
    Mach_max_idx = np.argmax(mach)
    v_max_idx = np.argmax(speed)

    # max Q log
    solver.solver_log['MaxQ']={
        'Q': Q[Q_max_idx],
        't': t_valid[Q_max_idx],
        'p': p[Q_max_idx],
        'T': T[Q_max_idx],
        'mach': mach[Q_max_idx]
    }

    # max mach log
    solver.solver_log['MaxMach']={
        'Q': Q[Mach_max_idx],
        't': t_valid[Mach_max_idx],
        'p': p[Mach_max_idx],
        'T': T[Mach_max_idx],
        'mach': mach[Mach_max_idx]
    }

    # max V log
    solver.solver_log['MaxV']={
        'Q': Q[v_max_idx],
        't': t_valid[v_max_idx],
        'p': p[v_max_idx],
        'T': T[v_max_idx],
        'speed': speed[v_max_idx],
        'mach': mach[v_max_idx]
    }

    return t_valid, x_sol, v_sol, q_sol, omega_sol, solver.solver_log