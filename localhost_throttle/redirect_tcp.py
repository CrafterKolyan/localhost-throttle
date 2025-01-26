import contextlib
import logging
import socket
import socketserver
import threading


class RedirectClientTCP:
  # TODO: Customize buffer_size
  def __init__(self, in_socket, out_socket, buffer_size=65536):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.buffer_size = buffer_size
    self._stopped = None
    self._thread_in_to_out = None
    self._thread_out_to_in = None

  def _start_redirect_blocking(self, in_socket, out_socket):
    buffer_size = self.buffer_size
    while not self._stopped.isSet():
      try:
        data = in_socket.recv(buffer_size)
        if len(data) == 0:
          out_socket.shutdown(socket.SHUT_RDWR)
          self._stopped.set()
          break
        out_socket.send(data)
      except OSError:
        self._stopped.set()

  def start(self):
    self._stopped = threading.Event()
    self._thread_in_to_out = threading.Thread(
      target=self._start_redirect_blocking, args=(self.in_socket, self.out_socket), daemon=True
    )
    self._thread_in_to_out.start()
    self._thread_out_to_in = threading.Thread(
      target=self._start_redirect_blocking, args=(self.out_socket, self.in_socket), daemon=True
    )
    self._thread_out_to_in.start()

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_tcp(*, client_socket, client_address, in_port):
  with contextlib.closing(client_socket) as client_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
      in_socket.connect(("localhost", in_port))
      redirect_in_to_client = RedirectClientTCP(in_socket, client_socket)
      redirect_in_to_client.start()
      redirect_in_to_client._stopped.wait()
  logging.info(f"Closed connection to {client_address}")


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
  class TCPServerRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
      client_socket = self.request
      client_address = self.client_address
      logging.info(f"Received new TCP connection from {client_address}")
      thread = threading.Thread(
        target=redirect_and_close_on_exception_tcp,
        kwargs={"client_socket": client_socket, "client_address": client_address, "in_port": in_port},
        daemon=True,
      )
      thread.start()

    def finish(self):
      pass

  return TCPServerRequestHandler


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
