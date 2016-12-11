import unittest
import pake.make

target_order = []


def test_target_1(self):
    target_order.append(test_target_1)


def test_target_2(self):
    target_order.append(test_target_2)


def test_target_3(self):
    target_order.append(test_target_3)


def test_target_4(self):
    target_order.append(test_target_4)


def test_target_5(self):
    target_order.append(test_target_5)


class MakeTests(unittest.TestCase):

    def text_execute_order(self):
        make = pake.make.Make()

        make.add_target(test_target_5)
        make.add_target(test_target_1)
        make.add_target(test_target_2, depends=[test_target_1])
        make.add_target(test_target_3, depends=[test_target_2])

        # Having 2 as a dependency here, when it is already the dependency of
        # 3 should not affect the execution order
        make.add_target(test_target_4, depends=[test_target_3, test_target_2])

        make.set_run_targets(["test_target_5", test_target_1, test_target_4])
        make.execute()

        # 5 and 1 should come in a deterministic order, because they are
        # leaf dependencies that are specified in order in the set_run_targets call

        self.assertEqual(target_order,
                         [test_target_5,
                          test_target_1,
                          test_target_2,
                          test_target_3,
                          test_target_4])

        target_order.clear()

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

        with self.assertRaises(ValueError):
            # Expects a function reference
            make.add_target(target_function="test")

        with self.assertRaises(ValueError):
            # depends contains something other than a
            # function reference or string
            make.add_target(test_target_1, depends=[0])

        self.assertEqual(len(make.get_all_targets()), 0)
        self.assertEqual(make.target_count(), 0)
