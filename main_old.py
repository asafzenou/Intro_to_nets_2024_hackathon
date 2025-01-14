from Client_old import Client
from Server_old import Server

if __name__ == "__main__":
    role = input("Start as (server/client): ").strip().lower()
    if role == "server":
        server = Server()
        server.start()
    elif role == "client":
        client = Client()
        client.start()