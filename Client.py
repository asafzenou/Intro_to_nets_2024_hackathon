#!/usr/bin/env python3
import socket
import struct

MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x02

BROADCAST_PORT = 13117


def main():
    # Create a UDP socket to listen for broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow re-binding the same port if another client is using it
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # If you want multiple clients on the same machine, also do:
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Listen on port 13117 on ALL interfaces
    sock.bind(('', BROADCAST_PORT))

    print(f"[Client] Listening for broadcast on UDP port {BROADCAST_PORT}...")
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if len(data) < 7:
                # Too short to be our expected packet => ignore
                continue

            # Try to parse the packet => [magic_cookie, msg_type, server_data_port]
            try:
                cookie, msg_type, server_data_port = struct.unpack('!IBH', data)
            except struct.error:
                # Not matching our structure => ignore
                continue

            # Check fields
            if cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER:
                print(f"[Client] Received offer from {addr[0]}, server_data_port={server_data_port}")
                # Here you could connect via TCP/UDP to the server at addr[0]:server_data_port
    except KeyboardInterrupt:
        print("\n[Client] Exiting.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
