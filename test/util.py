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
