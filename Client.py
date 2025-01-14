#!/usr/bin/env python3
import socket
import struct
import time
import threading

# ==============================
# CONFIGURATION & CONSTANTS
# ==============================
VERSION = "1.1"  # Just to remind that this is example code for Hackathon v1.1
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

# We listen for offer messages on this port:
CLIENT_LISTEN_PORT = 13117

# If you want to run multiple clients on the same computer, you may need:
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

# Timeout for UDP after we suspect server finished sending
UDP_TRANSFER_TIMEOUT = 1.0

# Default number of bytes for each file request (for quick demo)
DEFAULT_FILE_SIZE = 1024 * 1024  # 1 MB
DEFAULT_TCP_CONNECTIONS = 1
DEFAULT_UDP_CONNECTIONS = 1

# We'll store results in a simple structure
class TransferResult:
    def __init__(self, protocol, index):
        self.protocol = protocol
        self.index = index
        self.start_time = 0.0
        self.end_time = 0.0
        self.file_size = 0
        self.received_bytes = 0
        self.packets_expected = 0
        self.packets_received = 0

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def speed_bits_per_sec(self):
        # bits / seconds
        return (self.file_size * 8) / (self.duration + 1e-9)  # add a small offset to avoid division by zero

    def __str__(self):
        if self.protocol.lower() == "tcp":
            return (f"TCP transfer #{self.index} finished, "
                    f"total time: {self.duration:.3f} seconds, "
                    f"total speed: {self.speed_bits_per_sec:.3f} bits/sec")
        else:
            # UDP
            if self.packets_expected > 0:
                success_rate = 100.0 * self.packets_received / self.packets_expected
            else:
                success_rate = 0.0
            return (f"UDP transfer #{self.index} finished, "
                    f"total time: {self.duration:.3f} seconds, "
                    f"total speed: {self.speed_bits_per_sec:.3f} bits/sec, "
                    f"percentage of packets received successfully: {success_rate:.2f}%")

# ==============================
# CLIENT LOGIC
# ==============================
class SpeedTestClient:
    def __init__(self):
        self.running = True
        # Prepare a UDP socket for listening to "offer" broadcasts
        self.udp_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # If you need to run multiple clients on the same computer, uncomment next line:
            # self.udp_offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.udp_offer_socket.bind(('', CLIENT_LISTEN_PORT))
        except OSError as e:
            print("[Client] Could not bind to port 13117 - perhaps it's in use. Error:", e)
            raise

    def start(self):
        while self.running:
            print("[Client] ====================================")
            print("[Client] Welcome to the Speed Test Client!")
            file_size, tcp_count, udp_count = self.ask_user_params()

            # Go to "Looking for a server" state
            print("[Client] Client started, listening for offer requests...")
            server_info = self.listen_for_offers()
            if not server_info:
                print("[Client] No server offers received. Retrying...\n")
                continue

            # server_info is (server_ip, server_udp_port, server_tcp_port)
            self.run_speed_test(server_info, file_size, tcp_count, udp_count)

            # After finishing all transfers, go back to listening for new offers
            print("[Client] All transfers complete, listening to offer requests...\n")

    def ask_user_params(self):
        """
        Ask the user for file size, # of TCP connections, # of UDP connections.
        For automation, we'll just use defaults or prompt.
        """
        try:
            file_size_str = input(f"Enter the file size in bytes [{DEFAULT_FILE_SIZE}]: ").strip()
            if file_size_str == "":
                file_size = DEFAULT_FILE_SIZE
            else:
                file_size = int(file_size_str)

            tcp_str = input(f"Enter the number of TCP connections [{DEFAULT_TCP_CONNECTIONS}]: ").strip()
            tcp_count = int(tcp_str) if tcp_str else DEFAULT_TCP_CONNECTIONS

            udp_str = input(f"Enter the number of UDP connections [{DEFAULT_UDP_CONNECTIONS}]: ").strip()
            udp_count = int(udp_str) if udp_str else DEFAULT_UDP_CONNECTIONS

            return file_size, tcp_count, udp_count
        except ValueError:
            print("[Client] Invalid input. Using defaults.")
            return DEFAULT_FILE_SIZE, DEFAULT_TCP_CONNECTIONS, DEFAULT_UDP_CONNECTIONS

    def listen_for_offers(self, timeout=5.0):
        """
        Listen on self.udp_offer_socket for 'offer' messages for up to `timeout` seconds.
        If found, return (server_ip, server_udp_port, server_tcp_port).
        Otherwise, return None.
        """
        self.udp_offer_socket.settimeout(timeout)
        try:
            while True:
                data, addr = self.udp_offer_socket.recvfrom(1024)
                # Attempt to parse an offer
                try:
                    # Format of an offer: magic_cookie (4 bytes), msg_type (1 byte),
                    # server_udp_port (2 bytes), server_tcp_port (2 bytes)
                    cookie, msg_type, srv_udp_port, srv_tcp_port = struct.unpack('!IBHH', data)
                    if cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER:
                        server_ip = addr[0]
                        print(f"[Client] Received offer from {server_ip}, "
                              f"UDP port={srv_udp_port}, TCP port={srv_tcp_port}")
                        return (server_ip, srv_udp_port, srv_tcp_port)
                except struct.error:
                    # Not a valid packet, ignore
                    pass
        except socket.timeout:
            return None

    def run_speed_test(self, server_info, file_size, tcp_count, udp_count):
        """
        Given server info (ip, udp_port, tcp_port), file size, and number of connections,
        1) Launch threads to do TCP transfer(s)
        2) Launch threads to do UDP transfer(s)
        3) Wait for all to finish
        """
        server_ip, srv_udp_port, srv_tcp_port = server_info

        # For each transfer, create a TransferResult and spawn a thread
        results = []

        # === TCP Transfers ===
        for i in range(tcp_count):
            result = TransferResult("TCP", i + 1)
            result.file_size = file_size
            results.append(result)
            t = threading.Thread(target=self.do_tcp_transfer, args=(server_ip, srv_tcp_port, result))
            t.start()

        # === UDP Transfers ===
        for i in range(udp_count):
            result = TransferResult("UDP", i + 1)
            result.file_size = file_size
            results.append(result)
            t = threading.Thread(target=self.do_udp_transfer, args=(server_ip, srv_udp_port, result))
            t.start()

        # Wait for all threads to finish
        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()

        # Print results
        for r in results:
            print(str(r))

    def do_tcp_transfer(self, server_ip, tcp_port, result: TransferResult):
        """
        1) Connect via TCP to server
        2) Send the file size (as string + newline)
        3) Read the entire file
        """
        start_time = time.time()
        result.start_time = start_time

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server_ip, tcp_port))

            # Send request
            s.sendall(str(result.file_size).encode() + b"\n")

            # Receive the file
            bytes_received = 0
            while bytes_received < result.file_size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                bytes_received += len(chunk)

            result.end_time = time.time()
            result.received_bytes = bytes_received

        except Exception as e:
            print(f"[Client][TCP] Error: {e}")
            result.end_time = time.time()
        finally:
            s.close()

    def do_udp_transfer(self, server_ip, udp_port, result: TransferResult):
        """
        1) Send a request packet (Magic cookie, type=0x3, file_size)
        2) Receive payload packets until 1 second of no data
        3) Keep track of how many packets we got
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(UDP_TRANSFER_TIMEOUT)
        try:
            # Send request
            # Format: magic_cookie (4 bytes), msg_type (1 byte), file_size (8 bytes)
            msg = struct.pack('!IBQ', MAGIC_COOKIE, MSG_TYPE_REQUEST, result.file_size)
            s.sendto(msg, (server_ip, udp_port))

            # Start measuring time
            result.start_time = time.time()

            last_packet_time = time.time()
            while True:
                try:
                    data, addr = s.recvfrom(65535)  # large buffer
                    if not data:
                        # No data means server closed?
                        break

                    # Check that data is a valid payload
                    # Magic cookie (4 bytes), msg_type (1 byte),
                    # total_segment_count (8 bytes), current_segment (8 bytes)
                    header_size = struct.calcsize('!IBQQ')
                    if len(data) < header_size:
                        continue  # skip malformed

                    cookie, msg_type, total_segments, current_segment = struct.unpack('!IBQQ', data[:header_size])
                    if cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_PAYLOAD:
                        # update stats
                        payload = data[header_size:]
                        result.packets_expected = total_segments
                        result.packets_received += 1
                        result.received_bytes += len(payload)
                        last_packet_time = time.time()
                except socket.timeout:
                    # If we've timed out waiting for a packet, assume it's done
                    if (time.time() - last_packet_time) > UDP_TRANSFER_TIMEOUT:
                        break

            result.end_time = time.time()

        except Exception as e:
            print(f"[Client][UDP] Error: {e}")
            result.end_time = time.time()
        finally:
            s.close()


if __name__ == "__main__":
    client = SpeedTestClient()
    client.start()
