# -*- coding:utf-8 -*-
import numpy as np
import numpy.linalg as LA

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
    
    def DragForce(self, v_air, rho):
        '''
        Returns parachute drag force.  
        INPUT
            para
            v_air: air velocity vector in body coord.
            rho: air density
        OUTPUT
            parachute drag force vector in body coord.
        '''
        
        parachute_drag = 0.5 * rho * LA.norm(v_air) * v_air * self.S * self.Cd

        return parachute_drag