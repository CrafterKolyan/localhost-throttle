import contextlib
import signal
import socket
import subprocess
import sys
import time

from localhost_throttle import Protocol, ProtocolSet, context_util

from .constants import DEFAULT_CWD, DELAY_TO_START_UP, TIME_FOR_PROCESS_TO_FINISH


def is_windows():
  return sys.platform == "win32"


def spawn_localhost_throttle(*, in_port, out_port, protocols, bandwidth=None):
  creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0
  args = [
    sys.executable,
    "-m",
    "test.run_localhost_throttle_with_ctrl_handler",
    "--server",
    f"localhost:{in_port}",
    "--new-server",
    f"localhost:{out_port}",
    "--protocols",
    str(protocols),
    "--log-level",
    "debug",
  ]
  if bandwidth is not None:
    args.extend(["--bandwidth", str(bandwidth)])
  return subprocess.Popen(
    args,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=DEFAULT_CWD,
    creationflags=creationflags,
  )


def interrupt_process(process):
  if is_windows():
    signal_to_send = signal.CTRL_C_EVENT
  else:
    signal_to_send = signal.SIGINT
  process.send_signal(signal_to_send)


def random_ports(socket_type, size=None):
  sockets = [socket.socket(socket.AF_INET, socket_type) for _ in range(size if size is not None else 1)]
  try:
    ports = [0 for _ in range(len(sockets))]
    for i, sock in enumerate(sockets):
      sock.bind(("localhost", 0))
      ports[i] = sock.getsockname()[1]

    if size is None:
      return ports[0]
    return ports

  finally:
    for sock in sockets:
      sock.close()


class TCPSingleConnectionTest:
  def __init__(self, bandwidth=None):
    self._in_socket = None
    self._out_socket = None
    self._in_socket_out = None
    self._process = None
    self.bandwidth = bandwidth

  def __enter__(self):
    protocol = Protocol.TCP
    socket_type = protocol.socket_type()
    in_socket = socket.socket(socket.AF_INET, socket_type)
    with context_util.RunIfException(lambda: in_socket.close()):
      out_socket = socket.socket(socket.AF_INET, socket_type)
      with context_util.RunIfException(lambda: out_socket.close()):
        in_socket.bind(("localhost", 0))
        in_socket.listen(1)
        in_port = in_socket.getsockname()[1]
        out_port = random_ports(socket_type)

        self._in_socket = in_socket
        self._out_socket = out_socket
        self._process = spawn_localhost_throttle(
          in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]), bandwidth=self.bandwidth
        )
        with context_util.RunIfException(lambda: self._process.kill()):
          # TODO: Due to this `time.sleep` correct handling of resources becomes even more critical. Really want to use `RunIfException`
          time.sleep(DELAY_TO_START_UP)

          out_socket.connect(("localhost", out_port))
          in_socket_out, _ = in_socket.accept()
          with context_util.RunIfException(lambda: in_socket_out.close()):
            self._in_socket_out = in_socket_out
    return (self._in_socket_out, self._out_socket, self._process)

  def __exit__(self, exc_type, exc_value, traceback):
    with contextlib.closing(self._in_socket):
      with contextlib.closing(self._out_socket):
        with contextlib.closing(self._in_socket_out):
          with context_util.RunIfException(lambda: self._process.kill()):
            # TODO: For some reason we need to wait a little bit. Something weird happens with joining threads on Windows otherwise.
            # We need to understand why and fix the underlying issue.
            time.sleep(0.01)
            interrupt_process(self._process)
            self._process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)


class UDPSingleConnectionTest:
  def __init__(self, bandwidth=None):
    self._in_socket = None
    self._out_socket = None
    self._process = None
    self._out_port = None
    self.bandwidth = bandwidth

  def __enter__(self):
    protocol = Protocol.UDP
    socket_type = protocol.socket_type()
    in_socket = socket.socket(socket.AF_INET, socket_type)
    with context_util.RunIfException(lambda: in_socket.close()):
      # TODO: Need to use `RunIfException` here in case the exception is thrown here
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      out_port = random_ports(socket_type)
      self._in_socket = in_socket
      self._out_socket = socket.socket(socket.AF_INET, socket_type)
      with context_util.RunIfException(lambda: self._out_socket.close()):
        self._process = spawn_localhost_throttle(
          in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]), bandwidth=self.bandwidth
        )
        with context_util.RunIfException(lambda: self._process.kill()):
          self._out_port = out_port
          # TODO: Due to this `time.sleep` `RunIfException` becomes even more critical
          time.sleep(DELAY_TO_START_UP)
    return (self._in_socket, self._out_socket, self._process, self._out_port)

  def __exit__(self, exc_type, exc_value, traceback):
    with contextlib.closing(self._in_socket):
      with contextlib.closing(self._out_socket):
        self._process.kill()
