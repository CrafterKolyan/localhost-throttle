import pytest

from .constants import TIME_FOR_PROCESS_TO_FINISH
from .util import UDPSingleConnectionTest, interrupt_process


@pytest.mark.timeout(3)
def test_slows_down_data_out_to_in():
  with UDPSingleConnectionTest(bandwidth=5) as (in_socket, out_socket, _, out_port):
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    in_socket.settimeout(0.1)
    with pytest.raises(TimeoutError):
      data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
    in_socket.settimeout(0.5)
    data_to_receive, _ = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, f"Data received is not equal to data send. {data_to_send=}, {data_to_receive=}"


@pytest.mark.timeout(5)
def test_can_be_interrupted_on_long_transfer():
  with UDPSingleConnectionTest(bandwidth=5) as (in_socket, out_socket, process, out_port):
    data_to_send = b"1" * 100
    out_socket.sendto(data_to_send, ("localhost", out_port))
    in_socket.settimeout(0.1)
    with pytest.raises(TimeoutError):
      _, _ = in_socket.recvfrom(len(data_to_send))

    interrupt_process(process)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)


@pytest.mark.timeout(5)
def test_can_be_interrupted_on_long_transfer_back():
  with UDPSingleConnectionTest(bandwidth=5) as (in_socket, out_socket, process, out_port):
    data_to_send = b"1"
    out_socket.sendto(data_to_send, ("localhost", out_port))
    in_socket.settimeout(0.5)
    data_to_receive, in_addr = in_socket.recvfrom(len(data_to_send))
    assert data_to_send == data_to_receive, f"Data received is not equal to data send. {data_to_send=}, {data_to_receive=}"

    data_to_send = b"1" * 100
    out_socket.sendto(data_to_send, in_addr)
    out_socket.settimeout(0.1)
    with pytest.raises(TimeoutError):
      _, _ = out_socket.recvfrom(len(data_to_send))

    interrupt_process(process)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
