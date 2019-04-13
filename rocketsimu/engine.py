# -*- coding:utf-8 -*-

__author__ = 'Yusuke YAMAMOTO <motsulab@gmail.com>'
__status__ = 'debug'
__version__ = '0.0.1'
__date__ = '09 Feb 2019'

import pandas as pd
import numpy as np
import json
from .lpf import LPF
from scipy.interpolate import interp1d

class RocketEngine:
    '''
    ロケット推進剤に関するパラメータ及びエンジン推力カーブを保持
    時間変化する推力、推進剤消費に伴って時間変化する推進剤重量の計算等を担当

    Rocketクラスのインスタンスが保持している
    '''
    def __init__(self, params=None):
        self.__params = {
            'MOI_prop': np.array([0.0, 0.0, 0.0]),
            'mass_prop': 0.0
        }
        self.__syncParamsWithDict()

        if params is not None:
            self.overwrite_parameters(params)
    
    def overwrite_parameters(self, params):
        self.__params.update(params)
        self.__syncParamsWithDict()
    
    def __syncParamsWithDict(self):
        self.__MOI_init = self.__params['MOI_prop']
        self.__mass_init = self.__params['mass_prop']

    def loadThrust(self, thrust_filename, thrust_dt, cutoff_freq=10.):
        input_data = np.loadtxt(thrust_filename, comments=['$', '#', '%'], delimiter=',')
        thrust_raw = input_data[:, 1]
        self.thrust_dt = thrust_dt
        self.thrust_time_array = input_data[:, 0]

        if cutoff_freq > 0:
            # --------------------
            #  LPF Filtering
            # --------------------
            # TODO: LPF処理を別ファイルにしているが
            # 見やすさのためにここに直書きしたほうがいい

            # LPFメソッド: FFT -> cutoff -> IFFT
            self.thrust_array = LPF(thrust_raw, self.thrust_dt, cutoff_freq)
        else:
            self.thrust_array = thrust_raw
        self.thrust_array[self.thrust_array < 0.0] = 0.0

        self.max_thrust = np.max(self.thrust_array)
        
        '''
        self.thrust_startup_time = np.min(self.thrust_time_array[self.thrust_array >= self.max_thrust*0.01])
        self.thrust_cutoff_time = np.max(self.thrust_time_array[self.thrust_array >= self.max_thrust*0.01])\
                                    - self.thrust_startup_time

        self.thrust_array = self.thrust_array[self.thrust_time_array >= self.thrust_startup_time]
        self.thrust_time_array = self.thrust_time_array[self.thrust_time_array >= self.thrust_startup_time]
        self.thrust_time_array -= self.thrust_time_array[0]
        '''

        self.thrust_time_array, self.thrust_array = trimThrust(self.thrust_array, self.thrust_time_array, threshold_rate=0.01)
        self.thrust_startup_time = self.thrust_time_array[0]
        self.thrust_cutoff_time = self.thrust_time_array[-1]
        
        self.thrust_n_samples = len(self.thrust_array)

        self.impulse_array = getImpulseArray(self.thrust_array, self.thrust_dt)
        self.impulse_total = self.impulse_array[-1]
        self.prop_remaining_rate_array = 1.0 - (self.impulse_array / self.impulse_total)
        self.mass_prop_array = self.__mass_init * self.prop_remaining_rate_array
        self.MOI_prop_array = self.__MOI_init * np.resize(self.prop_remaining_rate_array, (self.thrust_n_samples, 3))

        self.thrust_f = interp1d(self.thrust_time_array, self.thrust_array)
        self.impulse_f = interp1d(self.thrust_time_array, self.impulse_array)
        self.mass_prop_f = interp1d(self.thrust_time_array, self.mass_prop_array)
        self.MOI_prop_f = interp1d(self.thrust_time_array, self.MOI_prop_array, axis=0)

    def thrust(self, t):
        if t >= self.thrust_cutoff_time:
            return 0.0
        else:
            return self.thrust_f(t)

    def impulse(self, t):
        if t >= self.thrust_cutoff_time:
            return self.impulse_total
        else:
            return self.impulse_f(t)

    def propMass(self, t):
        if t >= self.thrust_cutoff_time:
            return 0.0
        else:
            return self.mass_prop_f(t)

    def propMOI(self, t):
        if t >= self.thrust_cutoff_time:
            return np.zeros((3))
        else:
            return self.MOI_prop_f(t)


def trimThrust(thrust_array, time_array, threshold_rate=0.01):
    t_startup, t_cutoff = getThrustEffectiveTimeBoundary(
                            thrust_array,
                            time_array,
                            threshold_rate
                        )
    
    mask1 = (time_array >= t_startup)
    mask2 = (time_array <= t_cutoff)

    trimmed_time_array = time_array[mask1 & mask2]
    trimmed_time_array -= t_startup
    trimmed_thrust_array = thrust_array[mask1 & mask2]
    return trimmed_time_array, trimmed_thrust_array


def getThrustEffectiveTimeBoundary(thrust_array, time_array, threshold_rate=0.01):
    th_max = np.max(thrust_array)
    threshold = th_max * threshold_rate
    effective_time_array = time_array[thrust_array >= threshold]
    startup_time = np.min(effective_time_array)
    cutoff_time = np.max(effective_time_array)
    return startup_time, cutoff_time


def getImpulseArray(thrust_array, dt):
    impulse_array = np.cumsum(thrust_array * dt)
    return impulse_array