from .parser import create_parser
from .protocol_type import Protocol
from .redirect_tcp import redirect_tcp
from .redirect_udp import redirect_udp


def redirect(protocol, in_port, out_port, hostname="", request_queue_size=100, poll_interval=0.1):
  match protocol:
    case Protocol.TCP:
      redirect_tcp(in_port, out_port, hostname=hostname, request_queue_size=request_queue_size, poll_interval=poll_interval)
    case Protocol.UDP:
      redirect_udp(in_port, out_port, hostname=hostname, poll_interval=poll_interval)


def localhost_throttle(in_port, out_port, protocols):
  if len(protocols) > 1:
    raise NotImplementedError("Currently redirection of 2 protocols at the same time is not supported")
  for protocol in protocols:
    redirect(protocol, in_port, out_port)


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(args.in_port, args.out_port, args.protocols)
