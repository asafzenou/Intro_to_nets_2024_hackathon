import socket
import struct
import threading
import time
import random

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

class Server:
    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)

    def broadcast_offers(self):
        """Broadcast UDP offers to clients."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.bind(("", 0))  # Bind to any available port

            while True:
                # Prepare an offer packet
                offer_packet = struct.pack('>IBHH', MAGIC_COOKIE, OFFER_TYPE, self.udp_port, self.tcp_port)
                udp_socket.sendto(offer_packet, ('255.255.255.255', 13117))
                print(f"Broadcasting offer: UDP {self.udp_port}, TCP {self.tcp_port}")
                time.sleep(1)

    def handle_tcp_client(self, client_socket):
        """Handle TCP communication."""
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

        # Start broadcasting offers
        threading.Thread(target=self.broadcast_offers, daemon=True).start()

        # Listen for TCP connections
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(("", self.tcp_port))
            tcp_socket.listen(5)
            print("Listening for TCP connections...")

            while True:
                client_socket, addr = tcp_socket.accept()
                print(f"Accepted TCP connection from {addr}")
                threading.Thread(target=self.handle_tcp_client, args=(client_socket,), daemon=True).start()
