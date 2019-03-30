import numpy as np
import pandas as pd
from scipy import interpolate
from wind import Wind

class Air:
    def __init__(self, wind: Wind, T0=298.0, p0=1.013e5):
        self.wind = wind
        self.T0 = T0
        self.p0 = p0
        self.Cd0_scale = 1.0
        self.Clalpha_scale = 1.0
        self.Cd_amplitude = 15.0

    def loadCd0(self, filename):
        '''
        マッハ数に対する、迎角0deg時の抗力係数値をファイルからロード  
        ファイル形式例：
            $ Mach, Cd0 ($:コメントアウト)
            0.0, 0.5
            0.1, 0.692871059
            ...

        NOTE: マッハ数毎に求めるのが困難であれば
        `Cd0.csv` に基準となる Cd0 vs Mach値が用意されているので
        mach 0時のCd0のみ求めて、基準値をスケーリングすれば近似できる  
        スケーリングは `Air.setCd0Scale` より行える
        '''

        try:
            data = np.loadtxt(filename, delimiter=',', comments='$')
        except FileNotFoundError:
            raise FileNotFoundError('Cd0 file ' + filename + 'was not found')
        
        self.Cd0_vs_Mach = interpolate.interp1d(data[:, 0], data[:, 1], kind='linear')
    
    def loadClalpha(self, filename):
        '''
        マッハ数に対する、揚力傾斜値をファイルからロード  
        揚力傾斜については検索してください

        ファイル形式例：
            $ Mach, Clalpha ($:コメントアウト)
            0.0, 0.5
            0.1, 0.692871059
            ...

        NOTE: マッハ数毎に求めるのが困難であれば
        `Clalpha.csv` に基準となる Clalpha vs Mach値が用意されているので
        mach 0時のCd0のみ求めて、基準値をスケーリングすれば近似できる  
        スケーリングは `Air.setClalphaScale`より行える
        '''

        try:
            data = np.loadtxt(filename, delimiter=',', comments='$')
        except FileNotFoundError:
            raise FileNotFoundError('Clalpha file ' + filename + 'was not found')
        
        self.Clalpha_vs_Mach = interpolate.interp1d(data[:, 0], data[:, 1], kind='linear')
    
    def loadCP(self, filename):
        '''
        マッハ数、仰角に対する圧力中心値をファイルからロード

        ファイル形式例：
            $ Mach, Clalpha ($:コメントアウト)
            0.0, 0.5
            0.1, 0.692871059
            ...

        NOTE: マッハ数毎に求めるのが困難であれば
        `CPloc.csv` に基準となる CPloc vs Mach,Alpha 値が用意されているので
        基準値をスケーリングすれば近似できる  
        スケーリングは `Air.setCPScale`より行える
        '''
        try:
            df = pd.read_csv(filename, header=None, na_values='Mach/AOA')
        except FileNotFoundError:
            raise FileNotFoundError('CPloc file not found')
        Mach_array = np.array(df.iloc[1:,0])  # mach array
        AOA_array = np.array(df.iloc[0,1:]) * np.pi/180.  # AOA array (convert from deg to rad)

        # CP location 2D array (rows: Mach, columns: AOA)
        CP_array = np.array(df.iloc[1:,1:])
        self.CP_vs_MachAlpha = interpolate.RectBivariateSpline(Mach_array, AOA_array, CP_array)
        
    def scalingCd0(self, Cd0, mach=0.0):
        self.Cd0_scale = Cd0 / self.Cd0_vs_Mach(mach)
    
    def scalingClalpha(self, Clalpha, mach=0.0):
        self.Clalpha_scale = Clalpha / self.Clalpha_vs_Mach(mach)
    
    def scalingCP(self, CP, mach=0.3, AoA_deg=2.0):
        self.CP_scale = CP / float(self.CP_vs_MachAlpha(mach, AoA_deg*np.pi/180.0))


    def getCd(self, mach, alpha):
        Cd0 = self.Cd0_vs_Mach(mach) * self.Cd0_scale
        Cd = Cd0 + self.Cd_amplitude * (np.cos(2*alpha + np.pi) + 1.0)
        return Cd
    
    def getCl(self, mach, alpha):
        Clalpha = self.Clalpha_vs_Mach(mach) * self.Clalpha_scale

        '''
        self.f_cl_alpha(Mach) = slope near AOA=0
        shape will be lile sin(2*alpha), which means Cl=0 at 90deg
        therefore, multiply 0.5 to realized the shape sin(2*alpha) as well as slope|AOA=0 = Cl_alpha
        '''
        Cl = Clalpha * 0.5 * np.sin(2*alpha)
        return Cl

    def getCP(self, mach, alpha):
        CP = float(self.CP_vs_MachAlpha(mach, alpha)) * self.CP_scale
        return CP
    
    def standard_air(self, h):
        '''
        returns air property given an altitude  
        INPUT: h = altitude [m]
        '''

        # gas constant
        R = 287.15  # [J/kg.K]
        # gravitational accel.
        g = 9.81  # [m/s^2]

        if h <= 11.*10**3:
            # *** Troposphere ***
            # temperature lapse rate
            gamma = -0.0065
            # temperature[K]
            T = self.T0 + gamma * h
            # pressure[Pa]
            p = self.p0 * (T / self.T0)**(-g / (gamma*R))

        elif h <= 20.*10**3:
            # *** Tropopause ***
            # temperature is const at 11km-20km
            # p11 = pressure at 11km alt.
            T,p11,_,_ = self.standard_air(11000.)
            # pressure
            p = p11 * np.exp( (-g/(R*T)) * (h-11000.) )

        elif h <= 32.*10**3:
            # *** Stratosphere 1 ***
            # temp, pressure at 20km alt.
            T20,p20,_,_ = self.standard_air(20000.)
            # temperature lapse rate
            gamma = 0.001
            # temperature
            T = T20 + gamma * (h-20000.) # [K]
            #pressure
            p = p20 * (T/T20)**(-g/(gamma*R)) #[Pa]

        elif h <= 47.*10**3:
            # *** Stratosphere 2 ***
            # temp, pressure at 32km alt.
            T32,p32,_,_ = self.standard_air(32000.)
            # temperature lapse rate
            gamma = 0.0028
            # temperature
            T = T32 + gamma * (h-32000.) # [K]
            #pressure
            p = p32 * (T/T32)**(-g/(gamma*R)) #[Pa]

        elif h <= 51.*10**3:
            # *** Stratopause ***
            # temp, pressure at 47km alt.
            T,p47,_,_ = self.standard_air(47000.)
            # pressure
            p = p47 * np.exp( (-g/(R*T)) * (h-47000.) )

        elif h <= 71.*10**3:
            # *** Mesosphere 1 ***
            # temp, pressure at 51km alt.
            T51,p51,_,_ = self.standard_air(51000.)
            # temperature lapse rate
            gamma = -0.0028
            # temperature
            T = T51 + gamma * (h-51000.) # [K]
            #pressure
            p = p51 * (T/T51)**(-g/(gamma*R)) #[Pa]

        elif h <= 85.*10**3:
            # *** Mesosphere 2 ***
            # temp, pressure at 71km alt.
            T71,p71,_,_ = self.standard_air(71000.)
            # temperature lapse rate
            gamma = -0.002
            # temperature
            T = T71 + gamma * (h-71000.) # [K]
            #pressure
            p = p71 * (T/T71)**(-g/(gamma*R)) #[Pa]

        elif h <= 90.*10**3:
            # *** Mesopause ***
            # temp, pressure at 47km alt.
            T,p85,_,_ = self.standard_air(85000.)
            # pressure
            p = p85 * np.exp( (-g/(R*T)) * (h-85000.) )

        elif h <= 110.*10**3:
            # *** Thermosphere  ***
            # temp, pressure at 51km alt.
            T90,p90,_,_ = self.standard_air(90000.)
            # temperature lapse rate
            gamma = 0.0026675
            # temperature
            T = T90 + gamma * (h-90000.) # [K]
            #pressure
            p = p90 * (T/T90)**(-g/(gamma*R)) #[Pa]

        else:
            T110,p110,_,_ = self.standard_air(110000.)
            T = T110
            p = p110

        #END IF

        # density
        rho = p/(R*T) #[kg/m^3]

        # acoustic speed
        a = np.sqrt(1.4*R*T) # [m/s]

        return T,p,rho,a