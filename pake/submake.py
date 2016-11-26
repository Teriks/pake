import subprocess
import sys
import os


class SubMakeException(Exception):
    pass


def run_script(script_path, *args):
    if os.path.exists(script_path):
        if not os.path.isfile(script_path):
            raise FileNotFoundError('{script_path} is not a file.'
                                    .format(script_path=script_path))
    else:
        raise FileNotFoundError('{script_path} does not exist.'
                                .format(script_path=script_path))

    try:
        str_filter_args = list(str(a) for a in args)
        subprocess.check_output([sys.executable, script_path]+str_filter_args,
                                stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as err:
        raise SubMakeException(err.output)
