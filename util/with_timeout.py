import functools
import threading

from .exceptions import TimeoutExceeded


class RunWithTimeout:
  def __init__(self, *, seconds, msg=None):
    self.seconds = seconds
    self.msg = msg
    self._timer = None
    self._failed = False

  def __enter__(self):
    self._timer = threading.Timer(interval=self.seconds, function=self.fail)
    self._timer.start()

  def __exit__(self, exc_type, exc_value, traceback):
    self._timer.cancel()
    if self._failed:
      args = [self.msg] if self.msg is not None else []
      raise TimeoutExceeded(*args)

  def fail(self):
    self._failed = True


def with_timeout(*, seconds):
  @functools.wraps(with_timeout)
  def decorator(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
      with RunWithTimeout(seconds=seconds):
        return f(*args, **kwargs)

    return decorated

  return decorator
