import sys
from socket import *
import struct
from scapy.arch import *
from select import select
import getch


class Client:

    def __init__(self):
        self.port = 13500
        self.server_host = ""
        self.state = False  # False - not in game mode

        self.magic_cookie = 0xabcddcba
        self.message_type = 0x2

    def main(self):
        print("Client started, listening for offer requests...")
        while 1:
            server_port = self.listenning_on_udp()
            client_socket = self.listening_on_tcp(server_port)
            if (client_socket is None):
                continue
            start_game(client_socket)

    def listenning_on_udp(self):
        # Create a UDP socket at client side
        udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_client_socket.bind(("", self.port))

        while 1:

            offer_from_server, adress = udp_client_socket.recvfrom(2048)
            self.server_host = adress[0]
            # print(self.server_host)
            try:
                magic_cookie, message_type, server_port = struct.unpack('IbH', offer_from_server)
                print("amen")
                if (self.magic_cookie == magic_cookie and self.message_type == message_type):
                    udp_client_socket.close()
                    return server_port
            except:
                pass

    def listening_on_tcp(self, server_port):
        client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        try:
            print("Received offer from", self.server_host, ",attempting to connect...")
            client_socket.connect((self.server_host, server_port))
            # print("asdasf")
            client_socket.send("kitkat".encode('UTF-8'))
            return client_socket
        except:
            return None

    def start_game(self, client_socket):
        self.state = True
        message = client_socket.recv(1024).decode("UTF-8")
        print(message)
        client_socket.setblocking(0)
        while 1:
            try:
                message = client_socket.recv(1024).decode("UTF-8")
                if message is None:
                    break
            except:
                pass
            try:
                client_socket.sendall(getch.getch().encode("UTF-8"))
            except socket.error:
                pass
            client_socket.close()


def main():
    client = Client()
    client.main()


if __name__ == "__main__":
    main()