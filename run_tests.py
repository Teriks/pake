import unittest

runner = unittest.TextTestRunner()
runner.run(unittest.defaultTestLoader.discover("tests"))