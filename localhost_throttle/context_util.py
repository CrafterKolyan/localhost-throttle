import contextlib


class RunIfException(contextlib.AbstractContextManager, contextlib.AbstractAsyncContextManager):
  def __init__(self, f):
    self.f = f

  def _on_exit(self, exc_type):
    if exc_type is not None:
      self.f()

  def __exit__(self, exc_type, exc_value, traceback):
    self._on_exit(exc_type)

  def __aexit__(self, exc_type, exc_value, traceback):
    self._on_exit(exc_type)


class RunFinally(contextlib.AbstractContextManager, contextlib.AbstractAsyncContextManager):
  def __init__(self, f):
    self.f = f

  def _on_exit(self):
    self.f()

  def __exit__(self, exc_type, exc_value, traceback):
    self._on_exit()

  def __aexit__(self, exc_type, exc_value, traceback):
    self._on_exit()
