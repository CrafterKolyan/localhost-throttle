import contextlib
import socket
import time

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DELAY_TO_START_UP
from .util import spawn_localhost_throttle, random_port


class TCPSingleConnectionTest:
  def __init__(self):
    self._in_socket = None
    self._out_socket = None
    self._in_socket_out = None
    self._process = None

  def __enter__(self):
    protocol = Protocol.TCP
    socket_type = protocol.socket_type()
    in_socket = socket.socket(socket.AF_INET, socket_type)
    out_socket = socket.socket(socket.AF_INET, socket_type)
    # TODO: Need to use `RunIfException` here in case the exception is thrown here
    in_socket.bind(("localhost", 0))
    in_socket.listen(1)
    in_port = in_socket.getsockname()[1]
    out_port = random_port(socket_type)

    self._in_socket = in_socket
    self._out_socket = out_socket
    self._process = spawn_localhost_throttle(in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol]))
    # TODO: Due to this `time.sleep` `RunIfException` becomes even more critical
    time.sleep(DELAY_TO_START_UP)

    out_socket.connect(("localhost", out_port))
    in_socket_out, _ = in_socket.accept()
    self._in_socket_out = in_socket_out
    return (self._in_socket_out, self._out_socket, self._process)

  def __exit__(self, exc_type, exc_value, traceback):
    with contextlib.closing(self._in_socket):
      with contextlib.closing(self._out_socket):
        with contextlib.closing(self._in_socket_out):
          self._process.kill()


@pytest.mark.timeout(5)
def test_redirects_data_in_to_out():
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    data_to_send = b"1"
    in_socket_out.send(data_to_send)
    data_to_receive = out_socket.recv(len(data_to_send))
    assert data_to_send == data_to_receive, "Data received is not equal to data send"


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in():
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    data_to_send = b"1"
    out_socket.send(data_to_send)
    data_to_receive = in_socket_out.recv(len(data_to_send))
    assert data_to_send == data_to_receive, "Data received is not equal to data send"


@pytest.mark.timeout(3)
def test_redirects_data_in_to_out_to_in():
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    data_to_send = b"1"
    in_socket_out.send(data_to_send)
    data_to_receive = out_socket.recv(len(data_to_send))
    assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

    data_to_send = b"2"
    out_socket.send(data_to_send)
    data_to_receive = in_socket_out.recv(len(data_to_send))
    assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"


@pytest.mark.timeout(3)
def test_redirects_data_multiple_hops():
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    messages = [str(x).encode("utf-8") for x in range(100)]
    for data_to_send in messages:
      in_socket_out.send(data_to_send)
      data_to_receive = out_socket.recv(len(data_to_send))
      assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"
      in_socket_out, out_socket = out_socket, in_socket_out


@pytest.mark.timeout(3)
@pytest.mark.parametrize("n", [0, 1, 2, 5])
def test_end_of_connection_from_server_is_propagated_after_n_messages(n):
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    messages = [str(x).encode("utf-8") for x in range(2 * n)]
    for i in range(n):
      data_to_send = messages[2 * i]
      in_socket_out.send(data_to_send)
      data_to_receive = out_socket.recv(len(data_to_send))
      assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

      data_to_send = messages[2 * i + 1]
      out_socket.send(data_to_send)
      data_to_receive = in_socket_out.recv(len(data_to_send))
      assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

    in_socket_out.shutdown(socket.SHUT_RDWR)
    data_to_receive = out_socket.recv(1)
    expected = b""
    assert data_to_receive == expected, f"Data received is not equal to data send. ({expected=}, {data_to_receive=})"


@pytest.mark.timeout(3)
@pytest.mark.parametrize("n", [0, 1, 2, 5])
def test_end_of_connection_from_client_is_propagated_after_n_messages(n):
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    messages = [str(x).encode("utf-8") for x in range(2 * n - 1)]
    for i in range(n):
      data_to_send = messages[2 * i]
      in_socket_out.send(data_to_send)
      data_to_receive = out_socket.recv(len(data_to_send))
      assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

      if i + 1 != n:
        data_to_send = messages[2 * i + 1]
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(len(data_to_send))
        assert data_to_send == data_to_receive, f"Data received is not equal to data send. ({data_to_send=}, {data_to_receive=})"

    out_socket.shutdown(socket.SHUT_RDWR)
    data_to_receive = in_socket_out.recv(1)
    expected = b""
    assert data_to_receive == expected, f"Data received is not equal to data send. ({expected=}, {data_to_receive=})"
