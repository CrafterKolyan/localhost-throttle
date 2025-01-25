import socketserver
import threading

from .redirect_client import redirect_and_close_on_exception_udp


def create_udp_server_request_handler_with_payload(*, in_port):
  def create_udp_server_request_handler(*args, **kwargs):
    class UDPServerRequestHandler(socketserver.DatagramRequestHandler):
      def handle(self):
        message, _ = self.request
        client_address = self.client_address
        thread = threading.Thread(
          target=redirect_and_close_on_exception_udp,
          kwargs={"in_port": in_port, "client_address": client_address, "first_message": message},
          daemon=True,
        )
        thread.start()

      def finish(self):
        pass

    return UDPServerRequestHandler(*args, **kwargs)

  return create_udp_server_request_handler


def redirect_udp(in_port, out_port, hostname="", poll_interval=0.1):
  with socketserver.UDPServer(
    (hostname, out_port),
    create_udp_server_request_handler_with_payload(in_port=in_port),
    bind_and_activate=True,
  ) as server:
    server.serve_forever(poll_interval=poll_interval)
