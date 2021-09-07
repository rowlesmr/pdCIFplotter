from unittest import TestCase
from src import main

class Test(TestCase):
    def test_cifstr_to_double_tuple(self):
        self.assertEqual(main.cifstr_to_double_tuple("0.01(2)"), (0.01,0.02))
        self.assertEqual(main.cifstr_to_double_tuple("0.01(20)"), (0.01,0.2))
        self.assertEqual(main.cifstr_to_double_tuple("0.010(20)"), (0.01,0.02))
        self.assertEqual(main.cifstr_to_double_tuple("0.010(23)"), (0.01,0.023))
        self.assertEqual(main.cifstr_to_double_tuple("1.0(2)"), (1.0,0.2))
        self.assertEqual(main.cifstr_to_double_tuple("1.(2)"), (1.0,2.0))
        self.assertEqual(main.cifstr_to_double_tuple("1(2)"), (1.0,2.0))
        self.assertEqual(main.cifstr_to_double_tuple("1(23)"), (1.0,23.0))
        self.assertEqual(main.cifstr_to_double_tuple("10.0(2)"), (10.0,0.2))
        self.assertEqual(main.cifstr_to_double_tuple("10.0(23)"), (10.0,2.3))
        self.assertEqual(main.cifstr_to_double_tuple("100(2)"), (100.0,2.0))
        self.assertEqual(main.cifstr_to_double_tuple("100(23)"), (100,23.0))
        self.assertEqual(main.cifstr_to_double_tuple("100.(23)"), (100.0,23.0))

