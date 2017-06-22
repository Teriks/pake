
import pake.util
import os

# init once for defines/exports, de_init before next init
# STDIN defines from pake.subpake are cached, pake.de_init
# does not clear them
defines = pake.init()

assert '__PAKE_SYNC_OUTPUT' in os.environ

expected_value = defines['SYNC_OUTPUT_EXPECTED_VALUE']

if defines.has_define('INIT_SYNC_OUTPUT_VALUE'):
    init_sync_output = defines['INIT_SYNC_OUTPUT_VALUE']

    pake.de_init()
    assert '__PAKE_SYNC_OUTPUT' not in os.environ

    pk = pake.init(sync_output=init_sync_output)
    assert '__PAKE_SYNC_OUTPUT' in os.environ

else:
    pake.de_init()
    assert '__PAKE_SYNC_OUTPUT' not in os.environ

    pk = pake.init()
    assert '__PAKE_SYNC_OUTPUT' in os.environ

if pk.sync_output != expected_value:
    raise Exception('pk.sync_output was {}, expected {}!'.format(pk.sync_output, expected_value))
