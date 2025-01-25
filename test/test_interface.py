import contextlib
import time
import signal
import socket
import subprocess
import sys

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DEFAULT_CWD, MODULE_NAME, DELAY_TO_START_UP
from .util import spawn_localhost_throttle


def test_fails_with_no_arguments():
  process = subprocess.Popen(
    [sys.executable, "-m", MODULE_NAME],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=DEFAULT_CWD,
  )
  process.communicate()
  return_code = process.returncode
  assert return_code != 0, "Return code should not be 0 when run without arguments"


@pytest.mark.timeout(3)
def test_properly_starts_up():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      out_socket.bind(("localhost", 0))
      out_port = out_socket.getsockname()[1]
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([Protocol.TCP]))
  try:
    time.sleep(DELAY_TO_START_UP)
    with pytest.raises(subprocess.TimeoutExpired):
      process.communicate(timeout=1)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(sys.platform != "win32", reason="signal.CTRL_BREAK_EVENT exists only on Windows")
def test_can_be_killed_with_CTRL_BREAK_on_windows():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      out_socket.bind(("localhost", 0))
      out_port = out_socket.getsockname()[1]
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([Protocol.TCP]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.CTRL_BREAK_EVENT)
    process.communicate(timeout=0.3)
  finally:
    process.kill()
