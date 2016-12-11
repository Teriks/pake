import unittest
import pake.make


def test_target_1(self):
    pass


def test_target_2(self):
    pass


def test_target_3(self):
    pass


def test_target_4(self):
    pass


class MakeTests(unittest.TestCase):
    def test_get_target(self):
        make = pake.make.Make()
        make.add_target(test_target_3)

        make.add_target(test_target_1,
                        inputs="a",
                        outputs="a.o",
                        depends=test_target_3)

        make.add_target(test_target_2,
                        inputs=["d", "e", "f"],
                        outputs=["d.o", "e.o", "f.o"],
                        depends=[test_target_1, test_target_3])

        with self.assertRaises(pake.UndefinedTargetException):
            make.get_target(test_target_4)

        with self.assertRaises(pake.UndefinedTargetException):
            make.get_target("test_target_4")

        with self.assertRaises(ValueError):
            # something other than a string or function reference
            make.get_target(3)

        target = make.get_target("test_target_2")
        self.assertEqual(target.function, test_target_2)
        self.assertListEqual(list(target.inputs), ["d", "e", "f"])
        self.assertListEqual(list(target.outputs), ["d.o", "e.o", "f.o"])
        self.assertListEqual(list(target.dependency_outputs), ["a.o"])
        self.assertListEqual(list(target.dependencies), [test_target_1, test_target_3])

        target = make.get_target("test_target_1")
        self.assertEqual(target.function, test_target_1)
        self.assertListEqual(list(target.inputs), ["a"])
        self.assertListEqual(list(target.outputs), ["a.o"])
        self.assertListEqual(list(target.dependency_outputs), [])
        self.assertListEqual(list(target.dependencies), [test_target_3])

    def test_resolve_targets(self):
        make = pake.make.Make()
        make.add_target(test_target_1)
        make.add_target(test_target_2)
        make.add_target(test_target_3)

        self.assertEqual(make.target_count(), 3)
        self.assertEqual(len(make.get_all_targets()), 3)

        resolve = make.resolve_targets([test_target_1, "test_target_2", test_target_3])
        self.assertListEqual([test_target_1, test_target_2, test_target_3], resolve)

        resolve = make.resolve_targets(["test_target_2", "test_target_1", test_target_3])
        self.assertListEqual([test_target_2, test_target_1, test_target_3], resolve)

    def test_resolve_targets_guards(self):
        make = pake.make.Make()

        make.add_target(test_target_1)
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
        self.assertEqual(len(make.get_all_targets()), 0)
        self.assertEqual(make.target_count(), 0)

        # actually add a target
        make.add_target(test_target_1)

        # make sure it is there
        self.assertEqual(len(make.get_all_targets()), 1)
        self.assertEqual(make.target_count(), 1)

        # add another target
        make.add_target(test_target_2, [test_target_1])

        self.assertEqual(len(make.get_all_targets()), 2)
        self.assertEqual(make.target_count(), 2)

        # try adding a duplicate
        with self.assertRaises(pake.TargetRedefinedException):
            make.add_target(test_target_1)

        # make sure it was not added
        self.assertEqual(len(make.get_all_targets()), 2)
        self.assertEqual(make.target_count(), 2)

        make.clear_targets()

        self.assertEqual(len(make.get_all_targets()), 0)
        self.assertEqual(make.target_count(), 0)
