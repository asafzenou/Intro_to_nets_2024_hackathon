from socket import *
from _thread import *
from threading import Thread, Lock
import time
from scapy.arch import get_if_addr
import random


class Server:

    def __init__(self):

        # constants
        self.buff_len = 2048
        self.magic_cookie = 0xabcddcba
        self.msg_type = 0x2
        self.source_ip = get_if_addr('eth1')  # ip development network  # socket.gethostbyname(socket.gethostname())
        self.source_port = 2060
        self.dest_port = 13111
        # global variables
        self.clients = []  # (team_thread, team_num, team_name, connection_socket)
        self.question = ""
        self.answer_player1 = ""
        self.answer_player2 = ""
        # WINNER_NUM = 0
        self.lock = False
        self.winner = ""

    def start_server(self):
        print("Server started, listening on IP address {0}".format(self.source_ip))
        server_socket_TCP = socket(AF_INET, SOCK_STREAM)  # create tcp socket
        server_socket_TCP.bind((self.source_ip, self.source_port))
        while True:
            send_offers_thread = Thread(target=self.send_offers_byUDP)  # thread for sending offers
            find_client_thread = Thread(target=self.connet_client, args=(server_socket_TCP,))
            find_client_thread.start()
            send_offers_thread.start()
            send_offers_thread.join()
            find_client_thread.join()
            self.start_game()

    def send_offers_byUDP(self):
        server_socket_UDP = socket(AF_INET, SOCK_DGRAM)
        server_socket_UDP.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        server_socket_UDP.bind(("", self.source_port))
        offer = struct.pack('IbH', self.magic_cookie, self.msg_type, self.source_port)
        while len(self.clients) < 2:
            server_socket_UDP.sendto(offer, ("", self.dest_port))
            time.sleep(1)

    def connet_client(self, server_socket_TCP):
        # timeout?
        start_time = time.time()
        time_out = 0
        while time_out < 10:
            time_out = time.time() - start_time
            try:
                conn, client_address = server_socket_TCP.accept()
                print(client_address)
                # timeout?
                player_name = ""
                while player_name == "":
                    try:
                        player_name = conn.recv(self.buff_len).decode("UTF-8")
                        print(player_name)
                        while len(self.clients) < 2:
                            player_thread = Thread(target=answer, arg=(conn, len(self.clients)))
                            self.clients.append((player_thread, len(self.clients), player_name, conn))
                    except:
                        time_out = time.time() - start_time
                        if time_out >= 10:
                            print("timeout")
                            break
                        else:
                            pass
            except:
                pass

    def answer(self, conn, player_num):
        # start_game_message = "Welcome to Quick Maths.\nPlayer 1: {0}\nPlayer 2: {1}\n==\nPlease answer the following question as fast as you can:\nHow much is {2}?".format(self.clients[0][2], self.clients[1][2],self.question)
        start_game_message = "Welcome to Quick Maths.\nPlayer 1: {0}\nPlayer 2: player2\n==\nPlease answer the following question as fast as you can:\nHow much is {1}?".format(
            self.clients[0][2], self.question)
        conn.send(start_game_message.encode("UTF-8"))
        start_time = time.time()
        time_out = 0
        answer = None
        while time_out < 10 and answer == None:
            time_out = time.time() - start_time
            try:
                answer = conn.recv(self.buff_len).decode("UTF-8")
                self.lock = True
                if answer == eval(self.question):
                    self.winner = player_num

                else:
                    if player_num == self.clients[0][1]:
                        self.winner = self.clients[1][2]
                    else:
                        self.winner = self.clients[0][2]
                return
            except:
                pass
        if (self.lock == False):
            self.winner = 0
        self.game_over()

    def start_game(self):
        optional_questions = ["2+2", "5+2", "3*2"]
        index = random.randrange(3)
        self.question = optional_questions[index]
        # for client in self.clients:
        #     client[3].send(start_game_message.encode("UTF-8"))
        self.clients[0][0].start()
        self.clients[1][0].start()
        self.clients[0][0].join()
        self.clients[1][0].join()
        end_game_msg = "Game over!\nThe correct answer was {0}!\nCongratulations to the winner: {1}".format(
            eval(self.question), self.clients[0][2])
        if self.answer_player1 == eval(self.question):
            end_game_msg = "Game over!\nThe correct answer was {0}!\nCongratulations to the winner: {1}".format(
                eval(self.question), self.clients[0][2])

        for client in self.clients:
            client[3].send(end_game_msg.encode("UTF-8"))
            client[3].close()

    # if __name__ == "__main__":
    #     start_server()