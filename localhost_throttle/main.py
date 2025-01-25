import socketserver
import threading
from .parser import create_parser
from .protocol_type import Protocol
from .redirect_client import redirect_and_close_on_exception


class CustomizableTCPServer(socketserver.TCPServer):
  def __init__(
    self,
    server_address,
    RequestHandlerClass,
    bind_and_activate=True,
    request_queue_size=5,
    allow_reuse_address=False,
    allow_reuse_port=False,
    shutdown_requests=True,
  ):
    self.request_queue_size = request_queue_size
    self.allow_reuse_address = allow_reuse_address
    self.allow_reuse_port = allow_reuse_port
    self.shutdown_requests = shutdown_requests
    super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)

  def process_request(self, request, client_address):
    self.finish_request(request, client_address)
    if self.shutdown_requests:
      self.shutdown_request(request)


def create_tcp_server_request_handler_with_payload(*, in_port, socket_type):
  def create_tcp_server_request_handler(*args, **kwargs):
    class TCPServerRequestHandler(socketserver.StreamRequestHandler):
      def handle(self):
        client_socket = self.request
        thread = threading.Thread(
          target=redirect_and_close_on_exception,
          kwargs={"client_socket": client_socket, "in_port": in_port, "socket_type": socket_type},
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
def redirect(protocol, in_port, out_port, hostname="", request_queue_size=100, poll_interval=0.1):
  if protocol == Protocol.UDP:
    raise NotImplementedError("Redirecting UDP protocol/UDP datagrams is not supported yet")
  socket_type = protocol.socket_type()
  with CustomizableTCPServer(
    (hostname, out_port),
    create_tcp_server_request_handler_with_payload(in_port=in_port, socket_type=socket_type),
    bind_and_activate=True,
    request_queue_size=request_queue_size,
    shutdown_requests=False,
  ) as server:
    server.serve_forever(poll_interval=poll_interval)


def localhost_throttle(in_port, out_port, protocols):
  if len(protocols) > 1:
    raise NotImplementedError("Currently redirection of 2 protocols at the same time is not supported")
  for protocol in protocols:
    redirect(protocol, in_port, out_port)


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(args.in_port, args.out_port, args.protocols)
