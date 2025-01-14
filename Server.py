import socket
import threading
import time
import struct
from threading import Thread
import random


class Server:

    def __init__(self):

        self.d_port = 13500
        self.s_port = 2066
        self.host = socket.gethostbyname(socket.gethostname())
        self.state = False  # False - not in game mode
        self.clients = []
        self.magic_cookie = 0xabcddcba
        self.message_type = 0x2
        self.question = ""
        self.answer = ""
        self.client1_ans = ""
        self.client2_ans = ""
        self.winner = ""
        self.lock = False

    def main(self):
        print("Server started, listening on IP address", self.host)
        while 1:
            tcp_connect_thread = threading.Thread(target=self.listening_on_tcp)
            send_offer_thread = threading.Thread(target=self.send_offer_udp)
            print("lalalalallalalala")

            print("2sjdjkdllslsls")
            tcp_connect_thread.start()
            send_offer_thread.start()
            send_offer_thread.join()
            tcp_connect_thread.join()
            time.sleep(1)
            start_game()
            print("Game over!/nThecorrect answer was", self.answer, "!", "/nCongratulations to the winner: ",
                  self.winner)
            reset_all()

    def send_offer_udp(self):
        print("send_offer_udp1")
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        print("send_offer_udp2")
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # print("Server started, listening on IP address" , self.self.host)
        # Enable broadcasting mode
        # server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.bind(('', self.s_port))
        # timeout so the socket does not block

        print("send_offer_udp3")

        offer_message = struct.pack('IbH', self.magic_cookie, self.message_type, self.s_port)
        while len(self.clients) < 2:
            # print(len(self.clients))
            # print("client len", len(self.clients))
            server.sendto(offer_message, ('', self.d_port))
            time.sleep(1)

    def listening_on_tcp(self):
        # connection_succeess = False
        try:

            server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            server_socket.bind((self.host, self.s_port))
            server_socket.listen(2)

            i = 0
            # print(time.time() )
            # print(game_done)
            # while(time.time()<game_done and len(self.clients)<2):
            while (len(self.clients) < 2):
                print("dana")
                i += 1
                try:
                    connection_socket, addr = server_socket.accept()
                    # print("after accept")
                    client_name = connection_socket.recv(1024).decode("UTF-8")
                    # print("add client")
                    self.clients.append(
                        (Thread(calc_self.question, (connection_socket, i)), client_name, addr, connection_socket))
                except:
                    print("error")
                    if (time.time() >= game_done or len(self.clients) >= 2):
                        break
                    pass


        except:

            pass

    def start_game(self):
        val1 = random.randrange(5)
        val2 = random.randrange(5)
        self.answer = val1 + val2
        self.question = "{}+{}".format(val1, val2)
        self.state = True
        for client in self.clients:
            client[0].start()
        for client in self.clients:
            client[0].join()

    def calc_question(self, connection_socket, client_num):
        message = "Welcome to Quick Maths./nPlayer 1: ", self.clients[0][1], "/nPlayer 2: ", self.clients[1][
            1], "/n==/nPlease self.answer the following self.question as fast as you can:"
        connection_socket.send(message.encode("UTF-8"))
        game_done = time.time() + 10
        client_ans = None

        while (time.time() < game_done and client_ans == None):

            try:
                client_ans = connection_socket.recv(1024).decode('UTF-8')
                self.lock = True
                if client_ans == self.answer:
                    self.winner = client_num
                else:
                    if (client_num == 1):
                        self.winner = self.clients[1]
                    else:
                        self.winner = self.clients[0]
            except:
                pass

        def reset_all():

            self.state = False  # False - not in game mode
            self.clients = []

            self.question = ""
            self.answer = ""
            self.client1_ans = ""
            self.client2_ans = ""
            self.winner = ""


def main():
    server = Server()
    server.main()


if __name__ == "__main__":
    main()