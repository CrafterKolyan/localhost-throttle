import localhost_throttle

from ..util import is_windows

if is_windows():
  import win32api


def localhost_throttle_with_ctrl_handler():
  if is_windows():
    win32api.SetConsoleCtrlHandler(None, False)
  localhost_throttle.main()
