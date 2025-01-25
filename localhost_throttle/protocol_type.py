import enum
import socket


@enum.unique
class Protocol(enum.Enum):
  TCP = enum.auto()
  UDP = enum.auto()

  def from_string(str):
    str = str.lower()
    match str:
      case "tcp":
        return Protocol.TCP
      case "udp":
        return Protocol.UDP
      case _:
        raise ValueError(f"'{str}' is not a valid Protocol. Only 'tcp' and 'udp' are supported")

  def __str__(self):
    match self:
      case Protocol.TCP:
        return "tcp"
      case Protocol.UDP:
        return "udp"

  def socket_type(self):
    match self:
      case Protocol.TCP:
        return socket.SOCK_STREAM
      case Protocol.UDP:
        return socket.SOCK_DGRAM


class ProtocolSet(set):
  @staticmethod
  def from_string(str):
    str = str.lower()
    protocols = str.split(",")
    protocols = [Protocol.from_string(x) for x in protocols]
    return ProtocolSet(protocols)

  @staticmethod
  def from_iterable(protocols):
    return ProtocolSet(protocols)

  def __str__(self):
    return ",".join(str(x) for x in self)
