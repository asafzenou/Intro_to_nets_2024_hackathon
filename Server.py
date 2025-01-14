import socket
import struct
import threading
import time
import random

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
MULTICAST_GROUP = "224.0.0.1"
MULTICAST_PORT = 13117

class Server:
    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)

    def multicast_offers(self):
        """Send multicast UDP offers to clients."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # Set multicast TTL
            while True:
                offer_packet = struct.pack('>IBHH', MAGIC_COOKIE, OFFER_TYPE, self.udp_port, self.tcp_port)
                udp_socket.sendto(offer_packet, (MULTICAST_GROUP, MULTICAST_PORT))
                print(f"Multicasting offer: UDP {self.udp_port}, TCP {self.tcp_port}")
                time.sleep(1)

    def handle_tcp_client(self, client_socket):
        """Handle TCP client communication."""
        try:
            data = client_socket.recv(1024).decode()
            file_size = int(data.strip())
            payload = b'1' * file_size
            client_socket.sendall(payload)
            print(f"Sent {file_size} bytes over TCP.")
        except Exception as e:
            print(f"Error handling TCP client: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Start the server."""
        print(f"Server started. UDP port: {self.udp_port}, TCP port: {self.tcp_port}")

        # Start multicasting offers
        threading.Thread(target=self.multicast_offers, daemon=True).start()

        # Listen for TCP connections
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(("", self.tcp_port))
            tcp_socket.listen(5)
            print("Listening for TCP connections...")

            while True:
                client_socket, addr = tcp_socket.accept()
                print(f"Accepted TCP connection from {addr}")
                threading.Thread(target=self.handle_tcp_client, args=(client_socket,), daemon=True).start()
