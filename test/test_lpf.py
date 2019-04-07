import unittest
from rocketsimu.lpf import LPF
import numpy as np
from scipy.fftpack import fft, fftfreq

class TestLPF(unittest.TestCase):
    def setUp(self):
        # procedures before every tests are started.
        # This code block is executed every time
        pass

    def tearDown(self):
        # procedures after every tests are finished. 
        # This code block is executed every time
        pass

    def test_lpf(self):
        dt = 0.01
        x = np.arange(0., 10.0, dt)
        y = np.sin(2*x)+np.sin(4*x)+np.sin(6*x)+np.sin(10*x)
        lpf_10 = LPF(y, dt, 10.0)
        lpf_8 = LPF(y, dt, 8.0)

        spectrum_10 = fft(lpf_10)
        freq_10 = fftfreq(len(spectrum_10), d=dt)
        mask_10 = np.round(spectrum_10[(abs(freq_10) >= 10.0)], 7) == 0.0

        spectrum_8 = fft(lpf_8)
        freq_8 = fftfreq(len(spectrum_8), d=dt)
        mask_8 = np.round(spectrum_8[(abs(freq_8) >= 8.0)], 7) == 0.0
        self.assertEqual(mask_10.all(), True)
        self.assertEqual(mask_8.all(), True)

if __name__ == '__main__':
    unittest.main()