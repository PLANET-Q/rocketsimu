import unittest
from rocketsimu import engine
import numpy as np

class TestEngine(unittest.TestCase):
    def setUp(self):
        # procedures before every tests are started.
        # This code block is executed every time
        self.dt = 0.01
        self.max_t = 10.0
        self.time_array = np.arange(0.0, self.max_t, self.dt)
        self.thrust_array = np.r_[
            np.zeros((int(3.0/self.dt))),
            np.linspace(0.0, 1000.0, int(4.0/self.dt), endpoint=False),
            np.linspace(1000.0, 0.0, int(2.0/self.dt), endpoint=False),
            np.zeros((int(1.0/self.dt)))
        ]

    def tearDown(self):
        # procedures after every tests are finished. 
        # This code block is executed every time
        pass

    def test_thrust_trimming(self):
        '''
        推力の立ち上がり/カットオフがうまくできるかのテスト
        '''

        # t_startup = 3.04, t_cutoff=8.98
        t_startup, t_cutoff = engine.getThrustEffectiveTimeBoundary(
                self.thrust_array,
                self.time_array,
                threshold_rate=0.01
            )
        
        self.assertAlmostEqual(t_startup, 3.04)
        self.assertAlmostEqual(t_cutoff, 8.98)
    
    def test_impluse(self):
        '''
        力積変化の妥当性を調べるテスト
        '''
        impulse_array = engine.getImpulseArray(self.thrust_array, self.dt)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 0.00]), 0.0)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 3.00]), 0.0)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 5.00]), 502.5)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 7.00]), 2005.0)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 8.00]), 2752.5)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 9.00]), 3000.0)
        self.assertAlmostEqual(float(impulse_array[self.time_array == 9.99]), 3000.0)


if __name__ == '__main__':
    unittest.main()