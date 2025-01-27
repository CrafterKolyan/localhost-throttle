import logging
import select
import socket
import socketserver
import threading

from .context_util import RunIfException, RunFinally
from .resource_monitor import ResourceMonitor


def start_redirect_blocking(out_addr, in_socket, out_socket, *, resource_monitor, buffer_size=65536, poll_interval=0.1):
  while not resource_monitor.is_shutdown():
    new_data, _, _ = select.select([in_socket], [], [], poll_interval)
    if not new_data:
      continue
    data, _ = in_socket.recvfrom(buffer_size)
    out_socket.sendto(data, out_addr)


def redirect_and_close_on_exception_udp(*, client_address, out_socket, in_socket, resource_monitor):
  logging.info(f"Opened UDP connection to {client_address}")
  start_redirect_blocking(client_address, in_socket, out_socket, resource_monitor=resource_monitor)
  logging.info(f"Closed UDP connection to {client_address}")


def create_udp_server_request_handler_with_payload(*, in_port, client_address_to_thread):
  class UDPServerRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
      message, out_socket = self.request
      client_address = self.client_address
      result = client_address_to_thread.get(client_address, None)
      if result is None:
        logging.info(f"Received new UDP connection from {client_address}")
        # TODO: Rewrite `socket_obj` to a class that you can set only once
        socket_obj = []
        thread = threading.Thread(
          target=redirect_and_close_on_exception_udp,
          kwargs={
            "in_port": in_port,
            "client_address": client_address,
            "first_message": message,
            "out_socket": out_socket,
            "socket_obj": socket_obj,
          },
          daemon=True,
        )
        client_address_to_thread[client_address] = (thread, socket_obj)
        thread.start()
      else:
        _, socket_obj = result
        in_socket = socket_obj[0]
        in_socket.sendto(message, ("localhost", in_port))

    def finish(self):
      pass

  return UDPServerRequestHandler


def redirect_udp(in_port, out_port, *, resource_monitor: ResourceMonitor, hostname="", poll_interval=0.1):
  client_address_to_socket_and_thread = dict()

  out_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  with RunIfException(lambda: out_socket.close()):
    resource_monitor.add_socket(out_socket)
  with RunFinally(lambda: resource_monitor.close_socket(out_socket)):
    out_socket.bind((hostname, out_port))
    buffer_size = 65537

    while not resource_monitor.is_shutdown():
      new_connections, _, _ = select.select([out_socket], [], [], poll_interval)
      if not new_connections:
        continue
      (message, client_address) = out_socket.recvfrom(buffer_size)
      socket_and_thread = client_address_to_socket_and_thread.get(client_address)
      if socket_and_thread is None:
        server_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with RunIfException(lambda: server_client_socket.close()):
          resource_monitor.add_socket(server_client_socket)
        with RunIfException(lambda: resource_monitor.close_socket(server_client_socket)):
          server_client_socket.bind(("localhost", 0))
          thread = resource_monitor.add_thread(
            f=redirect_and_close_on_exception_udp,
            kwargs={
              "client_address": client_address,
              "out_socket": out_socket,
              "in_socket": server_client_socket,
            },
            daemon=True,
          )
          client_address_to_socket_and_thread[client_address] = (server_client_socket, thread)
      else:
        server_client_socket, _ = socket_and_thread
      server_client_socket.sendto(message, ("localhost", in_port))

    out_socket.shutdown(socket.SHUT_RDWR)
    for sock, _ in client_address_to_socket_and_thread.items():
      sock.shutdown(socket.SHUT_RDWR)
      resource_monitor.close_socket(sock)
