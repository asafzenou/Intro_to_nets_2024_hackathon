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
        self.SERVER_UDP_PORT = random.randint(20000, 30000)
        self.SERVER_TCP_PORT = random.randint(30001, 40000)

    def udp_offer_broadcast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                offer_packet = struct.pack(
                    '>IBHH', MAGIC_COOKIE, OFFER_TYPE, self.SERVER_UDP_PORT, self.SERVER_TCP_PORT)
                udp_socket.sendto(offer_packet, ('<broadcast>', 13117))
                print("Offer broadcast sent")
                time.sleep(1)

    def handle_client_tcp(self, client_socket):
        try:
            data = client_socket.recv(1024).decode()
            file_size = int(data.strip())
            payload = b'1' * file_size
            client_socket.sendall(payload)
            print(f"TCP: Sent {file_size} bytes")
        except Exception as e:
            print(f"Error in TCP handler: {e}")
        finally:
            client_socket.close()

    def handle_client_udp(self, server_udp_socket, client_address, file_size):
        segment_count = 0
        total_segments = file_size // 1024 + (1 if file_size % 1024 else 0)

        try:
            for i in range(total_segments):
                payload_packet = struct.pack(
                    '>IBQQ', MAGIC_COOKIE, PAYLOAD_TYPE, total_segments, i + 1
                ) + b'1' * 1024
                server_udp_socket.sendto(payload_packet, client_address)
                segment_count += 1
                time.sleep(0.001)  # Simulate slight delay
            print(f"UDP: Sent {segment_count} segments to {client_address}")
        except Exception as e:
            print(f"Error in UDP handler: {e}")

    def start(self):
        print(f"Server started. UDP port: {self.SERVER_UDP_PORT}, TCP port: {self.SERVER_TCP_PORT}")

        threading.Thread(target=self.udp_offer_broadcast, daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(("", self.SERVER_TCP_PORT))
            tcp_socket.listen(5)
            print("Listening for TCP connections...")

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.bind(("", self.SERVER_UDP_PORT))
                print("Listening for UDP requests...")

                while True:
                    import select
                    ready_sockets, _, _ = select.select([tcp_socket, udp_socket], [], [])

                    for sock in ready_sockets:
                        if sock == tcp_socket:
                            client_socket, _ = tcp_socket.accept()
                            threading.Thread(target=self.handle_client_tcp, args=(client_socket,), daemon=True).start()

                        elif sock == udp_socket:
                            data, client_address = udp_socket.recvfrom(1024)
                            if len(data) >= 13:
                                magic_cookie, message_type, file_size = struct.unpack('>IBQ', data[:13])
                                if magic_cookie == MAGIC_COOKIE and message_type == REQUEST_TYPE:
                                    threading.Thread(
                                        target=self.handle_client_udp, args=(udp_socket, client_address, file_size), daemon=True).start()