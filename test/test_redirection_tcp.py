import socket

import pytest

from .util import TCPSingleConnectionTest


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
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )

    data_to_send = b"2"
    out_socket.send(data_to_send)
    data_to_receive = in_socket_out.recv(len(data_to_send))
    assert data_to_send == data_to_receive, (
      f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
    )


@pytest.mark.timeout(3)
def test_redirects_data_multiple_hops():
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    messages = [str(x).encode("utf-8") for x in range(100)]
    for data_to_send in messages:
      in_socket_out.send(data_to_send)
      data_to_receive = out_socket.recv(len(data_to_send))
      assert data_to_send == data_to_receive, (
        f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
      )
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
      assert data_to_send == data_to_receive, (
        f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
      )

      data_to_send = messages[2 * i + 1]
      out_socket.send(data_to_send)
      data_to_receive = in_socket_out.recv(len(data_to_send))
      assert data_to_send == data_to_receive, (
        f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
      )

    in_socket_out.shutdown(socket.SHUT_RDWR)
    data_to_receive = out_socket.recv(1)
    expected = b""
    assert data_to_receive == expected, f"Shutdown was expected. (expected: {expected}, got: {data_to_receive})"


@pytest.mark.timeout(3)
@pytest.mark.parametrize("n", [0, 1, 2, 5])
def test_end_of_connection_from_client_is_propagated_after_n_messages(n):
  with TCPSingleConnectionTest() as (in_socket_out, out_socket, _):
    messages = [str(x).encode("utf-8") for x in range(2 * n - 1)]
    for i in range(n):
      data_to_send = messages[2 * i]
      in_socket_out.send(data_to_send)
      data_to_receive = out_socket.recv(len(data_to_send))
      assert data_to_send == data_to_receive, (
        f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
      )

      if i + 1 != n:
        data_to_send = messages[2 * i + 1]
        out_socket.send(data_to_send)
        data_to_receive = in_socket_out.recv(len(data_to_send))
        assert data_to_send == data_to_receive, (
          f"Data received is not equal to data send. (sent: {data_to_send}, got: {data_to_receive})"
        )

    out_socket.shutdown(socket.SHUT_RDWR)
    data_to_receive = in_socket_out.recv(1)
    expected = b""
    assert data_to_receive == expected, f"Shutdown was expected. (expected: {expected}, got: {data_to_receive})"
