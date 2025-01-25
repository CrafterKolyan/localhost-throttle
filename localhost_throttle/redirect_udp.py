import socketserver


def create_udp_server_request_handler_with_payload(*, in_port):
  def create_udp_server_request_handler(*args, **kwargs):
    class UDPServerRequestHandler(socketserver.DatagramRequestHandler):
      def handle(self):
        message, out_socket = self.request
        # TODO: Should be a different socket
        out_socket.sendto(message, ("localhost", in_port))

    return UDPServerRequestHandler(*args, **kwargs)

  return create_udp_server_request_handler


def redirect_udp(in_port, out_port, hostname="", poll_interval=0.1):
  with socketserver.UDPServer(
    (hostname, out_port),
    create_udp_server_request_handler_with_payload(in_port=in_port),
    bind_and_activate=True,
  ) as server:
    server.serve_forever(poll_interval=poll_interval)
