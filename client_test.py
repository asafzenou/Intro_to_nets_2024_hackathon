import socket
import struct

MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

udp_port = 13117

# Listen for UDP Broadcast
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(("", udp_port))
    print(f"Listening for UDP broadcast on port {udp_port}...")

    while True:
        data, address = udp_socket.recvfrom(1024)
        if len(data) >= 9:
            magic_cookie, message_type, recv_udp_port, recv_tcp_port = struct.unpack('>IBHH', data[:9])
            if magic_cookie == MAGIC_COOKIE and message_type == OFFER_TYPE:
                print(f"Received offer from {address[0]}: UDP port {recv_udp_port}, TCP port {recv_tcp_port}")
