import Client
import Server
import threading


def main():
    server = Server.Server()
    client = Client.Client()
    s = threading.Thread(target = server.start_server)
    # server.start_server()
    c1 = threading.Thread(target =client.start_client)
    c2 = threading.Thread(target =client.start_client)

    s.start()
    time.sleep(1)
    c1.start()
    c2.start()
if __name__ == '__main__':
    main()