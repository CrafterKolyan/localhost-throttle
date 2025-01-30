import argparse
from .protocol_type import ProtocolSet


def create_parser():
  parser = argparse.ArgumentParser(description="Throttle localhost connection")
  parser.add_argument(
    "--server-port",
    type=int,
    required=True,
    help="port on a localhost on which the original server is located. `localhost-throttle` subscribes to it",
  )
  parser.add_argument(
    "--new-server-port",
    type=int,
    required=True,
    help="port on a localhost for the new server that is handled by `localhost-throttle`. Clients should connect to this port.",
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
  return parser
