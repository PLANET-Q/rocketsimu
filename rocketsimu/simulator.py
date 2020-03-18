# -*- coding:utf-8 -*-
import json
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

    solver = TrajectorySolver(rocket, max_t=params['t_max'])
    
    solution = solver.solve().T

    x_sol = solution[:3]
    v_sol = solution[3:6]
    q_sol = solution[6:10]
    omega_sol = solution[10:]

    return solver.t, x_sol, v_sol, q_sol, omega_sol, solver.solver_log