import socket
import struct
import time

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2

class Client:
    def listen_for_offers(self):
        """Listen for server offers via UDP broadcast."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.bind(('', 13117))
            print("Client listening for broadcast offers on port 13117...")

            while True:
                data, address = udp_socket.recvfrom(1024)
                if len(data) >= 9:
                    magic_cookie, message_type, udp_port, tcp_port = struct.unpack('>IBHH', data[:9])
                    if magic_cookie == MAGIC_COOKIE and message_type == OFFER_TYPE:
                        print(f"Received offer from {address[0]} - UDP port {udp_port}, TCP port {tcp_port}")
                        return address[0], tcp_port

    def start(self):
        """Start the client."""
        server_ip, tcp_port = self.listen_for_offers()
        file_size = int(input("Enter file size in bytes: "))

        # Connect to the server via TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((server_ip, tcp_port))
            tcp_socket.sendall(f"{file_size}\n".encode())
            start_time = time.time()
            data = tcp_socket.recv(file_size)
            elapsed = time.time() - start_time
            print(f"Received {len(data)} bytes over TCP in {elapsed:.2f} seconds.")
