import contextlib
import socket

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .util import spawn_localhost_throttle


def random_port():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.bind(("localhost", 0))
    return sock.getsockname()[1]


@pytest.mark.timeout(5)
def test_redirects_data():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([Protocol.TCP]))
      try:
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        in_socket_out.send(data_to_send)
        data_to_receive = out_socket.recv(1)
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_in_opposite_direction():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([Protocol.TCP]))
      try:
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(1)
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_back_and_forth():
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as out_socket:
      in_socket.bind(("localhost", 0))
      in_socket.listen(1)
      in_port = in_socket.getsockname()[1]
      out_port = random_port()

      process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([Protocol.TCP]))
      try:
        out_socket.connect(("localhost", out_port))
        in_socket_out, _ = in_socket.accept()
        data_to_send = b"1"
        in_socket_out.send(data_to_send)
        data_to_receive = out_socket.recv(1)
        assert data_to_send == data_to_receive, "Data received is not equal to data send"

        data_to_send = b"2"
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(1)
        assert data_to_send == data_to_receive, "Data received is not equal to data send"
      finally:
        process.kill()
