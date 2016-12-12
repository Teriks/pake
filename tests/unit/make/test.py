import unittest
import threading
import time
import sys
import io
import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake.make


def test_target_1(self):
    pass


def test_target_2(self):
    pass


def test_target_3(self):
    pass


def test_target_4(self):
    pass


def test_target_5(self):
    pass


class MakeTests(unittest.TestCase):
    def test_execute_order_parallel(self):
        target_order = []

        def target_1():
            target_order.append(target_1)

        def target_2():
            target_order.append(target_2)

        def target_3():
            target_order.append(target_3)

        def target_4():
            target_order.append(target_4)

        def target_5():
            target_order.append(target_5)

        make = pake.make.Make()

        make.add_target(target_5)
        make.add_target(target_1, depends=[target_5])
        make.add_target(target_2, depends=[target_1])
        make.add_target(target_3, depends=[target_2])

        # Having 2 and 5 as a dependency here, when it is already the dependency of
        # 3 and 1 respectively, should not affect the execution order
        make.add_target(target_4, depends=[target_3, target_2, target_5])

        # Specifying multiple times, or specifying an indirect dependency
        # of a target that has already been specified should not change the
        # order of target execution.
        make.set_run_targets(["target_4", target_4, target_2])

        # For making pake.make.Make() shut up
        # need to make that configurable

        save_stdout = sys.stdout
        sys.stdout = io.StringIO()

        make.execute()

        sys.stdout = save_stdout

        # 5 and 1 should come in a deterministic order, because they are
        # leaf dependencies that are specified in order in the set_run_targets call
        self.assertEqual(target_order,
                         [target_5,
                          target_1,
                          target_2,
                          target_3,
                          target_4])

        target_order.clear()

        def visitor(x):
            target_order.append(x.function)

        sys.stdout = io.StringIO()
        # Test visit as well
        make.visit(visitor)

        sys.stdout = save_stdout

        self.assertEqual(target_order,
                         [target_5,
                          target_1,
                          target_2,
                          target_3,
                          target_4])

        target_order.clear()

        sys.stdout = save_stdout

    def test_execute_order(self):
        target_order = []
        target_order_lock = threading.RLock()

        def target_1():
            time.sleep(0.3)
            with target_order_lock:
                target_order.append(target_1)

        def target_2():
            with target_order_lock:
                target_order.append(target_2)

        def target_3():
            with target_order_lock:
                target_order.append(target_3)

        def target_4():
            with target_order_lock:
                target_order.append(target_4)

        def target_5():
            time.sleep(0.3)
            with target_order_lock:
                target_order.append(target_5)

        make = pake.make.Make()
        make.set_max_jobs(10)

        make.add_target(target_5)
        make.add_target(target_1, depends=[target_5])
        make.add_target(target_2, depends=[target_1])
        make.add_target(target_3, depends=[target_2])

        # Having 2 and 5 as a dependency here, when it is already the dependency of
        # 3 and 1 respectively, should not affect the execution order
        make.add_target(target_4, depends=[target_3, target_2, target_5])

        # Specifying multiple times, or specifying an indirect dependency
        # of a target that has already been specified should not change the
        # order of target execution.
        make.set_run_targets(["target_4", target_4, target_2])

        # For making pake.make.Make() shut up
        # need to make that configurable

        save_stdout = sys.stdout
        sys.stdout = io.StringIO()

        make.execute()

        sys.stdout = save_stdout

        # 5 and 1 should come in a deterministic order, because they are
        # leaf dependencies that are specified in order in the set_run_targets call
        self.assertEqual(target_order,
                         [target_5,
                          target_1,
                          target_2,
                          target_3,
                          target_4])

        target_order.clear()

        def visitor(x):
            target_order.append(x.function)

        sys.stdout = io.StringIO()
        # Test visit as well
        make.visit(visitor)

        sys.stdout = save_stdout

        self.assertEqual(target_order,
                         [target_5,
                          target_1,
                          target_2,
                          target_3,
                          target_4])

        target_order.clear()

        sys.stdout = save_stdout

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
