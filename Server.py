#!/usr/bin/env python3
import socket
import struct
import threading
import time

# ==============================
# CONFIGURATION & CONSTANTS
# ==============================
VERSION = "1.1"  # Just to remind that this is example code for Hackathon v1.1
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

BROADCAST_IP = "10.100.102.255"
BROADCAST_PORT = 13117      # Usually the known port for receiving offers
BROADCAST_INTERVAL = 1.0    # seconds between broadcasts
TCP_BACKLOG = 5             # Maximum pending TCP connections

# For demo, we'll use these default ports for server to listen on:
SERVER_UDP_PORT = 2024
SERVER_TCP_PORT = 2025

# We will chunk the UDP data in segments of this size
UDP_PAYLOAD_SIZE = 1024
# Similarly, for TCP we can read/write in chunks
TCP_PAYLOAD_SIZE = 1024

# ==============================
# SERVER LOGIC
# ==============================
class SpeedTestServer:
    """
    SpeedTestServer class responsible for:
    1) Broadcasting offer messages via UDP.
    2) Handling client requests (TCP & UDP).
    """

    def __init__(self):
        # 1. Prepare a UDP socket for broadcasting offers
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 2. Prepare a TCP server socket to accept connections for file transfer
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server_socket.bind(('', SERVER_TCP_PORT))
        self.tcp_server_socket.listen(TCP_BACKLOG)

        # 3. Prepare a UDP server socket to listen for request packets
        self.udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_server_socket.bind(('', SERVER_UDP_PORT))

        self.running = True

    def start(self):
        """
        Start the server by launching threads for:
        1) Broadcasting offers
        2) Handling incoming TCP connections
        3) Handling incoming UDP requests
        """
        print(f"[Server] Version {VERSION} starting up.")
        ip_address = self.get_local_ip()
        print(f"[Server] Server started, listening on IP address {ip_address}")

        # Start broadcast thread
        broadcast_thread = threading.Thread(target=self.broadcast_offers, daemon=True)
        broadcast_thread.start()

        # Start TCP accept thread
        tcp_thread = threading.Thread(target=self.tcp_accept_loop, daemon=True)
        tcp_thread.start()

        # Start UDP handle thread
        udp_thread = threading.Thread(target=self.udp_handle_loop, daemon=True)
        udp_thread.start()

        # Main thread will just keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Server] Shutting down...")

        self.shutdown()

    def broadcast_offers(self):
        """
        Periodically broadcast an "offer" packet to all clients on the local network.
        """
        while self.running:
            try:
                # Prepare the offer message:
                # Magic cookie (4 bytes), Message type (1 byte), server UDP port (2 bytes), server TCP port (2 bytes)
                # Use network order (= big-endian) packing format: ! = network (big-endian)
                # I = unsigned int (4 bytes), B = unsigned char (1 byte), H = unsigned short (2 bytes)
                packet = struct.pack('!IBHH',
                                     MAGIC_COOKIE,
                                     MSG_TYPE_OFFER,
                                     SERVER_UDP_PORT,
                                     SERVER_TCP_PORT)

                self.broadcast_socket.sendto(packet, (BROADCAST_IP, BROADCAST_PORT))
            except Exception as e:
                print(f"[Server][broadcast_offers] Error: {e}")

            time.sleep(BROADCAST_INTERVAL)

    def tcp_accept_loop(self):
        """
        Accepts incoming TCP connections. For each connection, spawns a new thread to handle file transfer.
        """
        print(f"[Server][TCP] Listening on port {SERVER_TCP_PORT} for incoming connections.")
        while self.running:
            try:
                client_socket, client_address = self.tcp_server_socket.accept()
                print(f"[Server][TCP] New connection from {client_address}")
                threading.Thread(target=self.handle_tcp_client, args=(client_socket, client_address), daemon=True).start()
            except Exception as e:
                print(f"[Server][TCP] Accept error: {e}")
                break

    def handle_tcp_client(self, client_socket, client_address):
        """
        Read the file-size request from the client (in string form),
        then send the requested amount of data and close the connection.
        """
        try:
            data = b""
            while not data.endswith(b"\n"):
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data += chunk

            if data:
                # data is something like b"1000000\n"
                file_size_str = data.strip().decode()
                file_size = int(file_size_str)
                print(f"[Server][TCP] Client {client_address} requested {file_size} bytes (TCP).")

                # Send the requested amount of data
                bytes_sent = 0
                while bytes_sent < file_size:
                    to_send = min(TCP_PAYLOAD_SIZE, file_size - bytes_sent)
                    client_socket.sendall(b'X' * to_send)
                    bytes_sent += to_send

        except Exception as e:
            print(f"[Server][TCP] Error handling client {client_address}: {e}")
        finally:
            client_socket.close()

    def udp_handle_loop(self):
        """
        Listen for incoming request messages on self.udp_server_socket, then handle them in a new thread.
        """
        print(f"[Server][UDP] Listening on port {SERVER_UDP_PORT} for incoming requests.")
        while self.running:
            try:
                message, client_address = self.udp_server_socket.recvfrom(1024)
                # This should be a request packet
                # Magic cookie (4 bytes), Message type (1 byte), file_size (8 bytes)
                try:
                    unpacked = struct.unpack('!IBQ', message)
                    cookie, msg_type, file_size = unpacked
                    if cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_REQUEST:
                        print(f"[Server][UDP] Received request from {client_address}: file_size={file_size}")
                        threading.Thread(target=self.handle_udp_client,
                                         args=(client_address, file_size),
                                         daemon=True).start()
                except struct.error:
                    pass  # ignore malformed messages

            except Exception as e:
                print(f"[Server][UDP] Error: {e}")
                break

    def handle_udp_client(self, client_address, file_size):
        """
        Sends the requested `file_size` bytes in multiple UDP payload messages.
        Each packet:
          - Magic cookie (4 bytes)
          - msg_type (1 byte)
          - total_segment_count (8 bytes)
          - current_segment_index (8 bytes)
          - payload (UDP_PAYLOAD_SIZE)
        """
        # Compute how many segments we need
        total_segments = (file_size + UDP_PAYLOAD_SIZE - 1) // UDP_PAYLOAD_SIZE

        segments_sent = 0
        for segment_idx in range(total_segments):
            # Build the packet
            header = struct.pack('!IBQQ',
                                 MAGIC_COOKIE,
                                 MSG_TYPE_PAYLOAD,
                                 total_segments,
                                 segment_idx + 1)  # 1-based index
            bytes_to_send = min(UDP_PAYLOAD_SIZE, file_size - (segment_idx * UDP_PAYLOAD_SIZE))
            payload = b'Y' * bytes_to_send

            packet = header + payload
            try:
                self.udp_server_socket.sendto(packet, client_address)
            except Exception as e:
                print(f"[Server][UDP] Error sending to {client_address}: {e}")
                break

            segments_sent += 1

        print(f"[Server][UDP] Finished sending {segments_sent} segments to {client_address}.")

    def shutdown(self):
        self.running = False
        self.broadcast_socket.close()
        self.tcp_server_socket.close()
        self.udp_server_socket.close()

    @staticmethod
    def get_local_ip():
        """
        Attempt to get the local IP address by opening a throwaway connection.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'


if __name__ == "__main__":
    server = SpeedTestServer()
    server.start()
