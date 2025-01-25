import contextlib
import socket
import subprocess
import sys

import pytest

from test.constants import DEFAULT_CWD


def test_fails_with_no_arguments():
  process = subprocess.Popen(
    [sys.executable, "-m", "localhost-throttle"],
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
      in_socket_port = in_socket.getsockname()[1]
      out_socket.bind(("localhost", 0))
      out_socket_port = in_socket.getsockname()[1]
  process = subprocess.Popen(
    [
      sys.executable,
      "-m",
      "localhost-throttle",
      "--in-port",
      str(in_socket_port),
      "--out-port",
      str(out_socket_port),
      "--protocols",
      "tcp",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=DEFAULT_CWD,
  )
  try:
    with pytest.raises(subprocess.TimeoutExpired):
      process.communicate(timeout=1)
  finally:
    process.kill()
