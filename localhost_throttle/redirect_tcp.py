import logging
import select
import socket
import threading

from .context_util import RunIfException, RunFinally
from .global_state import GlobalState


class RedirectClientTCP:
  # TODO: Customize buffer_size
  def __init__(self, in_socket, out_socket, *, resource_monitor, buffer_size=65536, poll_interval=0.01):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.buffer_size = buffer_size
    self.poll_interval = poll_interval
    self.resource_monitor = resource_monitor
    self._stopped = None
    self._thread_in_to_out = None
    self._thread_out_to_in = None

  def _start_redirect_blocking(self, in_socket, out_socket, *, resource_monitor: GlobalState):
    buffer_size = self.buffer_size
    while not resource_monitor.is_shutdown() and not self._stopped.isSet():
      try:
        new_data, _, _ = select.select([in_socket], [], [], self.poll_interval)
        if not new_data:
          continue
        data = in_socket.recv(buffer_size)
        if len(data) == 0:
          out_socket.shutdown(socket.SHUT_RDWR)
          self._stopped.set()
          break
        out_socket.send(data)
      except (OSError, ValueError):
        self._stopped.set()
    self._stopped.set()

  def start(self):
    self._stopped = threading.Event()
    self._thread_in_to_out = self.resource_monitor.add_thread(
      f=self._start_redirect_blocking, args=(self.in_socket, self.out_socket)
    )
    self._thread_out_to_in = self.resource_monitor.add_thread(
      f=self._start_redirect_blocking, args=(self.out_socket, self.in_socket)
    )

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_tcp(*, client_socket, client_address, in_port, resource_monitor: GlobalState):
  with RunFinally(lambda: resource_monitor.close_socket(client_socket)):
    in_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    resource_monitor.add_socket(in_socket)
    with RunFinally(lambda: resource_monitor.close_socket(in_socket)):
      in_socket.connect(("localhost", in_port))
      redirect_in_to_client = RedirectClientTCP(in_socket, client_socket, resource_monitor=resource_monitor)
      redirect_in_to_client.start()
      logging.info(f"Opened TCP connection to {client_address}")
      redirect_in_to_client._stopped.wait()
      in_socket.shutdown(socket.SHUT_RDWR)
    client_socket.shutdown(socket.SHUT_RDWR)
  logging.info(f"Closed TCP connection to {client_address}")


# TODO: Make hostname configurable
# TODO: Make request_queue_size configurable
# TODO: Make poll_interval configurable
def redirect_tcp(in_port, out_port, *, resource_monitor: GlobalState, hostname="", request_queue_size=100, poll_interval=0.1):
  out_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  with RunIfException(lambda: out_socket.close()):
    resource_monitor.add_socket(out_socket)
  with RunFinally(lambda: resource_monitor.close_socket(out_socket)):
    out_socket.bind((hostname, out_port))
    out_socket.listen(request_queue_size)

    while not resource_monitor.is_shutdown():
      new_connections, _, _ = select.select([out_socket], [], [], poll_interval)
      if not new_connections:
        continue
      (client_socket, client_address) = out_socket.accept()
      with RunIfException(lambda: client_socket.close()):
        resource_monitor.add_socket(client_socket)
      with RunIfException(lambda: resource_monitor.close_socket(client_socket)):
        resource_monitor.add_thread(
          f=redirect_and_close_on_exception_tcp,
          kwargs={"client_socket": client_socket, "client_address": client_address, "in_port": in_port},
        )

    out_socket.shutdown(socket.SHUT_RDWR)
