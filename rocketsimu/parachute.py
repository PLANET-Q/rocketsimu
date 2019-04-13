# -*- coding:utf-8 -*-
import numpy as np
import numpy.linalg as LA
import quaternion

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

    def __init__(self, Cd, S):
        self.rocket = None
        self.air = None
        self.__Cd = Cd
        self.__S = S
        self.__t_deploy = None
        self.__t_deploy_falling = None
        self.__alt_deploy = None
    
    def setAltitudeTrigger(self, alt):
        self.__alt_deploy = alt
    
    def setFallTimeTrigger(self, t_falling):
        self.__t_deploy_falling = t_falling
    
    def setFlightTimeTrigger(self, t_flight):
        self.__t_deploy = t_flight
    
    def isDeploy(self):
        if self.__t_deploy is not None:
            if self.rocket.t > self.__t_deploy:
                return True
        if self.__t_deploy_falling is not None and self.rocket.t_apogee is not None:
            if self.rocket.t - self.rocket.t_apogee > self.__t_deploy_falling:
                return True
        if self.__alt_deploy is not None and self.rocket.t_apogee is not None:
            if self.rocket.x[2] < self.__alt_deploy:
                return True
        return False
    
    def joinRocket(self, rocket):
        self.rocket = rocket
    
    def setAir(self, air):
        self.air = air
    
    def DragForce(self, v_air, rho):
        '''
        Returns parachute drag force.  
        INPUT
            v_air: air velocity vector in body coord.
            rho: air density
        OUTPUT
            parachute drag force vector in body coord.
        '''
        
        parachute_drag = 0.5 * rho * LA.norm(v_air) * v_air * self.__S * self.__Cd

        return parachute_drag