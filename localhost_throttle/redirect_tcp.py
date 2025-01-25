import socketserver
import threading

from .redirect_client import redirect_and_close_on_exception_tcp


class CustomizableTCPServer(socketserver.TCPServer):
  def __init__(
    self,
    server_address,
    RequestHandlerClass,
    bind_and_activate=True,
    request_queue_size=5,
    allow_reuse_address=False,
    allow_reuse_port=False,
    shutdown_connections_after_processing=True,
  ):
    self.request_queue_size = request_queue_size
    self.allow_reuse_address = allow_reuse_address
    self.allow_reuse_port = allow_reuse_port
    self.shutdown_connections_after_processing = shutdown_connections_after_processing
    super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)

  def process_request(self, request, client_address):
    self.finish_request(request, client_address)
    if self.shutdown_connections_after_processing:
      self.shutdown_request(request)


def create_tcp_server_request_handler_with_payload(*, in_port):
  def create_tcp_server_request_handler(*args, **kwargs):
    class TCPServerRequestHandler(socketserver.StreamRequestHandler):
      def handle(self):
        client_socket = self.request
        thread = threading.Thread(
          target=redirect_and_close_on_exception_tcp,
          kwargs={"client_socket": client_socket, "in_port": in_port},
          daemon=True,
        )
        thread.start()

      def finish(self):
        pass

    return TCPServerRequestHandler(*args, **kwargs)

  return create_tcp_server_request_handler


# TODO: Make hostname configurable
# TODO: Make request_queue_size configurable
# TODO: Make poll_interval configurable
def redirect_tcp(in_port, out_port, hostname="", request_queue_size=100, poll_interval=0.1):
  with CustomizableTCPServer(
    (hostname, out_port),
    create_tcp_server_request_handler_with_payload(in_port=in_port),
    bind_and_activate=True,
    request_queue_size=request_queue_size,
    shutdown_connections_after_processing=False,
  ) as server:
    server.serve_forever(poll_interval=poll_interval)
