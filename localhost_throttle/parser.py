import argparse
from .protocol_type import ProtocolSet


def create_parser():
  parser = argparse.ArgumentParser(description="Throttle localhost connection")
  parser.add_argument("--in-port", type=int, required=True, help="port on a localhost from which localhost-throttle receives data")
  parser.add_argument("--out-port", type=int, required=True, help="port on a localhost to which localhost-throttle outputs data")
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
