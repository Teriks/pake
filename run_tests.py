import unittest

runner = unittest.TextTestRunner()
exit(not runner.run(unittest.defaultTestLoader.discover("tests")).wasSuccessful())
