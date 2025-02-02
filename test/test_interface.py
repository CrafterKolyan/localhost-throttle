import time
import signal
import subprocess
import sys

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DEFAULT_CWD, MODULE_NAME, DELAY_TO_START_UP, TIME_FOR_PROCESS_TO_FINISH
from .util import spawn_localhost_throttle, random_ports, is_windows


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
      _, stderr = process.communicate(timeout=1)
      assert stderr == b"", stderr
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(not is_windows(), reason="Exits after Ctrl+Break on Windows")
def test_can_be_killed_with_CTRL_BREAK_on_windows():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.CTRL_BREAK_EVENT)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(not is_windows(), reason="Exits after Ctrl+C on Windows")
def test_can_be_killed_with_CTRL_C_on_windows():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.CTRL_C_EVENT)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
  finally:
    process.terminate()


@pytest.mark.timeout(3)
@pytest.mark.skipif(is_windows(), reason="Exits after Ctrl+C on Linux")
def test_can_be_killed_with_SIGINT_on_linux():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.SIGINT)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(is_windows(), reason="Exits after SIGTERM on Linux")
def test_can_be_killed_with_SIGTERM_on_linux():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(
    in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]), run_with_ctrl_handler=False
  )
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.SIGTERM)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
  finally:
    process.kill()


@pytest.mark.timeout(3)
@pytest.mark.skipif(is_windows(), reason="Exits after SIGKILL on Linux")
def test_can_be_killed_with_SIGKILL_on_linux():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  in_port, out_port = random_ports(socket_type, size=2)
  process = spawn_localhost_throttle(
    in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]), run_with_ctrl_handler=False
  )
  try:
    # Give some time to start up
    time.sleep(DELAY_TO_START_UP)
    process.send_signal(signal.SIGKILL)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
  finally:
    process.kill()
