import socket
import struct
import threading
import time
import random

from Server import Server

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4


class Client:
    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(('', 13117))
            print("Client listening for offers...")

            while True:
                data, address = udp_socket.recvfrom(1024)
                if len(data) >= 9:
                    magic_cookie, message_type, udp_port, tcp_port = struct.unpack('>IBHH', data[:9])
                    if magic_cookie == MAGIC_COOKIE and message_type == OFFER_TYPE:
                        print(f"Received offer from {address[0]} - UDP port {udp_port}, TCP port {tcp_port}")
                        return address[0], udp_port, tcp_port

    def send_requests(self, server_ip, udp_port, tcp_port, file_size, tcp_connections, udp_connections):
        def tcp_request():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.connect((server_ip, tcp_port))
                tcp_socket.sendall(f"{file_size}\n".encode())
                start_time = time.time()
                data = tcp_socket.recv(file_size)
                elapsed = time.time() - start_time
                print(f"TCP transfer finished in {elapsed:.2f}s")

        def udp_request():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                request_packet = struct.pack('>IBQ', MAGIC_COOKIE, REQUEST_TYPE, file_size)
                udp_socket.sendto(request_packet, (server_ip, udp_port))

                start_time = time.time()
                received_segments = 0

                while True:
                    udp_socket.settimeout(1)
                    try:
                        data, _ = udp_socket.recvfrom(2048)
                        if len(data) >= 21:
                            received_segments += 1
                    except socket.timeout:
                        break
                elapsed = time.time() - start_time
                print(f"UDP transfer finished in {elapsed:.2f}s, received {received_segments} segments")

        threads = []
        for _ in range(tcp_connections):
            threads.append(threading.Thread(target=tcp_request))

        for _ in range(udp_connections):
            threads.append(threading.Thread(target=udp_request))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def start(self):
        server_ip, udp_port, tcp_port = self.listen_for_offers()
        file_size = int(input("Enter file size in bytes: "))
        tcp_connections = int(input("Enter number of TCP connections: "))
        udp_connections = int(input("Enter number of UDP connections: "))

        self.send_requests(server_ip, udp_port, tcp_port, file_size, tcp_connections, udp_connections)



