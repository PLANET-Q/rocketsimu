import numpy as np
import pandas as pd
from scipy import interpolate
import os
from scipy.interpolate import RectBivariateSpline
from scipy.interpolate import interp1d
from wind import Wind

class Air:
    def __init__(self, wind: Wind, T0=298.0, p0=1.013e5):
        self.wind = wind
        self.T0 = T0
        self.p0 = p0
    
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


class _StandardAeroCoeff:
    def __init__(self):
        self.Cd_amplitude=15.0

        '''
        基準となるCP値、Clalpha値、Cd値をファイルからロードして正規化する
        '''
        rootpath = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '../data'))
        CPloc_path = os.path.join(rootpath, 'CPloc.csv')
        Cd0_path = os.path.join(rootpath, 'Cd0.csv')
        Clalpha_path = os.path.join(rootpath, 'Clalpha.csv')

        # CPlocのロード
        try:
            df = pd.read_csv(CPloc_path, header=None, na_values='Mach/AOA')
        except FileNotFoundError:
            raise FileNotFoundError('CPloc file not found')
        Mach_array = np.array(df.iloc[1:,0])  # mach array
        AOA_array = np.array(df.iloc[0,1:]) * np.pi/180.  # AOA array (convert from deg to rad)

        # CP location 2D array (rows: Mach, columns: AOA)
        CP_array = np.array(df.iloc[1:,1:])
        self.CP_vs_MachAlpha = RectBivariateSpline(Mach_array, AOA_array, CP_array)

        # Cd0のロード
        try:
            data = np.loadtxt(Cd0_path, delimiter=',', comments='$')
        except FileNotFoundError:
            raise FileNotFoundError('Cd0 file ' + Cd0_path + 'was not found')
        
        self.Cd0_vs_Mach = interp1d(data[:, 0], data[:, 1], kind='linear')

        # Clalphaのロード
        try:
            data = np.loadtxt(Clalpha_path, delimiter=',', comments='$')
        except FileNotFoundError:
            raise FileNotFoundError('Clalpha file ' + Clalpha_path + 'was not found')
        
        self.Clalpha_vs_Mach = interp1d(data[:, 0], data[:, 1], kind='linear')

    def CP(self, mach, AoA, scale=1.0):
        return float(self.CP_vs_MachAlpha(mach, AoA)) * scale
    
    def Clalpha(self, mach, scale=1.0):
        return self.Clalpha_vs_Mach(mach) * scale
    
    def Cd0(self, mach, scale=1.0):
        return self.Cd0_vs_Mach(mach) * scale
    
    def Cl(self, mach, AoA, Clalpha_scale=1.0):
        Clalpha = self.Clalpha(mach, Clalpha_scale)
        
        '''
        self.f_cl_alpha(Mach) = slope near AOA=0
        shape will be lile sin(2*alpha), which means Cl=0 at 90deg
        therefore, multiply 0.5 to realized the shape sin(2*alpha) as well as slope|AOA=0 = Cl_alpha
        '''
        _Cl = Clalpha * 0.5 * np.sin(2*AoA)
        return _Cl

    def Cd(self, mach, AoA, Cd0_scale=1.0):
        Cd0 = self.Cd0(mach, Cd0_scale)
        _Cd = Cd0 + self.Cd_amplitude * (np.cos(2*AoA + np.pi) + 1.0)
        return _Cd

standard_aero_coeff = _StandardAeroCoeff()