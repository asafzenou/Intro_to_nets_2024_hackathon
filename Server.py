import socket
import struct
import time

# ==============================
# CONFIGURATION & CONSTANTS
# ==============================
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x02

BROADCAST_IP = "255.255.255.255"  # or '172.1.255.255' if you're on that specific subnet
BROADCAST_PORT = 13117  # The port clients listen on

SERVER_UDP_PORT = 2024  # Example: The UDP port your server uses for data (if needed)
BROADCAST_INTERVAL = 1  # Seconds between sending broadcast messages


def main():
    """
    Continuously broadcasts an 'offer' message via UDP so that clients can detect the server.
    """
    print("Server: Creating broadcast socket...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable sending broadcast packets
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Optionally allow reusing address
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f"Server started, sending offer to broadcast {BROADCAST_IP}:{BROADCAST_PORT}")
    try:
        while True:
            # Format: magic_cookie (4 bytes), msg_type (1 byte), server_udp_port (2 bytes)
            #   '!IBH' means:
            #     !    => Network (big-endian)
            #     I    => unsigned int  (4 bytes)
            #     B    => unsigned char (1 byte)
            #     H    => unsigned short (2 bytes)
            packet = struct.pack('!IBH', MAGIC_COOKIE, MSG_TYPE_OFFER, SERVER_UDP_PORT)

            # Broadcast
            sock.sendto(packet, (BROADCAST_IP, BROADCAST_PORT))
            print(f"Broadcasted offer. (server_udp_port={SERVER_UDP_PORT})")
            time.sleep(BROADCAST_INTERVAL)

    except KeyboardInterrupt:
        print("\nServer shutting down...")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
