import time
import signal
import subprocess
import sys

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DEFAULT_CWD, MODULE_NAME, DELAY_TO_START_UP
from .util import spawn_localhost_throttle, random_ports


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
  assert return_code != 0, "localhost-throttle should fail when run without arguments"


@pytest.mark.timeout(3)
def test_properly_starts_up():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    time.sleep(DELAY_TO_START_UP)
    with pytest.raises(subprocess.TimeoutExpired):
      process.communicate(timeout=1)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(sys.platform != "win32", reason="Exits after Ctrl+Break on Windows")
def test_can_be_killed_with_CTRL_BREAK_on_windows():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.CTRL_BREAK_EVENT)
    process.communicate(timeout=0.3)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(sys.platform == "win32", reason="Exits after Ctrl+C on Linux")
def test_can_be_killed_with_SIGINT_on_linux():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.SIGINT)
    process.communicate(timeout=0.3)
  finally:
    process.kill()
