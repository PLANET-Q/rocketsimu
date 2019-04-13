import numpy as np
import scipy.interpolate as interpolate

class Wind:
    def __call__(self, h):
        return self.wind(h)
    
    def wind(self, h):
        return 0


class HybridWind(Wind):
    def __init__(
            self,
            wind0,
            wind1,
            kind='linear',
            border_height0=0.,
            border_height1=0.,
            weight0=0.,
            weight1=1.
        ):
        self.h1 = border_height1
        self.h0 = border_height0
        self.wind0 = wind0
        self.wind1 = wind1
        self.weight0 = weight0
        self.weight1 = weight1

        if kind == 'linear':
            pass
        else:
            raise ValueError('Invalid hybrid type "'+kind+'" was indicated.')
        
        self.kind = kind
    
    def __w(self, h):
        w0 = self.weight0
        w1 = self.weight1
        h0 = self.h0
        h1 = self.h1
        if self.kind == 'linear':
            if h < h0:
                return w0
            elif h < h1:
                w_trans = (w1 - w0) * (h - h0)/(h1 - h0) + w0
                return w_trans
            else:
                return w1

    def wind(self, h):
        return self.wind0(h) * (1.0 - self.__w(h)) + self.wind1(h) * self.__w(h)


class WindPower(Wind):
    def __init__(self, z0, n, wind_std):
        self.wind_std = np.array(wind_std)
        self.wind_direction = np.arctan2(-wind_std[0], -wind_std[1])
        self.n = n
        self.z0 = z0

    def wind(self, h):
        if h < 0.:
            h = 0.
        
        wind_vec = self.wind_std * (h / self.z0)**(1. / self.n)
        return wind_vec


class WindConstant(Wind):
    def __init__(self, wind=np.array([0., 0., 0.])):
        self.wind_std = np.array(wind)
    def wind(self, h):
        return self.wind_std


class WindForecast(Wind):
    def __init__(self, forecast_filename):
        input_data = np.loadtxt(forecast_filename, comments=['#','$','%'], delimiter=',')
        self.alt_axis = input_data[:, 0]
        self.wind_vec_array = input_data[:, 1:]
        self._w = interpolate.interp1d(self.alt_axis, self.wind_vec_array, axis=0)
    def wind(self, h):
        return self._w(h)


def createWind(wind_model, params_dict):
    '''
    create instance of Wind class.  
    INPUT
        wind_model: name of wind model.
            `constant`, `power` or `forecast` is currently available(v0.1.0).
        params_dict: dict of parameters that is needed for the model

        NOTE:ハイブリッド風モデルの場合、params_dictの2つのWindオブジェクトには以下の二種類の指定方法が利用できる
        {
            "wind0": <first wind model object>,
            "wind1": <second wind model object>,
            ...
        }
        or
        {
            "wind0": {
                "wind_model": "[type of first wind model]",
                "wind_parameters": {
                    [params dictionary of first wind model]
                    ...
                }
            },
            "wind1": {
                "wind_model": "[type of second wind model]",
                "wind_parameters": {
                    [params dictionary of second wind model]
                    ...
                }
            },
            ...
        }
    OUTPUT
        wind instance
    '''
    if wind_model == 'constant':
        return WindConstant(params_dict['wind_std'])
    elif wind_model == 'power':
        return WindPower(params_dict['z0'], params_dict['n'], params_dict['wind_std'])
    elif wind_model == 'forecast':
        return
        #return WindForecast()
    elif wind_model == 'hybrid':
        '''
        Hybridモデルで合成する2つの風モデル：wind0, wind1も
        ディクショナリ型での指定ができ、再帰的に風モデルのインスタンスを生成する。
        '''
        if type(params_dict['wind0']) is dict:
            w0_dict = params_dict['wind0']
            w0 = createWind(w0_dict['wind_model'], w0_dict['wind_parameters'])
        else:
            w0 = params_dict['wind0']
        
        if type(params_dict['wind1']) is dict:
            w1_dict = params_dict['wind1']
            w1 = createWind(w1_dict['wind_model'], w1_dict['wind_parameters'])
        else:
            w1 = params_dict['wind1']

        return HybridWind(w0,
                    w1,
                    params_dict['kind'],
                    params_dict['border_height0'],
                    params_dict['border_height1'],
                    params_dict['weight0'],
                    params_dict['weight1'])
    else:
        ValueError('Invalid wind model')


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    wind_direction = np.deg2rad(90.0)
    wind_std = np.array([-np.sin(wind_direction), -np.cos(wind_direction)])
    wind_power = WindPower(2, 14, wind_std)
    wind_fore = WindForecast()
    wind_hybrid = HybridWind(wind_power, wind_fore, border_height0=100., border_height1=200.)
    alt_axis = np.arange(0, 500)

    wind_array = np.zeros((len(alt_axis), 2))
    for i in range(len(alt_axis)):
        wind_array[i] = wind_hybrid(alt_axis[i])

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(wind_array[:, 0], wind_array[:, 1], alt_axis)
    ax.set_xlabel('u')
    ax.set_ylabel('v')
    ax.set_zlabel('altitude')
    fig.show()
    plt.show()