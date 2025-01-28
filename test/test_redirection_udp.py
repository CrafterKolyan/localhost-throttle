import pytest


from .util import UDPSingleConnectionTest


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
