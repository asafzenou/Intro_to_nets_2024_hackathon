from socket import *
import struct
from select import select
import sys
import getch
from scapy.arch import get_if_addr


class Client:

    def __init__(self):
        self.buff_len = 2048
        self.magic_cookie = 0xabcddcba
        self.msg_type = 0x2
        self.team_name = "STAV NAVIT"
        self.udp_port = 13111
        self.server_ip = ""

    def start_client(self):
        print("Client started, listening for offer requests...")
        while True:
            server_port, server_ip = self.get_offer_byUDP()
            client_socket_TCP = self.connect_to_server(server_port, server_ip)
            print("sent to connect_to_server")
            if client_socket_TCP is None:
                continue
            self.start_game(client_socket_TCP)

    def get_offer_byUDP(self):
        client_socket_UDP = socket(AF_INET, SOCK_DGRAM)  # create udp client socket
        client_socket_UDP.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        client_socket_UDP.bind(("", self.udp_port))
        while True:
            offer, server_address = client_socket_UDP.recvfrom(self.buff_len)
            self.server_ip = server_address[0]
            try:
                cookie, msg_type, server_port = struct.unpack('IbH', offer)
                if cookie == self.magic_cookie and msg_type == self.msg_type:
                    # client_socket.close()
                    return server_port, self.server_ip
            except:
                pass

    def connect_to_server(self, server_port, server_ip):
        try:
            client_socket_TCP = socket(AF_INET, SOCK_STREAM)  # create tcp client socket
            print("Received offer from {0} attempting to connect...".format(server_ip))
            print(server_ip, server_port)
            client_socket_TCP.connect((server_ip, server_port))
            print("client connected")
            client_socket_TCP.sendall(team_name.encode("UTF-8"))

            return client_socket_TCP
        except:
            return None

    def start_game(self, client_socket):
        print("client-start game")
        start_msg = client_socket.recv(self.buff_len).decode("UTF-8")
        print(start_msg)
        client_socket.setblocking(0)
        end_game = False
        while not end_game:
            try:
                msg = client_socket.recv(self.buff_len).decode("UTF-8")
                if not msg:
                    end_game = True
                    break
                else:
                    print(msg)
                    end_game = True
                    break
            except:
                pass
            if not end_game and not kbhit():
                try:
                    client_socket.sendall(getch().encode("UTF-8"))
                except:
                    pass
        client_socket.close()
        print("Server disconnected, listening for offer requests...\n")

    def kbhit(self):
        dr, dw, de = select([sys.stdin], [], [], 0)
        return dr == 0

    # def close_tcp(client_socket):
    #     client_socket.shutdown(socket.SHUT_RDWR)
    #     client_socket.close()

    # if __name__ == "__main__":
    #     start_client()