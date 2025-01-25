import contextlib
import socket
import time

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DELAY_TO_START_UP
from .util import spawn_localhost_throttle


def random_port():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.bind(("localhost", 0))
    return sock.getsockname()[1]


@pytest.mark.timeout(5)
def test_redirects_data_in_to_out():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        in_socket_out.send(data_to_send)
        data_to_receive = out_socket.recv(len(data_to_send))
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(len(data_to_send))
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_in_to_out_to_in():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        in_socket_out.send(data_to_send)
        data_to_receive = out_socket.recv(len(data_to_send))
        assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

        data_to_send = b"2"
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(len(data_to_send))
        assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_multiple_hops():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()

        messages = [str(x).encode("utf-8") for x in range(100)]
        for data_to_send in messages:
          in_socket_out.send(data_to_send)
          data_to_receive = out_socket.recv(len(data_to_send))
          assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"
          in_socket_out, out_socket = out_socket, in_socket_out
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_end_of_connection_is_propagated():
  protocol = Protocol.TCP
  socket_type = protocol.socket_type()
  with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
      try:
        time.sleep(DELAY_TO_START_UP)
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        in_socket_out.send(data_to_send)
        data_to_receive = out_socket.recv(len(data_to_send))
        assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

        data_to_send = b"2"
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(len(data_to_send))
        assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

        in_socket_out.shutdown(socket.SHUT_RDWR)
        data_to_receive = out_socket.recv(1)
        expected = b""
        assert data_to_receive == expected, f"Data received is not equal to data send. ({expected=}, {data_to_receive=})"
      finally:
        process.kill()
