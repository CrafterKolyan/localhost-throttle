import contextlib
import logging
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
          out_socket.shutdown(socket.SHUT_RDWR)
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
  def __init__(self, in_addr, out_addr, in_socket, out_socket, buffer_size=65536):
    self.in_addr = in_addr
    self.in_socket = in_socket
    self.out_socket = out_socket
    self.out_addr = out_addr
    self.buffer_size = buffer_size
    self._stopped = None
    self._thread = None

  def _start_redirect_blocking(self, in_addr, out_addr, in_socket, out_socket, first_message):
    buffer_size = self.buffer_size
    in_socket.sendto(first_message, in_addr)
    while not self._stopped.isSet():
      try:
        data, _ = in_socket.recvfrom(buffer_size)
        out_socket.sendto(data, out_addr)
        if len(data) == 0:
          self._stopped.set()
          break

        # in_addr, out_addr = out_addr, in_addr
      except OSError:
        self._stopped.set()

  def start(self, first_message):
    self._stopped = threading.Event()
    self._thread = threading.Thread(
      target=self._start_redirect_blocking,
      args=(self.in_addr, self.out_addr, self.in_socket, self.out_socket, first_message),
      daemon=True,
    )
    self._thread.start()

  def stop(self):
    self._stopped.set()


def redirect_and_close_on_exception_tcp(*, client_socket, client_address, in_port):
  with contextlib.closing(client_socket) as client_socket:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as in_socket:
      in_socket.connect(("localhost", in_port))
      redirect_in_to_client = RedirectClientTCP(in_socket, client_socket)
      redirect_in_to_client.start()
      redirect_in_to_client._stopped.wait()
  logging.info(f"Closed connection to {client_address}")


def redirect_and_close_on_exception_udp(*, in_port, client_address, first_message, out_socket, socket_obj):
  with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as in_socket:
    socket_obj.append(in_socket)
    redirect_in_to_client = RedirectClientUDP(("localhost", in_port), client_address, in_socket, out_socket)
    redirect_in_to_client.start(first_message)
    redirect_in_to_client._stopped.wait()
  logging.info(f"Closed UDP connection to {client_address}")
