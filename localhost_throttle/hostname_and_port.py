class HostnameAndPort:
  def __init__(self, hostname: str, port: int):
    self.hostname = hostname
    self.port = port

  def to_address(self) -> tuple[str, int]:
    return (self.hostname, self.port)

  @staticmethod
  def from_string(str_: str):
    hostname, port = str_.rsplit(":", maxsplit=1)
    port = int(port)
    return HostnameAndPort(hostname, port)

  def to_string(self) -> str:
    return f"{self.hostname}:{self.port}"

  def __str__(self) -> str:
    return self.to_string()
