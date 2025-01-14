import socket
import struct
import threading
import time
import random

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4

class Server:
    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)

    def broadcast_offers(self):
        """Broadcast UDP offers to clients."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                offer_packet = struct.pack('>IBHH', MAGIC_COOKIE, OFFER_TYPE, self.udp_port, self.tcp_port)
                udp_socket.sendto(offer_packet, ('<broadcast>', 13117))
                print(f"Broadcasting offer: UDP {self.udp_port}, TCP {self.tcp_port}")
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

    def handle_udp_request(self, udp_socket, client_address, file_size):
        """Handle UDP data transfer."""
        total_segments = file_size // 1024 + (1 if file_size % 1024 else 0)
        try:
            for i in range(total_segments):
                payload = struct.pack('>IBQQ', MAGIC_COOKIE, PAYLOAD_TYPE, total_segments, i + 1) + b'1' * 1024
                udp_socket.sendto(payload, client_address)
            print(f"Sent {total_segments} UDP segments to {client_address}.")
        except Exception as e:
            print(f"Error handling UDP client: {e}")

    def start(self):
        """Start the server."""
        print(f"Server started. UDP port: {self.udp_port}, TCP port: {self.tcp_port}")
        threading.Thread(target=self.broadcast_offers, daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(("", self.tcp_port))
            tcp_socket.listen(5)
            print("Listening for TCP connections...")

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.bind(("", self.udp_port))
                print("Listening for UDP requests...")

                while True:
                    ready, _, _ = socket.select.select([tcp_socket, udp_socket], [], [])
                    for sock in ready:
                        if sock == tcp_socket:
                            client_socket, _ = tcp_socket.accept()
                            threading.Thread(target=self.handle_tcp_client, args=(client_socket,), daemon=True).start()
                        elif sock == udp_socket:
                            data, addr = udp_socket.recvfrom(1024)
                            if len(data) >= 13:
                                magic_cookie, message_type, file_size = struct.unpack('>IBQ', data[:13])
                                if magic_cookie == MAGIC_COOKIE and message_type == REQUEST_TYPE:
                                    threading.Thread(
                                        target=self.handle_udp_request, args=(udp_socket, addr, file_size), daemon=True
                                    ).start()
