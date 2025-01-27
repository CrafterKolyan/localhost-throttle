import contextlib
import logging
import socket
import socketserver
import threading


class RedirectClientUDP:
  # TODO: Customize buffer_size
  def __init__(self, in_addr, out_addr, in_socket, out_socket, buffer_size=65536):
    self.in_addr = in_addr
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.out_addr = out_addr
    self.buffer_size = buffer_size
    self._stopped = None
    self._thread = None

  def _start_redirect_blocking(self, in_addr, out_addr, in_socket, out_socket, first_message):
    buffer_size = self.buffer_size
    in_socket.sendto(first_message, in_addr)
    while not self._stopped.isSet():
      try:
        data, _ = in_socket.recvfrom(buffer_size)
        out_socket.sendto(data, out_addr)
        if len(data) == 0:
          self._stopped.set()
          break
      except OSError:
        self._stopped.set()

  def start(self, first_message):
    self._stopped = threading.Event()
    self._thread = threading.Thread(
      target=self._start_redirect_blocking,
      args=(self.in_addr, self.out_addr, self.in_socket, self.out_socket, first_message),
      daemon=True,
    )
    self._thread.start()

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_udp(*, in_port, client_address, first_message, out_socket, socket_obj):
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as in_socket:
    socket_obj.append(in_socket)
    redirect_in_to_client = RedirectClientUDP(("localhost", in_port), client_address, in_socket, out_socket)
    redirect_in_to_client.start(first_message)
    redirect_in_to_client._stopped.wait()
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


def redirect_udp(in_port, out_port, hostname="", poll_interval=0.1):
  client_address_to_thread = dict()
  with socketserver.UDPServer(
    (hostname, out_port),
    create_udp_server_request_handler_with_payload(in_port=in_port, client_address_to_thread=client_address_to_thread),
    bind_and_activate=True,
  ) as server:
    server.serve_forever(poll_interval=poll_interval)
