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

    def __init__(self, params_filename = None):
        if params_filename is not None:
            self.loadParam(params_filename)

        self.engine = RocketEngine()

        # 推進剤重心のノーズ先端からの位置 [m]
        self.CG_prop = 0

        self.parachute = None
        self.droguechute = None

        # NOTE: 座標系に依存するパラメータはこのクラスで適切か？
        self.v = np.zeros((3))
        self.omega = np.zeros((3))
        self.x = np.zeros((3))
        self.atitude = np.quaternion(0, 0, 0, 0)

    def loadParam(self, filename):
        with open(filename, 'r') as f:
            params = json.load(f)
        
        self.height = params['body_height']
        self.diameter = params['body_diameter']

        # dry: 乾燥時,即ち推進剤無しの場合のパラメータのこと
        self.CG_dry = params['CG_dry']
        self.mass_dry = params['mass_dry']

        # ノーズ先端からのランチラグ位置
        self.lug_1st = params['lug_1st']
        self.lug_2nd = params['lug_2nd']
        MOI_x = params['MOI_dry_x']
        MOI_y = params['MOI_dry_y']
        MOI_z = params['MOI_dry_z']
        self.MOI_dry = np.array([MOI_x, MOI_y, MOI_z])

        # Cm:モーメント係数 Cmp:ロール方向, Cmq:ピッチ/ヨー方向
        self.Cm = np.array([params['Cmp'], params['Cmq'], params['Cmq']])
    
    def totalCG(self, t):
        moment_dry = self.CG_dry * self.mass_dry
        moment_prop = self.CG_prop * self.engine.propMass(t)
        return float((moment_dry + moment_prop)/(self.mass_dry + self.engine.propMass(t)))

    def totalMass(self, t):
        return self.mass_dry + self.engine.propMass(t)
    
    def totalMOI(self, t):
        # 平衡軸の定理を使用したモーメント計算
        # ロール方向のモーメントには影響しないとしている(即ちエンジンに偏心がない)
        CG = self.totalCG(t)
        yz_unit = np.array([0, 1.0, 1.0])
        MOI_body = self.MOI_dry + self.mass_dry*(CG - self.CG_dry)**2 * yz_unit
        MOI_prop = self.engine.propMOI(t) + self.engine.propMass(t)*(CG - self.CG_prop)**2 * yz_unit
        #return (MOI_body + MOI_prop) * yz_unit
        return (MOI_body + MOI_prop)

    def joinEngine(self, engine, position):
        self.engine = engine
        self.CG_prop = position
        self.CG_rocket_init = self.totalCG(0)
    
    def hasParachute(self):
        return self.parachute != None
    
    def hasDrogueChute(self):
        return self.droguechute != None