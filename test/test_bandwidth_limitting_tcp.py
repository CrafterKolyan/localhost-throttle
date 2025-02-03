import pytest

from .constants import TIME_FOR_PROCESS_TO_FINISH
from .util import TCPSingleConnectionTest, interrupt_process


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


@pytest.mark.timeout(5)
def test_can_be_interrupted_on_long_transfer():
  with TCPSingleConnectionTest(bandwidth=5) as (in_socket_out, out_socket, process):
    data_to_send = b"1" * 100
    in_socket_out.send(data_to_send)
    out_socket.settimeout(0.1)
    with pytest.raises(TimeoutError):
      _ = out_socket.recv(len(data_to_send))

    interrupt_process(process)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)


@pytest.mark.timeout(5)
def test_can_be_interrupted_on_long_transfer_back():
  with TCPSingleConnectionTest(bandwidth=5) as (in_socket_out, out_socket, process):
    data_to_send = b"1" * 100
    out_socket.send(data_to_send)
    in_socket_out.settimeout(0.1)
    with pytest.raises(TimeoutError):
      _ = in_socket_out.recv(len(data_to_send))

    interrupt_process(process)
    process.communicate(timeout=TIME_FOR_PROCESS_TO_FINISH)
