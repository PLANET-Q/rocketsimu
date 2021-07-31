# -*- coding:utf-8 -*-
import json
import os
from typing import Optional
import yaml
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

def simulate(
        parameters_filename:str,
        thrust_curve_filename:Optional[str]=None
    ):
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
        param_ext = os.path.splitext(parameters_filename)[1]
        if param_ext == '.json':
            params = json.load(f)
        elif param_ext == '.yml' or param_ext == '.yaml':
            params = yaml.load(f)

    rocket = Rocket(params['rocket'])

    engine_params = params['engine']
    engine = RocketEngine(engine_params)
    if thrust_curve_filename is None:
        thrust_curve_filename = engine_params['thrust_curve_csv']
    if 'cutoff_freq' in engine_params:
        cutoff_freq = engine_params['cutoff_freq']
    else:
        cutoff_freq = 10
    engine.loadThrust(thrust_curve_filename, engine_params['thrust_dt'], cutoff_freq)

    parachute_params = params['parachutes']
    if 'drogue' in parachute_params and parachute_params['drogue']['enable'] == True:
        drogue_params = parachute_params['drogue']
        drogue = Parachute(drogue_params['Cd'], drogue_params['S'])
        # set trigger of the droguechute's deployment
        drogue.set_triggers(drogue_params['trigger'])
        rocket.joinDroguechute(drogue)

    main_para_params = parachute_params['para']
    para = Parachute(main_para_params['Cd'], main_para_params['S'])
    # set trigger of the parachute's deployment
    para.set_triggers(main_para_params['trigger'])

    rocket.joinParachute(para)
    rocket.joinEngine(engine, position=params['rocket']['CG_prop'])

    wind = createWind(params['wind_model'], params['wind_parameters'])
    rocket.air = Air(wind)

    launcher_params = params['launcher']
    rocket.launcher = Launcher(launcher_params['rail_length'], launcher_params['azimuth'], launcher_params['elev_angle'])
    env_params = params['environment']
    rocket.enviroment = Enviroment(env_params['latitude'], env_params['longitude'], env_params['alt_launcher'])

    rocket.setRocketOnLauncher()

    solver = TrajectorySolver(max_t=params['simulation']['t_max'])
    result = solver.solve(rocket)
    return result
