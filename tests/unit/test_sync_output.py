import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.pake


class SyncOutputTest(unittest.TestCase):

    def test_specify_sync_output(self):
        # This test just makes sure the --sync-output
        # is correctly setting pake.Pake.sync_output
        # with respect to the environment and command line.

        # The command line option should override the environmental
        # variable PAKE_SYNC_OUTPUT

        # The value of option should be inherited by
        # subpake invocations in all cases.

        # The value of this option sync_output defaults to True

        #
        self._test_stub(call_init=False)
        self._test_stub(call_init=True)

    def _test_stub(self, call_init):

        # This clears any internal environmental
        # vars pake sets up, by default
        pake.de_init(clear_conf=False)

        assert_sync_output = os.path.join(script_dir, 'assert_sync_output.py')

        # os.environ['INIT_SYNC_OUTPUT_VALUE'], value is passed to pake.init(sync_output=..) in assert script
        # if the environmental variable is not set, no value is passed indicating no manual override to pake

        # os.environ['SYNC_OUTPUT_EXPECTED_VALUE']
        # The value of pake.Pake.sync_output must equal this value after pake.init, or the script will assert

        def set_init_sync_output_value(value):
            pake.export('INIT_SYNC_OUTPUT_VALUE', value)

        def del_init_sync_output_value():
            # Prevent passing to pake.init all together
            # the **kwargs argument will not be specified
            if 'INIT_SYNC_OUTPUT_VALUE' in pake.EXPORTS:
                del pake.EXPORTS['INIT_SYNC_OUTPUT_VALUE']

        def set_expected_value(value):
            pake.export('SYNC_OUTPUT_EXPECTED_VALUE', value)

        def del_expected_value():
            if 'SYNC_OUTPUT_EXPECTED_VALUE' in pake.EXPORTS:
                del pake.EXPORTS['SYNC_OUTPUT_EXPECTED_VALUE']

        def clean_env():
            pake.EXPORTS.clear()
            if 'PAKE_SYNC_OUTPUT' in os.environ:
                del os.environ['PAKE_SYNC_OUTPUT']

        def assert_subpake_success(*args, msg=None):
            try:
                pake.subpake(assert_sync_output, *args, call_exit=False)
            except pake.SubpakeException as err:
                err.write_info(sys.stderr)
                self.fail(msg=msg)

        def m_init():
            if call_init:
                pake.de_init(clear_conf=False)
                pake.init()

        # delete PAKE_SYNC_OUTPUT environmental variable, clear all pake.EXPORTS
        clean_env()

        # Test simple cases

        m_init()

        set_expected_value(True)
        assert_subpake_success(msg='pake.sync_output should default to true when PAKE_SYNC_OUTPUT and --sync-output not used.')

        m_init()

        set_expected_value(False)
        assert_subpake_success('--sync-output', False, msg='pake.sync_output did not match --sync-output=False.')

        m_init()

        set_expected_value(True)
        assert_subpake_success('--sync-output', True, msg='pake.sync_output did not match --sync-output=True.')

        m_init()

        set_expected_value(False)
        assert_subpake_success('--sync-output', 0, msg='pake.sync_output did not match --sync-output=0.')

        m_init()

        set_expected_value(True)
        assert_subpake_success('--sync-output', 1, msg='pake.sync_output did not match --sync-output=1.')

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success(msg='pake.sync_output did not match pake.init(sync-output=False).')

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success(msg='pake.sync_output did not match pake.init(sync-output=True).')

        m_init()

        set_init_sync_output_value(None)
        set_expected_value(True)
        assert_subpake_success(msg='pake.sync_output did not match pake.init(sync-output=None).'
                                   'None == unspecified, use default of True')

        # Test overriding the environment with --sync-output (the command line)
        # =====================================================================

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        del_init_sync_output_value()
        set_expected_value(True)
        assert_subpake_success('--sync-output', True,
                               msg='pake.sync_output --sync-output=True should override the environmental variable PAKE_SYNC_OUTPUT=0.')

        # Test override False ENV from command line with --sync-output=1

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        del_init_sync_output_value()
        set_expected_value(True)
        assert_subpake_success('--sync-output', 1,
                               msg='pake.sync_output --sync-output=1 should override the environmental variable PAKE_SYNC_OUTPUT=0.')

        # Test override True ENV from command line with --sync-output=False

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        del_init_sync_output_value()
        set_expected_value(False)
        assert_subpake_success('--sync-output', False,
                               msg='pake.sync_output --sync-output=False should override the environmental variable PAKE_SYNC_OUTPUT=1.')

        # Test override True ENV from command line with --sync-output=0

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        del_init_sync_output_value()
        set_expected_value(False)
        assert_subpake_success('--sync-output', 0,
                               msg='pake.sync_output --sync-output=0 should override the environmental variable PAKE_SYNC_OUTPUT=1.')

        clean_env()

        # Test overriding the command line from pake.init
        # ===============================================

        # Test override command line --sync-output=True with pake.init(sync_output=False)

        m_init()

        set_init_sync_output_value(False)  # set whats passed to pake.init
        set_expected_value(False)  # it should win against everything
        assert_subpake_success('--sync-output', True,
                               msg='setting pake.init(sync_output=...) should override --sync-output and the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test override command line --sync-output=False with pake.init(sync_output=True)

        m_init()

        set_init_sync_output_value(True)  # set whats passed to pake.init
        set_expected_value(True)  # it should win against everything
        assert_subpake_success('--sync-output', False,
                               msg='setting pake.init(sync_output=...) should override --sync-output and the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test override command line --sync-output=1 with pake.init(sync_output=False)

        m_init()

        set_init_sync_output_value(False)  # set whats passed to pake.init
        set_expected_value(False)  # it should win against everything
        assert_subpake_success('--sync-output', 1,
                               msg='setting pake.init(sync_output=...) should override --sync-output and the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test override command line --sync-output=0 with pake.init(sync_output=True)

        m_init()

        set_init_sync_output_value(True)  # set whats passed to pake.init
        set_expected_value(True)  # it should win against everything
        assert_subpake_success('--sync-output', 0,
                               msg='setting pake.init(sync_output=...) should override --sync-output and the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test that --sync-output=True is not overridden when pake.init(sync_output=None)

        m_init()

        set_init_sync_output_value(None)  # set whats passed to pake.init, None is the same as not specifying
        set_expected_value(True)  # it should win against everything
        assert_subpake_success('--sync-output', True,
                               msg='setting pake.init(sync_output=None) should NOT override --sync-output or the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test that --sync-output=False is not overridden when pake.init(sync_output=None)

        m_init()

        set_init_sync_output_value(None)  # set whats passed to pake.init, None is the same as not specifying
        set_expected_value(False)  # it should win against everything
        assert_subpake_success('--sync-output', False,
                               msg='setting pake.init(sync_output=None) should NOT override --sync-output or the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test that --sync-output=1 is not overridden when pake.init(sync_output=None)

        m_init()

        set_init_sync_output_value(None)  # set whats passed to pake.init, None is the same as not specifying
        set_expected_value(True)  # it should win against everything
        assert_subpake_success('--sync-output', 1,
                               msg='setting pake.init(sync_output=None) should NOT override --sync-output or the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        # Test that --sync-output=0 is not overridden when pake.init(sync_output=None)

        m_init()

        set_init_sync_output_value(None)  # set whats passed to pake.init, None is the same as not specifying
        set_expected_value(False)  # it should win against everything
        assert_subpake_success('--sync-output', 0,
                               msg='setting pake.init(sync_output=None) should NOT override --sync-output or the '
                                   'environmental variable PAKE_SYNC_OUTPUT.')

        clean_env()

        # Test overriding the environment with pake.init
        # ==============================================

        # Test override False ENV from command line with pake.init(sync_output=True)

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success(msg='pake.sync_output pake.init(sync_output=True) should override the environmental variable PAKE_SYNC_OUTPUT=0.')

        # Test override True ENV from command line with pake.init(sync_output=False)

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success(msg='pake.sync_output pake.init(sync_output=False) should override the environmental variable PAKE_SYNC_OUTPUT=1.')

        # Test that PAKE_SYNC_OUTPUT=1 is not overridden when pake.init(sync_output=None)

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(None)
        set_expected_value(True)
        assert_subpake_success(msg='pake.sync_output pake.init(sync_output=None) should NOT override the environmental variable PAKE_SYNC_OUTPUT=1.')

        # Test that PAKE_SYNC_OUTPUT=0 is not overridden when pake.init(sync_output=None)

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(None)
        set_expected_value(False)
        assert_subpake_success(msg='pake.sync_output pake.init(sync_output=None) should NOT override the environmental variable PAKE_SYNC_OUTPUT=0.')

        # Test that pake.init overrides both the environment and the command line
        # =======================================================================

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success('--sync-output', 0,
                               msg='pake.sync_output pake.init(sync_output=True) should override both --sync-output=0 and PAKE_SYNC_OUTPUT=0.')

        # Test override False ENV from command line with --sync-output=1

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success('--sync-output', False,
                               msg='pake.sync_output pake.init(sync_output=True) should override both --sync-output=False and PAKE_SYNC_OUTPUT=0.')

        # Test override True ENV from command line with --sync-output=False

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success('--sync-output', True,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=True and PAKE_SYNC_OUTPUT=1.')

        # Test override True ENV from command line with --sync-output=0

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success('--sync-output', 1,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=1 and PAKE_SYNC_OUTPUT=1.')

        clean_env()

        # Few mix matched tests with all three methods
        # of specifying sync_output present at the same time
        # ==================================================

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success('--sync-output', 0,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=0 and PAKE_SYNC_OUTPUT=1.')

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(False)
        set_expected_value(False)
        assert_subpake_success('--sync-output', 1,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=1 and PAKE_SYNC_OUTPUT=0.')

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success('--sync-output', 1,
                               msg='pake.sync_output pake.init(sync_output=True) should override both --sync-output=1 and PAKE_SYNC_OUTPUT=0.')

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(True)
        set_expected_value(True)
        assert_subpake_success('--sync-output', 0,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=0 and PAKE_SYNC_OUTPUT=1.')

        os.environ['PAKE_SYNC_OUTPUT'] = '1'

        m_init()

        set_init_sync_output_value(None)  # pake.init(sync_output=None)
        set_expected_value(False)  # Because the command line option overrides the environment
        assert_subpake_success('--sync-output', 0,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=0 and PAKE_SYNC_OUTPUT=1.')

        os.environ['PAKE_SYNC_OUTPUT'] = '0'

        m_init()

        set_init_sync_output_value(None)  # pake.init(sync_output=None)
        set_expected_value(True)  # Because the command line option overrides the environment
        assert_subpake_success('--sync-output', 1,
                               msg='pake.sync_output pake.init(sync_output=False) should override both --sync-output=0 and PAKE_SYNC_OUTPUT=1.')

        clean_env()
