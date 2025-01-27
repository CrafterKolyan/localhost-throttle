import logging
import functools
import threading
from concurrent.futures import Future
from collections import defaultdict


class GlobalState:
  def __init__(self):
    current_thread = threading.current_thread()
    self.total_threads_spawned = 0
    self.thread_id_to_thread = {self.total_threads_spawned: (None, current_thread)}
    self.thread_ident_to_thread_id = {current_thread.ident: self.total_threads_spawned}
    self.total_threads_spawned += 1

    self.spawned_threads = []
    self.finished_threads = []

    self.total_sockets_created = 0
    self.socket_id_to_socket_and_thread_id = dict()
    self.socket_to_socket_id = dict()
    self.thread_id_to_sockets = defaultdict(lambda: set())

    self.added_sockets = []
    self.closed_sockets = []

    self.lock = threading.Lock()
    self.condition = threading.Condition()
    self._is_shutdown = threading.Event()

  def _wrap_function(self, f, args, kwargs, *, thread_id):
    future = Future()

    @functools.wraps(f)
    def wrapped_function():
      try:
        result = f(*args, **kwargs)
        future.set_result(result)
      except BaseException as e:
        future.set_exception(e)

    future.add_done_callback(lambda _: self._notify_finished_thread(thread_id))

    return future, wrapped_function

  def add_thread(self, *, f, args=(), kwargs=None, daemon=None, group=None, name=None):
    with self:
      thread_id = self.total_threads_spawned
      self.total_threads_spawned += 1
      extra_kwargs = {"resource_monitor": self}
      kwargs = kwargs if kwargs is not None else dict()
      for key in extra_kwargs:
        if key in kwargs:
          raise ValueError(
            f"Passing keys {list(extra_kwargs.keys())} is prohibited to kwargs. They will be passed by ResourceMonitor instead"
          )
      kwargs.update(extra_kwargs)
      future, f = self._wrap_function(f, args, kwargs, thread_id=thread_id)
      thread = threading.Thread(target=f, daemon=daemon, group=group, name=name)
      self.thread_id_to_thread[thread_id] = (future, thread)
      thread.start()
      self.thread_ident_to_thread_id[thread.ident] = thread_id
      self.spawned_threads.append(thread_id)
      self.notify_monitor()
      return thread

  def add_socket(self, sock):
    with self:
      socket_id = self.total_sockets_created
      self.total_sockets_created += 1
      thread_id = self.thread_ident_to_thread_id[threading.get_ident()]
      self.socket_id_to_socket_and_thread_id[socket_id] = sock, thread_id
      self.socket_to_socket_id[sock] = socket_id
      self.thread_id_to_sockets[thread_id].add(socket_id)
      self.added_sockets.append(socket_id)
      self.notify_monitor()

  def _close_socket(self, socket_id):
    sock, thread_id = self.socket_id_to_socket_and_thread_id[socket_id]
    sock.close()
    del self.socket_id_to_socket_and_thread_id[socket_id]
    del self.socket_to_socket_id[sock]
    opened_sockets_by_thread = self.thread_id_to_sockets[thread_id]
    opened_sockets_by_thread.remove(socket_id)
    if not opened_sockets_by_thread:
      del self.thread_id_to_sockets[thread_id]
    self.closed_sockets.append(socket_id)
    self.notify_monitor()

  def close_socket(self, sock):
    with self:
      socket_id = self.socket_to_socket_id[sock]
      self._close_socket(socket_id)

  def _join_thread(self, thread_id):
    _, thread = self.thread_id_to_thread[thread_id]
    thread_ident = thread.ident
    thread.join()
    del self.thread_id_to_thread[thread_id]
    del self.thread_ident_to_thread_id[thread_ident]

  def notify_monitor(self):
    with self.condition:
      self.condition.notify_all()

  def _notify_finished_thread(self, thread_id):
    with self:
      self.finished_threads.append(thread_id)
      self.notify_monitor()

  def shutdown(self):
    self._is_shutdown.set()

  def is_shutdown(self):
    return self._is_shutdown.isSet()

  def join(self, timeout=1):
    current_thread_id = self.thread_ident_to_thread_id[threading.get_ident()]
    all_threads_joined = True
    for thread_id, (_, thread) in self.thread_id_to_thread.items():
      if thread_id == current_thread_id:
        continue
      thread.join(timeout=timeout)
      all_threads_joined &= not thread.is_alive()
    return all_threads_joined

  def wait_for_updates(self, timeout=None):
    with self.condition:
      return self.condition.wait_for(
        lambda: self.spawned_threads != [] or self.finished_threads != [] or self.added_sockets != [] or self.closed_sockets != [],
        timeout=timeout,
      )

  def monitor_forever(self, poll_interval=0.01):
    first_update = True
    while True:
      if not first_update and not self.wait_for_updates(timeout=poll_interval):
        continue
      with self:
        if not first_update:
          logging.debug("")

        for thread_id in self.spawned_threads:
          logging.debug(f"Spawned thread {thread_id}")
        self.spawned_threads = []

        for thread_id in self.finished_threads:
          future, _ = self.thread_id_to_thread[thread_id]
          self._join_thread(thread_id)
          logging.debug(f"Finished thread {thread_id} -> {future.result()}")
        self.finished_threads = []

        for socket_id in self.added_sockets:
          logging.debug(f"Added socket {socket_id}")
        self.added_sockets = []

        for socket_id in self.closed_sockets:
          logging.debug(f"Closed socket {socket_id}")
        self.closed_sockets = []

        logging.debug(f"Threads: {len(self.thread_id_to_thread)} | Sockets: {len(self.socket_id_to_socket_and_thread_id)}")
        first_update = False

  def __enter__(self):
    return self.lock.__enter__()

  def __exit__(self, exc_type, exc_val, exc_tb):
    return self.lock.__exit__(exc_type, exc_val, exc_tb)
