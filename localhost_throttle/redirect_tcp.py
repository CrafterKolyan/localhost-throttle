import logging
import select
import socket
import threading

from .context_util import RunIfException, RunFinally
from .global_state import GlobalState
from .hostname_and_port import HostnameAndPort
from .util import sleep_with_poll


class RedirectClientTCP:
  # TODO: Customize buffer_size
  def __init__(
    self,
    in_socket,
    out_socket,
    *,
    bandwidth: float | None,
    global_state: GlobalState,
    poll_interval: float,
    buffer_size: int = 65536,
  ):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.buffer_size = buffer_size
    self.poll_interval = poll_interval
    self.global_state = global_state
    self.bandwidth = bandwidth
    self._stopped = None
    self._thread_in_to_out = None
    self._thread_out_to_in = None

  def _start_redirect_blocking(self, in_socket, out_socket, *, global_state: GlobalState):
    buffer_size = self.buffer_size
    bandwidth = self.bandwidth
    while not global_state.is_shutdown() and not self._stopped.isSet():
      try:
        new_data, _, _ = select.select([in_socket], [], [], self.poll_interval)
        if not new_data:
          continue
        data = in_socket.recv(buffer_size)

        data_length = len(data)
        if data_length == 0:
          out_socket.shutdown(socket.SHUT_RDWR)
          self._stopped.set()
          break
        if bandwidth is not None:
          time_to_wait = data_length / bandwidth
          sleep_with_poll(time_to_wait, poll_interval=self.poll_interval, global_state=global_state)

        out_socket.send(data)
      except (OSError, ValueError):
        self._stopped.set()
    self._stopped.set()

  def start(self):
    self._stopped = threading.Event()
    self._thread_in_to_out = self.global_state.add_thread(f=self._start_redirect_blocking, args=(self.in_socket, self.out_socket))
    self._thread_out_to_in = self.global_state.add_thread(f=self._start_redirect_blocking, args=(self.out_socket, self.in_socket))

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_tcp(
  *,
  client_socket,
  client_address,
  server_address: HostnameAndPort,
  bandwidth: float | None,
  poll_interval: float,
  global_state: GlobalState,
):
  with RunFinally(lambda: global_state.close_socket(client_socket)):
    in_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global_state.add_socket(in_socket)
    with RunFinally(lambda: global_state.close_socket(in_socket)):
      in_socket.connect(server_address.to_address())
      redirect_in_to_client = RedirectClientTCP(
        in_socket, client_socket, bandwidth=bandwidth, poll_interval=poll_interval, global_state=global_state
      )
      redirect_in_to_client.start()
      logging.info(f"Opened TCP connection to {client_address}")
      redirect_in_to_client._stopped.wait()
      in_socket.shutdown(socket.SHUT_RDWR)
    client_socket.shutdown(socket.SHUT_RDWR)
  logging.info(f"Closed TCP connection to {client_address}")


# TODO: Make request_queue_size configurable
def redirect_tcp(
  server_address: HostnameAndPort,
  new_server_address: HostnameAndPort,
  *,
  bandwidth: float | None,
  global_state: GlobalState,
  poll_interval: float,
  request_queue_size: int = 100,
):
  out_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  with RunIfException(lambda: out_socket.close()):
    global_state.add_socket(out_socket)
  with RunFinally(lambda: global_state.close_socket(out_socket)):
    out_socket.bind(new_server_address.to_address())
    out_socket.listen(request_queue_size)

    while not global_state.is_shutdown():
      new_connections, _, _ = select.select([out_socket], [], [], poll_interval)
      if not new_connections:
        continue
      (client_socket, client_address) = out_socket.accept()
      with RunIfException(lambda: client_socket.close()):
        global_state.add_socket(client_socket)
      with RunIfException(lambda: global_state.close_socket(client_socket)):
        global_state.add_thread(
          f=redirect_and_close_on_exception_tcp,
          kwargs={
            "client_socket": client_socket,
            "client_address": client_address,
            "server_address": server_address,
            "bandwidth": bandwidth,
            "poll_interval": poll_interval,
          },
        )

    out_socket.shutdown(socket.SHUT_RDWR)
