import subprocess
import sys

from .constants import DEFAULT_CWD, MODULE_NAME


def spawn_localhost_throttle(*, in_port, out_port, protocols):
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
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
  )
