import os
import unittest


def main():
  dir = os.path.dirname(__file__)
  testsuite = unittest.TestLoader().discover(dir)
  unittest.TextTestRunner(verbosity=1).run(testsuite)
