import unittest
from rocketsimu import wind
import numpy as np
import os

class TestLPF(unittest.TestCase):
    def setUp(self):
        # procedures before every tests are started.
        # This code block is executed every time
        pass

    def tearDown(self):
        # procedures after every tests are finished. 
        # This code block is executed every time
        pass

    def testForecastFileLoading(self):
        rootpath = os.path.abspath(os.path.dirname(__file__))
        thrust_path = os.path.join(rootpath, 'sample_wind.csv')
        windfore = wind.WindForecast(thrust_path)
        alt_axis_shape = windfore.alt_axis.shape
        wind_vec_shape = windfore.wind_vec_array.shape
        self.assertTupleEqual(wind_vec_shape, (16, 3))
        self.assertTupleEqual(alt_axis_shape, (16,))
    
    def testCreateHybridWind(self):
        params_dict = {
            'wind0': {
                'wind_model': 'constant',
                'wind_parameters':{
                    'wind_std': [0.0, 0.0, 1.0] 
                }
            },
            'wind1':{
                'wind_model': 'constant',
                'wind_parameters':{
                    'wind_std': [1.0, 0.0, 0.0] 
                }
            },
            'kind': 'linear',
            'border_height0': 100,
            'border_height1': 200,
            'weight0': 0.5,
            'weight1': 1.0
        }
        wind_hybrid = wind.createWind('hybrid', params_dict)
        self.assertEqual((wind_hybrid(0) == np.array([0.5, 0.0, 0.5])).all(), True)
        self.assertEqual((wind_hybrid(99.9) == np.array([0.5, 0.0, 0.5])).all(), True)
        self.assertEqual((wind_hybrid(150) == np.array([0.75, 0.0, 0.25])).all(), True)
        self.assertEqual((wind_hybrid(200.1) == np.array([1.0, 0.0, 0.0])).all(), True)

if __name__ == '__main__':
    unittest.main()