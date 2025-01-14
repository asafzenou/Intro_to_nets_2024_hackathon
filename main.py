import threading
import Server
import Client
import time

server = Server.Server()
client1 = Client.Client()
client2 = Client.Client()

server_thread = threading.Thread(target=server.main)
client_thread = threading.Thread(target=client1.main)
client_thread1 = threading.Thread(target=client2.main)
server_thread.start()
time.sleep(1)

client_thread.start()
client_thread1.start()