import socket
import struct
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

udp_port = 13117

# Broadcast UDP Offer
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(("", 0))  # Bind to any available port

    while True:
        offer_packet = struct.pack('>IBHH', MAGIC_COOKIE, OFFER_TYPE, udp_port, udp_port)
        udp_socket.sendto(offer_packet, ('<broadcast>', udp_port))
        print(f"Broadcasting offer on port {udp_port}")
        time.sleep(1)
