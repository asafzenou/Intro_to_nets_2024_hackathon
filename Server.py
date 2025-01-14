#!/usr/bin/env python3
import socket
import struct
import time

MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x02
SERVER_DATA_PORT = 2024     # Example: A port you'd like to advertise
BROADCAST_PORT = 13117      # The port that the client listens on
BROADCAST_INTERVAL = 1.0    # Seconds between broadcast messages

def main():
    # Create a UDP socket for broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Allow re-binding the same port if needed
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to an ephemeral port on all interfaces (0.0.0.0 with port=0)
    sock.bind(('', 0))

    # Prepare a packet: [magic_cookie (4 bytes), msg_type (1 byte), server_data_port (2 bytes)]
    # Using struct: '!IBH' => (network-endian) unsigned int, unsigned char, unsigned short
    packet = struct.pack('!IBH', MAGIC_COOKIE, MSG_TYPE_OFFER, SERVER_DATA_PORT)

    print(f"[Server] Broadcasting on 255.255.255.255:{BROADCAST_PORT} every {BROADCAST_INTERVAL} second(s).")
    try:
        while True:
            # Send a limited broadcast to 255.255.255.255 on port 13117
            sock.sendto(packet, ('255.255.255.255', BROADCAST_PORT))
            print("[Server] Broadcasted offer packet.")
            time.sleep(BROADCAST_INTERVAL)
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
