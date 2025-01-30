import pytest

from .util import TCPSingleConnectionTest


@pytest.mark.timeout(5)
def test_slows_down_data_transfer_tcp():
  with TCPSingleConnectionTest(bandwidth=5) as (in_socket_out, out_socket, _):
    out_socket.settimeout(0.1)
    data_to_send = b"1"
    in_socket_out.send(data_to_send)
    with pytest.raises(TimeoutError):
      data_to_receive = out_socket.recv(len(data_to_send))
    out_socket.settimeout(0.5)
    data_to_receive = out_socket.recv(len(data_to_send))
    assert data_to_send == data_to_receive, f"Data received is not equal to data send. {data_to_send=}, {data_to_receive=}"
