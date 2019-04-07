import unittest
from rocketsimu import air
import math

class TestAir(unittest.TestCase):
    def setUp(self):
        # procedures before every tests are started.
        # This code block is executed every time
        pass

    def tearDown(self):
        # procedures after every tests are finished. 
        # This code block is executed every time
        pass

    def test_standard_CP(self):
        # one test case. here. 
        # You must “test_” prefix always. Unless, unittest ignores
        self.assertEqual(
            air.standard_aero_coeff.CP(0.3, 2*math.pi/180.0),
            1.0
            )
    
    def test_standard_Cd0(self):
        self.assertEqual(
            air.standard_aero_coeff.Cd0(0.0),
            1.0
            )
    
    def test_standard_Clalpha(self):
        self.assertEqual(
            air.standard_aero_coeff.Clalpha(0.0),
            1.0
            )


if __name__ == '__main__':
    unittest.main()