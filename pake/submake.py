import subprocess
import sys
import os


class SubMakeException(Exception):
    pass


def _execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def run_script(script_path, *args):
    if os.path.exists(script_path):
        if not os.path.isfile(script_path):
            raise FileNotFoundError('"{script_path}" is not a file.'
                                    .format(script_path=script_path))
    else:
        raise FileNotFoundError('"{script_path}" does not exist.'
                                .format(script_path=script_path))

    try:

        str_filter_args = list(str(a) for a in args)
        work_dir = os.path.dirname(os.path.abspath(script_path))
        output = _execute([sys.executable, script_path, "-C", work_dir]+str_filter_args)
        for line in output:
            sys.stdout.write(line)
    except subprocess.CalledProcessError as err:
        raise SubMakeException(err.output)


