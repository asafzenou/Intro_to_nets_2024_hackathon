import socket
import struct
import time

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

def start_unicast_server(client_ip, client_port):
    """Send unicast UDP message to a specific client."""
    udp_port = 13117  # Server's UDP port

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind(("", 0))  # Bind to any available port

        while True:
            # Prepare an offer packet
            offer_packet = struct.pack('>IBHH', MAGIC_COOKIE, OFFER_TYPE, udp_port, udp_port)
            udp_socket.sendto(offer_packet, (client_ip, client_port))
            print(f"Sent unicast offer to {client_ip}:{client_port}")
            time.sleep(1)

if __name__ == "__main__":
    client_ip = "10.100.102.20"  # Replace with the client's IP
    client_port = 13117  # Client's listening port
    start_unicast_server(client_ip, client_port)
