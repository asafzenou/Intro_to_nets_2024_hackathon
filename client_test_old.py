import socket
import struct

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

def start_unicast_client():
    """Listen for unicast UDP messages."""
    udp_port = 13117  # Client's listening port

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', udp_port))  # Bind to the specified port
        print(f"Listening for unicast messages on port {udp_port}...")

        while True:
            try:
                data, address = udp_socket.recvfrom(1024)
                if len(data) >= 9:
                    # Unpack the received packet
                    magic_cookie, message_type, recv_udp_port, recv_tcp_port = struct.unpack('>IBHH', data[:9])
                    if magic_cookie == MAGIC_COOKIE and message_type == OFFER_TYPE:
                        print(f"Received unicast offer from {address[0]}: UDP port {recv_udp_port}, TCP port {recv_tcp_port}")
            except Exception as e:
                print(f"Error receiving packet: {e}")

if __name__ == "__main__":
    start_unicast_client()
