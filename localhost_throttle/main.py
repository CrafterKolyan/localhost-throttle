import logging

from .global_state import GlobalState
from .hostname_and_port import HostnameAndPort
from .parser import create_parser
from .protocol_type import Protocol, ProtocolSet
from .redirect_tcp import redirect_tcp
from .redirect_udp import redirect_udp


def redirect(
  protocol: Protocol,
  server_address: HostnameAndPort,
  new_server_address: HostnameAndPort,
  *,
  bandwidth: float | None,
  global_state: GlobalState,
  request_queue_size: int = 100,
  poll_interval: float = 0.01,
):
  match protocol:
    case Protocol.TCP:
      redirect_tcp(
        server_address,
        new_server_address,
        bandwidth=bandwidth,
        global_state=global_state,
        request_queue_size=request_queue_size,
        poll_interval=poll_interval,
      )
    case Protocol.UDP:
      redirect_udp(
        server_address,
        new_server_address,
        bandwidth=bandwidth,
        global_state=global_state,
        poll_interval=poll_interval,
      )


def localhost_throttle(
  server_address: HostnameAndPort,
  new_server_address: HostnameAndPort,
  protocols: ProtocolSet,
  *,
  bandwidth: float | None = None,
  poll_interval: float = 0.01,
  log_level: int = logging.INFO,
):
  logging.basicConfig(format="%(asctime)s\t%(filename)s:%(lineno)s\t%(levelname)s\t%(message)s", level=log_level)
  global_state = GlobalState()
  for protocol in protocols:
    global_state.add_thread(
      f=redirect,
      args=(protocol, server_address, new_server_address),
      kwargs={"bandwidth": bandwidth, "poll_interval": poll_interval},
    )
  try:
    global_state.monitor_forever(poll_interval=poll_interval)
  except BaseException:
    global_state.shutdown()
    all_threads_joined = global_state.join(timeout=1)
    if not all_threads_joined:
      raise RuntimeError("Not all threads joined in the end")


def main():
  parser = create_parser()
  args = parser.parse_args()
  localhost_throttle(
    args.server,
    args.new_server,
    args.protocols,
    bandwidth=args.bandwidth,
    poll_interval=args.poll_interval,
    log_level=args.log_level,
  )
