import contextlib
import socket
import subprocess
import sys

from .constants import DEFAULT_CWD, MODULE_NAME


def spawn_localhost_throttle(*, in_port, out_port, protocols):
  creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
  return subprocess.Popen(
    [
      sys.executable,
      "-m",
      MODULE_NAME,
      "--in-port",
      str(in_port),
      "--out-port",
      str(out_port),
      "--protocols",
      str(protocols),
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=DEFAULT_CWD,
    creationflags=creationflags,
  )


def random_port(socket_type):
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as sock:
    sock.bind(("localhost", 0))
    return sock.getsockname()[1]
