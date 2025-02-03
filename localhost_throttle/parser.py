import argparse
import logging

from .protocol_type import ProtocolSet
from .hostname_and_port import HostnameAndPort

default_poll_interval = 0.01


def parse_log_level(str_: str):
  return logging.getLevelName(str_.upper())


def create_parser():
  parser = argparse.ArgumentParser(description="Throttle localhost connection")
  parser.add_argument(
    "--server",
    "--server-addr",
    "--server-address",
    type=HostnameAndPort.from_string,
    required=True,
    help='address on which the original server is located in the format "host:port". "localhost-throttle" subscribes to it',
  )
  parser.add_argument(
    "--new-server",
    "--new-server-addr",
    "--new-server-address",
    type=HostnameAndPort.from_string,
    required=True,
    help='bind new server to this address. Format: "host:port" New server is handled by "localhost-throttle". Clients should connect to new server',
  )
  parser.add_argument(
    "--protocols",
    type=ProtocolSet.from_string,
    required=True,
    help="protocols to redirect. Supported values: 'tcp', 'udp', 'tcp,udp'",
  )
  parser.add_argument(
    "--bandwidth", type=float, required=False, help="Bandwidth in bytes per second. Can be ommitted for unlimited"
  )
  parser.add_argument(
    "--poll-interval",
    type=float,
    default=default_poll_interval,
    required=False,
    help=f'Polling interval for blocking calls. This value controls how fast "localhost-throttle" responds to user actions like Ctrl+C. (default: {default_poll_interval})',
  )
  parser.add_argument("--log-level", type=parse_log_level, required=False, help="Logging level")
  return parser
