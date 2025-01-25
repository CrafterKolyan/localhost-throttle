import logging
import socketserver
import threading

from .redirect_client import redirect_and_close_on_exception_udp


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
