import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.graph
import pake.conf

from tests import open_devnull

pake.conf.stdout = open_devnull()
pake.conf.stderr = open_devnull()


class MultitaskAggregateExceptionTest(unittest.TestCase):
    def test_normal_exception(self):
        pake.de_init(clear_conf=False)

        pk = pake.init()

        class TestException(Exception):
            def __init__(self):
                pass

        def raise_test(unused):
            raise TestException()

        @pk.task
        def test_submit(ctx):
            with ctx.multitask() as mt:
                mt.submit(raise_test, None)

        @pk.task
        def test_map(ctx):
            with ctx.multitask() as mt:
                mt.map(raise_test, range(0, 5))

        with self.assertRaises(pake.TaskException) as te:
            pk.run(tasks=test_submit)

        self.assertEqual(type(te.exception.exception), TestException)

        self.assertEqual(type(te.exception.exception), TestException,
                         msg='test_multitask_exceptions.py: ctx.multitask with mt.submit did '
                             'not propagate the correct exception type, expected '
                             '"TestException", got "{}"'
                         .format(type(te.exception.exception)))

        with self.assertRaises(pake.TaskException) as te:
            pk.run(tasks=test_map)

        self.assertEqual(type(te.exception.exception), TestException,
                         msg='test_multitask_exceptions.py: ctx.multitask with mt.map did '
                             'not propagate the correct exception type, expected '
                             '"TestException", got "{}"'
                         .format(type(te.exception.exception)))

    def test_aggregate_exception(self):
        pake.de_init(clear_conf=False)

        pk = pake.init()

        class TestException(Exception):
            def __init__(self, exc_id):
                self.exc_id = exc_id

        def raise_test(exc_id):
            raise TestException(exc_id)

        test_submit_exc_count = 5
        test_map_exc_count = 7

        @pk.task
        def test_submit(ctx):

            # Throw some extra tasks in

            with ctx.multitask() as mt:
                mt.aggregate_exceptions = True

                for i in range(0, 10):
                    if i < test_submit_exc_count:
                        mt.submit(raise_test, i)
                    else:
                        mt.submit(lambda: None)

        @pk.task
        def test_map(ctx):

            # Test that the map function of the executor
            # aggregates exceptions.  It is just using .submit
            # under the hood so it should be fine, test anyway

            with ctx.multitask(aggregate_exceptions=True) as mt:
                arguments = range(0, 18)

                def should_raise(argument):
                    if argument < test_map_exc_count:
                        raise_test(argument)

                mt.map(should_raise, arguments)

        # Assert that the correct amount of exceptions
        # were raised, and that their ID's were unique

        def all_unique(x):
            seen = set()
            return not any(i in seen or seen.add(i) for i in x)

        def assert_exception_count(task, count, jobs):
            task_name = pk.get_task_name(task)
            try:
                pk.run(tasks=task, jobs=jobs)
            except pake.TaskException as err:

                if isinstance(err.exception, pake.AggregateException):
                    aggregate = err.exception

                    self.assertEqual(len(aggregate.exceptions), count,
                                     msg='test_multitask_exceptions.py: Task Name: "{}", Expected {} '
                                         'exceptions to have been aggregated, got: {}'
                                     .format(task_name, count,
                                             len(aggregate.exceptions)))

                    self.assertTrue(all_unique(i.exc_id for i in aggregate.exceptions),
                                    msg='test_multitask_exceptions.py: Task Name: "{}", aggregate '
                                        'exception contained the same exception more than once.'
                                    .format(task_name))

                    # test for exceptions

                    aggregate.write_info()

                else:
                    self.fail(msg='test_multitask_exceptions.py: Task Name: "{}", Expected a '
                                  'pake.AggregateException to be raised, got: {}'
                              .format(task_name, err.exception))

            else:
                self.fail(msg='test_multitask_exceptions.py: Task Name: "{}", Expected '
                              'pake.AggregateException to be raised and cause a pake.TaskException'
                          .format(task_name))

        assert_exception_count(test_submit, 5, jobs=1)
        assert_exception_count(test_map, 7, jobs=1)

        assert_exception_count(test_submit, 5, jobs=10)
        assert_exception_count(test_map, 7, jobs=10)
