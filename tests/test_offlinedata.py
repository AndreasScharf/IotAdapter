import unittest
from iotadapter import interprete_offline_data

class TestofflineData(unittest.TestCase):


    def interprete_offline_data(self):
        
        self.assertIsInstance(interprete_offline_data)

'''
 

class TestDiv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # runs once for this TestCase
        cls.num = 10

    def setUp(self):
        # runs before each test
        self.den = 2

    def tearDown(self):
        # runs after each test
        self.den = None

    def test_div_ok(self):
        self.assertEqual(div(self.num, self.den), 5)

    def test_div_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            div(1, 0)

'''