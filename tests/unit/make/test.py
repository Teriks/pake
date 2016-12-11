import unittest
import pake.make


def test_target_1(self):
    pass


def test_target_2(self):
    pass


def test_target_3(self):
    pass


class MakeTests(unittest.TestCase):
    def test_resolve_targets_guards(self):
        make = pake.make.Make()

        make.add_target(test_target_1, [])
        make.add_target(test_target_2, [test_target_1])

        with self.assertRaises(pake.UndefinedTargetException):
            # because test_target_3 is not defined yet
            make.resolve_targets([test_target_1, test_target_2, test_target_3])

        with self.assertRaises(pake.UndefinedTargetException):
            # same as above except the undefined target is a string
            make.resolve_targets([test_target_1, test_target_2, "test_target_3"])

        with self.assertRaises(ValueError):
            # because a list element that was not a function or a string
            # was encountered
            print(make.resolve_targets([("test",)]))

    def test_add_target_guards(self):
        make = pake.make.Make()

        with self.assertRaises(pake.UndefinedTargetException):
            # Because test_target_1 was not previously defined,
            # which happens to catch the case of targets depending on
            # themselves
            make.add_target(test_target_1, depends=[test_target_1])

        with self.assertRaises(pake.UndefinedTargetException):
            # Same as above really, test_target_2 was never added as a target
            make.add_target(test_target_1, depends=[test_target_2])

        with self.assertRaises(pake.UndefinedTargetException):
            # Won't work with a string either, though the exception
            # will be on "test_target_1" since it is seen first.
            make.add_target(test_target_1, depends=["test_target_1", "test_target_2"])

        # There should be no targets defined after handling the cases above
        self.assertTrue(len(make.get_all_targets()) == 0)

        # actually add a target
        make.add_target(test_target_1, [])

        # make sure it is there
        self.assertTrue(len(make.get_all_targets()) == 1)

        # add another target
        make.add_target(test_target_2, [test_target_1])

        self.assertTrue(len(make.get_all_targets()) == 2)

        # try adding a duplicate
        with self.assertRaises(pake.TargetRedefinedException):
            make.add_target(test_target_1)

        # make sure it was not added
        self.assertTrue(len(make.get_all_targets()) == 2)
