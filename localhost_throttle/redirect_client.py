import contextlib
import threading
import socket


class RedirectClientTCP:
  # TODO: Customize buffer_size
  def __init__(self, in_socket, out_socket, buffer_size=65536):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.buffer_size = buffer_size
    self._stopped = None
    self._thread_in_to_out = None
    self._thread_out_to_in = None

  def _start_redirect_blocking(self, in_socket, out_socket):
    buffer_size = self.buffer_size
    while not self._stopped.isSet():
      try:
        data = in_socket.recv(buffer_size)
        if len(data) == 0:
          self._stopped.set()
          break
        out_socket.send(data)
      except OSError:
        self._stopped.set()

  def start(self):
    self._stopped = threading.Event()
    self._thread_in_to_out = threading.Thread(
      target=self._start_redirect_blocking, args=(self.in_socket, self.out_socket), daemon=True
    )
    self._thread_in_to_out.start()
    self._thread_out_to_in = threading.Thread(
      target=self._start_redirect_blocking, args=(self.out_socket, self.in_socket), daemon=True
    )
    self._thread_out_to_in.start()

  def stop(self):
    self._stopped.set()


class RedirectClientUDP:
  # TODO: Customize buffer_size
  def __init__(self, in_socket, in_out_socket, out_socket, buffer_size=65536):
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.in_out_socket = in_out_socket
    self.buffer_size = buffer_size
    self._stopped = None
    self._thread_in_to_out = None
    self._thread_out_to_in = None

  def _start_redirect_blocking(self, in_socket, out_socket):
    buffer_size = self.buffer_size
    while not self._stopped.isSet():
      try:
        data = out_socket.recvfrom(buffer_size)
        if len(data) == 0:
          self._stopped.set()
          break
        in_socket.sendto(data)
      except OSError:
        self._stopped.set()

  def start(self):
    self._stopped = threading.Event()
    self._thread_in_to_out = threading.Thread(
      target=self._start_redirect_blocking, args=(self.in_socket, self.out_socket), daemon=True
    )
    self._thread_in_to_out.start()
    self._thread_out_to_in = threading.Thread(
      target=self._start_redirect_blocking, args=(self.out_socket, self.in_socket), daemon=True
    )
    self._thread_out_to_in.start()

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_tcp(*, client_socket, in_port):
  with contextlib.closing(client_socket) as client_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
      in_socket.connect(("localhost", in_port))
      redirect_in_to_client = RedirectClientTCP(in_socket, client_socket)
      redirect_in_to_client.start()
      redirect_in_to_client._stopped.wait()


def redirect_and_close_on_exception_udp(*, client_socket, in_port, socket_type):
  with contextlib.closing(client_socket) as client_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket_type)) as in_out_socket:
      redirect_in_to_client = RedirectClientUDP(in_socket, client_socket)
      redirect_in_to_client.start()
      redirect_in_to_client._stopped.wait()
