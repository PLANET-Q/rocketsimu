# -*- coding:utf-8 -*-

__author__ = 'Yusuke YAMAMOTO <motsulab@gmail.com>'
__status__ = 'debug'
__version__ = '0.0.1'
__date__ = '09 Feb 2019'

import numpy as np
import quaternion
import json
from engine import RocketEngine

class Rocket:
    '''
    ロケット機体に関するパラメータや
    位置/速度/角速度/姿勢を保持するクラス
    推進によって時間変化するロケット全体の重量と重心位置などを算出する

    内部でRocketEngineを保持し
    エンジン推力と推進剤パラメータはこのクラスが保持する
    '''

    def __init__(self, params=None):
        self.engine = RocketEngine()

        self.__params = {
            'height':0.0,
            'diameter':0.0,
            'CG_dry':0.0,
            'mass_dry':0.0,
            'lug_1st':0.0,
            'lug_2nd':0.0,
            'MOI_dry':[0.0, 0.0, 0.0],
            'Cmp':0.0,
            'Cmq':0.0,
            'CG_prop':0.0
        }
        self.__syncParamToDict()

        if params is not None:
            self.overwrite_parameters(params)

        self.parachute = None
        self.droguechute = None

        # NOTE: 座標系に依存するパラメータはこのクラスで適切か？
        self.v = np.zeros((3))
        self.omega = np.zeros((3))
        self.x = np.zeros((3))
        self.atitude = np.quaternion(0, 0, 0, 0)

    def overwrite_parameters(self, params):
        self.__params.update(params)
        self.__syncParamToDict()
    
    def totalCG(self, t):
        moment_dry = self.__CG_dry * self.__mass_dry
        moment_prop = self.__CG_prop * self.engine.propMass(t)
        return float((moment_dry + moment_prop)/(self.__mass_dry + self.engine.propMass(t)))

    def totalMass(self, t):
        return self.__mass_dry + self.engine.propMass(t)
    
    def totalMOI(self, t):
        # 平衡軸の定理を使用したモーメント計算
        # ロール方向のモーメントには影響しないとしている(即ちエンジンに偏心がない)
        CG = self.totalCG(t)
        yz_unit = np.array([0, 1.0, 1.0])
        MOI_body = self.__MOI_dry + self.__mass_dry*(CG - self.__CG_dry)**2 * yz_unit
        MOI_prop = self.engine.propMOI(t) + self.engine.propMass(t)*(CG - self.CG_prop)**2 * yz_unit
        #return (MOI_body + MOI_prop) * yz_unit
        return (MOI_body + MOI_prop)

    def joinEngine(self, engine, position):
        self.engine = engine
        self.CG_prop = position
        self.CG_rocket_init = self.totalCG(0)
    
    def joinDroguechute(self, droguechute):
        self.droguechute = droguechute
        pass

    def joinParachute(self, parachute):
        self.parachute = parachute
        pass
    
    def hasParachute(self):
        return self.parachute != None
    
    def hasDrogueChute(self):
        return self.droguechute != None
    
    def __syncParamToDict(self):
        self.__height = self.__params['body_height']

        self.__diameter = self.__params['body_diameter']

        # dry: 乾燥時,即ち推進剤無しの場合のパラメータのこと
        self.__CG_dry = self.__params['CG_dry']
        self.__mass_dry = self.__params['mass_dry']

        # ノーズ先端からのランチラグ位置
        self.__lug_1st = self.__params['lug_1st']
        self.__lug_2nd = self.__params['lug_2nd']

        # 乾燥時慣性モーメント
        self.__MOI_dry = self.__params['MOI_dry']

        # Cm:モーメント係数 Cmp:ロール方向, Cmq:ピッチ/ヨー方向
        self.__Cm = np.array([self.__params['Cmp'], self.__params['Cmq'], self.__params['Cmq']])

        # 推進剤重心のノーズ先端からの位置 [m]
        self.__CG_prop = self.__params['CG_prop']