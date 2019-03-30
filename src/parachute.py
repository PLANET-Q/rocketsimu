# -*- coding:utf-8 -*-
import numpy as np

__author__ = 'Yusuke YAMAMOTO <motsulab@gmail.com>'
__status__ = 'debug'
__version__ = '0.0.1'
__date__ = '26 Feb 2019'

class Parachute:
    '''
    パラシュートに関するパラメータを保持するクラス
    NOTE:ドローグシュートとメインパラシュートの二段式の場合は
    二つのParachuteインスタンスを用意する必要がある
    '''

    def __init__(self, Cd, S, t_deploy, rocket=None, air=None):
        self.rocket = rocket
        self.air = air
        self.Cd = Cd
        self.S = S
        self.t_deploy = t_deploy
    
    def DrugForce(self, v_air, rho):
        # parachute drag force
        parachute_drag = 0.5 * rho * np.linalg.norm(v_air) * v_air * self.S * self.Cd

        # print('v_air', v_air, 'speed', np.linalg.norm(v_air))
        return parachute_drag