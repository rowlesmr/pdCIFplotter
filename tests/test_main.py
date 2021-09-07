from unittest import TestCase
from src import main
import numpy as np


class Test(TestCase):

    def test_cifstr_to_double(self):
        self.assertEqual(main.cifstr_to_double("."), 0.0)
        self.assertEqual(main.cifstr_to_double("?"), 0.0)
        self.assertEqual(main.cifstr_to_double("0.01(2)"), 0.01)
        self.assertEqual(main.cifstr_to_double("0.01(20)"), 0.01)
        self.assertEqual(main.cifstr_to_double("0.010"), 0.01)
        self.assertEqual(main.cifstr_to_double("10."), 10.0)

    def test_cifstr_to_double_tuple(self):
        self.assertEqual(main.cifstr_to_double_tuple("."), (0.0, 0.0))
        self.assertEqual(main.cifstr_to_double_tuple("?"), (0.0, 0.0))
        self.assertEqual(main.cifstr_to_double_tuple("0.01(2)"), (0.01, 0.02))
        self.assertEqual(main.cifstr_to_double_tuple("0.01(20)"), (0.01, 0.2))
        self.assertEqual(main.cifstr_to_double_tuple("0.010(20)"), (0.01, 0.02))
        self.assertEqual(main.cifstr_to_double_tuple("0.010(23)"), (0.01, 0.023))
        self.assertEqual(main.cifstr_to_double_tuple("1.0(2)"), (1.0, 0.2))
        self.assertEqual(main.cifstr_to_double_tuple("1.(2)"), (1.0, 2.0))
        self.assertEqual(main.cifstr_to_double_tuple("1(2)"), (1.0, 2.0))
        self.assertEqual(main.cifstr_to_double_tuple("1(23)"), (1.0, 23.0))
        self.assertEqual(main.cifstr_to_double_tuple("10.0(2)"), (10.0, 0.2))
        self.assertEqual(main.cifstr_to_double_tuple("10.0(23)"), (10.0, 2.3))
        self.assertEqual(main.cifstr_to_double_tuple("100(2)"), (100.0, 2.0))
        self.assertEqual(main.cifstr_to_double_tuple("100(23)"), (100, 23.0))
        self.assertEqual(main.cifstr_to_double_tuple("100.(23)"), (100.0, 23.0))

    def test_cifstrlist_to_nparray_errs(self):
        array = np.array([[1, 2, 3], [0.1, 0.0, 0.3]])
        cifstr = ["1.0(1)", "2", "3.00(30)"]
        np.testing.assert_array_equal(main.cifstrlist_to_nparray_errs(cifstr), array)

    def test_cifstrlist_to_nparray_noerrs(self):
        array = np.array([1, 2, 3])
        cifstr = ["1.0(1)", "2", "3.00(30)"]
        np.testing.assert_array_equal(main.cifstrlist_to_nparray_noerrs(cifstr), array)

    def test_convert_2theta_to_q(self):
        array_q = np.array([0.7107461352, 0.7142907725, 0.7178352737, 0.7213796383])
        array_2th = np.array([10.0, 10.05, 10.10, 10.15])
        lam = 1.54096
        np.testing.assert_almost_equal(main.convert_2theta_to_q(array_2th, lam), array_q)

    def test_convert_2theta_to_d(self):
        array_d = np.array([8.8402665815,8.7963971386,8.7529626044,8.7099565517])
        array_2th = np.array([10.0, 10.05, 10.10, 10.15])
        lam = 1.54096
        np.testing.assert_almost_equal(main.convert_2theta_to_d(array_2th, lam), array_d)
