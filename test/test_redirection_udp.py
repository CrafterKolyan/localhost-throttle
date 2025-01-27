import contextlib
import socket
import time

import pytest

from localhost_throttle import Protocol, ProtocolSet

from .constants import DELAY_TO_START_UP
from .util import spawn_localhost_throttle, random_port


class UDPSingleConnectionTest:
  def __init__(self):
    self._in_socket = None
    self._out_socket = None
    self._process = None
    self._out_port = None

  def __enter__(self):
    protocol = Protocol.UDP
    socket_type = protocol.socket_type()
    in_socket = socket.socket(socket.AF_INET, socket_type)
    try:
      # TODO: Need to use `RunIfException` here in case the exception is thrown here
      in_socket.bind(("localhost", 0))
      in_port = in_socket.getsockname()[1]
      out_port = random_port(socket_type)
      self._in_socket = in_socket
      self._out_socket = socket.socket(socket.AF_INET, socket_type)
      try:
        self._process = spawn_localhost_throttle(
          in_port=in_port, out_port=out_port, protocols=ProtocolSet.from_iterable([protocol])
        )
        try:
          self._out_port = out_port
          # TODO: Due to this `time.sleep` `RunIfException` becomes even more critical
          time.sleep(DELAY_TO_START_UP)
        except BaseException:
          self._process.kill()
      except BaseException:
        self._out_socket.close()
    except BaseException:
      in_socket.close()
    return (self._in_socket, self._out_socket, self._process, self._out_port)

  def __exit__(self, exc_type, exc_value, traceback):
    with contextlib.closing(self._in_socket):
      with contextlib.closing(self._out_socket):
        self._process.kill()


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in():
  with UDPSingleConnectionTest() as (in_socket, out_socket, _, out_port):
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, "Data received is not equal to data send"


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in_to_out():
  with UDPSingleConnectionTest() as (in_socket, out_socket, _, out_port):
    time.sleep(DELAY_TO_START_UP)
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    data_to_receive, addr = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )

    data_to_send = b"2"
    in_socket.sendto(data_to_send, addr)
    data_to_receive, addr = out_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )


@pytest.mark.timeout(3)
def test_redirects_data_client_receives_data_from_the_same_port():
  with UDPSingleConnectionTest() as (in_socket, out_socket, _, out_port):
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    data_to_receive, addr = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )

    data_to_send = b"2"
    in_socket.sendto(data_to_send, addr)
    data_to_receive, addr = out_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )
    assert addr[1] == out_port, (
      f"Port for client's addressee has changed. (client sent message to: '{out_port}' but received from '{addr[1]}')"
    )


@pytest.mark.timeout(3)
def test_redirects_data_multiple_hops():
  with UDPSingleConnectionTest() as (in_socket, out_socket, _, out_port):
    messages = [str(x).encode("utf-8") for x in range(100)]
    out_addr = ("localhost", out_port)
    for data_to_send in messages:
      out_socket.sendto(data_to_send, out_addr)
      data_to_receive, in_addr = in_socket.recvfrom(len(data_to_send))
      assert data_to_send == data_to_receive, (
        f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
      )
      in_socket, out_socket = out_socket, in_socket
      in_addr, out_addr = out_addr, in_addr
