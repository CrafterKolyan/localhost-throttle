import logging
import select
import socket
import time

from .context_util import RunIfException, RunFinally
from .global_state import GlobalState
from .hostname_and_port import HostnameAndPort


def start_redirect_blocking(out_address, in_socket, out_socket, *, bandwidth, global_state, buffer_size=65536, poll_interval=0.1):
  while not global_state.is_shutdown():
    new_data, _, _ = select.select([in_socket], [], [], poll_interval)
    if not new_data:
      continue
    data, _ = in_socket.recvfrom(buffer_size)
    if bandwidth is not None:
      time_to_sleep = len(data) / bandwidth
      time.sleep(time_to_sleep)
    out_socket.sendto(data, out_address)


def redirect_and_close_on_exception_udp(*, client_address, out_socket, in_socket, bandwidth, global_state):
  logging.info(f"Opened UDP connection to {client_address}")
  start_redirect_blocking(client_address, in_socket, out_socket, bandwidth=bandwidth, global_state=global_state)
  logging.info(f"Closed UDP connection to {client_address}")


def redirect_udp(
  server_address: HostnameAndPort,
  new_server_address: HostnameAndPort,
  *,
  bandwidth: float | None,
  global_state: GlobalState,
  poll_interval: float = 0.1,
):
  client_address_to_socket_and_thread = dict()

  out_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  with RunIfException(lambda: out_socket.close()):
    global_state.add_socket(out_socket)
  with RunFinally(lambda: global_state.close_socket(out_socket)):
    out_socket.bind(new_server_address.to_address())
    buffer_size = 65537

    while not global_state.is_shutdown():
      new_connections, _, _ = select.select([out_socket], [], [], poll_interval)
      if not new_connections:
        continue
      (message, client_address) = out_socket.recvfrom(buffer_size)
      socket_and_thread = client_address_to_socket_and_thread.get(client_address)
      if socket_and_thread is None:
        server_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with RunIfException(lambda: server_client_socket.close()):
          global_state.add_socket(server_client_socket)
        with RunIfException(lambda: global_state.close_socket(server_client_socket)):
          server_client_socket.bind(("localhost", 0))
          thread = global_state.add_thread(
            f=redirect_and_close_on_exception_udp,
            kwargs={
              "client_address": client_address,
              "out_socket": out_socket,
              "in_socket": server_client_socket,
              "bandwidth": bandwidth,
            },
          )
          client_address_to_socket_and_thread[client_address] = (server_client_socket, thread)
      else:
        server_client_socket, _ = socket_and_thread

      if bandwidth is not None:
        time_to_sleep = len(message) / bandwidth
        time.sleep(time_to_sleep)
      server_client_socket.sendto(message, server_address.to_address())

    out_socket.shutdown(socket.SHUT_RDWR)
    for sock, _ in client_address_to_socket_and_thread.items():
      sock.shutdown(socket.SHUT_RDWR)
      global_state.close_socket(sock)
