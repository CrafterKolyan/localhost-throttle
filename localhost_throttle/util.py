import time

from .global_state import GlobalState


def sleep_with_poll(time_to_sleep: float, poll_interval: float = None, *, global_state: GlobalState):
  if time_to_sleep <= 0:
    return
  elif poll_interval is None:
    time.sleep(time_to_sleep)
    return
  start = time.perf_counter()
  current = start
  while current - start < time_to_sleep:
    time_to_sleep_now = min(time_to_sleep - (current - start), poll_interval)
    time.sleep(time_to_sleep_now)
    if global_state.is_shutdown():
      break
    current = time.perf_counter()
