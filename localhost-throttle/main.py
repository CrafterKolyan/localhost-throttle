import socket
import contextlib
import threading
from .parser import create_parser
from .protocol_type import Protocol
from .redirect_client import redirect_and_close_on_exception


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
      (client_socket, _) = out_socket.accept()
      thread = threading.Thread(
        target=redirect_and_close_on_exception,
        kwargs={"client_socket": client_socket, "in_port": in_port, "socket_type": socket_type},
        daemon=True,
      )
      thread.start()


def localhost_throttle(in_port, out_port, protocols):
  if len(protocols) > 1:
    raise NotImplementedError("Currently redirection of 2 protocols at the same time is not supported")
  for protocol in protocols:
    redirect(protocol, in_port, out_port)


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(args.in_port, args.out_port, args.protocols)
