import numpy as np


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
        self.wind_std = wind
    def wind(self, h):
        return self.wind_std


class WindForecast(Wind):
    def wind(self, h):
        return 0
    pass


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