import socket
import struct

# ==============================
# CONFIGURATION & CONSTANTS
# ==============================
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x02

LISTEN_PORT = 13117  # Must match BROADCAST_PORT in server.py


def main():
    """
    Listens on UDP port 13117 for 'offer' messages from the server.
    When an offer is received, prints out the server IP and port.
    """
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # If you want to run multiple clients on the same machine, 
    # you can also do: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock.bind(('', LISTEN_PORT))  # Listen on all interfaces, port 13117

    print("Client started, listening for offer requests...")

    try:
        while True:
            data, addr = sock.recvfrom(1024)  # Receive up to 1024 bytes
            if len(data) < 7:
                # Too small to contain our message => ignore
                continue

            # Attempt to parse
            # Format: magic_cookie (4 bytes), msg_type (1 byte), server_udp_port (2 bytes)
            try:
                cookie, msg_type, server_udp_port = struct.unpack('!IBH', data)
            except struct.error:
                # Invalid data format
                continue

            if cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER:
                # This is a valid offer message
                print(f"Received offer from {addr[0]}, server UDP port={server_udp_port}")
                print("You could now initiate a TCP or UDP connection to that server.")
    except KeyboardInterrupt:
        print("\nClient shutting down...")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
