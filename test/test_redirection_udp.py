import contextlib
import socket
import time

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DELAY_TO_START_UP
from .util import spawn_localhost_throttle


def random_ports(size=1):
  try:
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(size)]
    ports = []
    for sock in sockets:
      sock.bind(("localhost", 0))
      ports.append(sock.getsockname()[1])
    return ports
  finally:
    for sock in sockets:
      sock.close()


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in():
  protocol = Protocol.UDP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      ports = random_ports(size=1)
      out_port = ports[0]

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        data_to_send = b"1"
        out_socket.sendto(data_to_send, ("localhost", out_port))
        data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in_to_out():
  protocol = Protocol.UDP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      ports = random_ports(size=1)
      out_port = ports[0]

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        data_to_send = b"1"
        out_socket.sendto(data_to_send, ("localhost", out_port))
        data_to_receive, addr = in_socket.recvfrom(len(data_to_send))
        assert data_to_send == data_to_receive, "Data received is not equal to data send"

        data_to_send = b"2"
        in_socket.sendto(data_to_send, addr)
        data_to_receive, addr = out_socket.recvfrom(len(data_to_send))
        assert data_to_send == data_to_receive, "Data received is not equal to data send"

      finally:
        process.kill()
