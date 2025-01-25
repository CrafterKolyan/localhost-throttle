import socket
import contextlib
import threading
from .parser import create_parser
from .protocol_type import Protocol

import time


class RedirectClient:
  # TODO: Customize buffer_size
  def __init__(self, in_socket, out_socket, buffer_size=1000):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.buffer_size = buffer_size
    self._running = None
    self._thread = None

  def start_redirect_blocking(self):
    if self._running is None:
      self._running = threading.Event()

    in_socket = self.in_socket
    out_socket = self.out_socket
    buffer_size = self.buffer_size
    while not self._running.isSet():
      data = in_socket.recv(buffer_size)
      out_socket.send(data)

  def start_redirect_nonblocking(self):
    self._running = threading.Event()
    self._thread = threading.Thread(target=self.start_redirect_blocking)
    self._thread.start()

  def stop(self):
    self._running.set()


# TODO: Make hostname configurable
# TODO: Make backlog configurable
def redirect(protocol, in_port, out_port, hostname="", backlog=100):
  if protocol == Protocol.UDP:
    raise NotImplementedError("Redirecting UDP protocol/UDP datagrams is not supported yet")
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
    out_socket.bind((hostname, out_port))
    out_socket.listen(backlog)

    while True:
      (clientsocket, _) = out_socket.accept()

      with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
        in_socket.connect(("localhost", in_port))
        redirect_in_to_client = RedirectClient(in_socket, clientsocket)
        redirect_in_to_client.start_redirect_nonblocking()
        redirect_client_to_in = RedirectClient(clientsocket, in_socket)
        redirect_client_to_in.start_redirect_nonblocking()
        time.sleep(5)
        clientsocket.close()


def localhost_throttle(in_port, out_port, protocols):
  if len(protocols) > 1:
    raise NotImplementedError("Currently redirection of 2 protocols at the same time is not supported")
  for protocol in protocols:
    redirect(protocol, in_port, out_port)


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(args.in_port, args.out_port, args.protocols)
