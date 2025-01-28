import pytest

from .util import UDPSingleConnectionTest


@pytest.mark.timeout(3)
def test_redirects_data_out_to_in():
  with UDPSingleConnectionTest(bandwidth=5) as (in_socket, out_socket, _, out_port):
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    in_socket.settimeout(0.1)
    with pytest.raises(TimeoutError):
      data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
    in_socket.settimeout(0.2)
    data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, "Data received is not equal to data send"
