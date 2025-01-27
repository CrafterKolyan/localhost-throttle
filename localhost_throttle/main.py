import logging

from .parser import create_parser
from .protocol_type import Protocol, ProtocolSet
from .redirect_tcp import redirect_tcp
from .redirect_udp import redirect_udp
from .global_state import GlobalState


def redirect(
  protocol: Protocol,
  in_port: int,
  out_port: int,
  *,
  bandwidth: float | None,
  global_state: GlobalState,
  hostname: str = "",
  request_queue_size: int = 100,
  poll_interval: float = 0.1,
):
  match protocol:
    case Protocol.TCP:
      redirect_tcp(
        in_port,
        out_port,
        bandwidth=bandwidth,
        global_state=global_state,
        hostname=hostname,
        request_queue_size=request_queue_size,
        poll_interval=poll_interval,
      )
    case Protocol.UDP:
      redirect_udp(
        in_port, out_port, bandwidth=bandwidth, global_state=global_state, hostname=hostname, poll_interval=poll_interval
      )


def localhost_throttle(
  in_port: int, out_port: int, protocols: ProtocolSet, *, bandwidth: float | None, poll_interval: float = 0.01
):
  logging.basicConfig(format="%(asctime)s\t%(filename)s:%(lineno)s\t%(levelname)s\t%(message)s", level=logging.INFO)
  global_state = GlobalState()
  for protocol in protocols:
    global_state.add_thread(
      f=redirect, args=(protocol, in_port, out_port), kwargs={"bandwidth": bandwidth, "poll_interval": poll_interval}
    )
  try:
    global_state.monitor_forever(poll_interval=poll_interval)
  except KeyboardInterrupt:
    global_state.shutdown()
    all_threads_joined = global_state.join()
    if not all_threads_joined:
      raise RuntimeError("Not all threads joined in the end")


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(args.in_port, args.out_port, args.protocols, bandwidth=args.bandwidth)
