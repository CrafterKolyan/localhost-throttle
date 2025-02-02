import subprocess

from ..util import is_windows

if is_windows():
  import win32api


def run_with_ctrl_handler(*arguments):
  if is_windows():
    win32api.SetConsoleCtrlHandler(None, False)
  subprocess.run(arguments)
