from  Message_Client_DB import *
import socket
import threading
from Client_Handler import *
PORT_FILE_NAME = "port.info"


def handle_client(client):
    print("client connected")
    myClient = Client(client)
    while True:
        try:
            msg = myClient.recvMsg()
            myClient.handleMsg(msg)
        except:
            print("client exited")
            break







def main():
    #get port number
    port_file = open(PORT_FILE_NAME)
    port = int(port_file.readline())
    #get local ip
    local_ip = socket.gethostbyname(socket.gethostname())
    #intiallize server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip,port))
    server.listen(5)

    thread_list = []

    #accepting clients
    while True:
        client, addr = server.accept()
        t = threading.Thread(target = handle_client, args = (client,))
        t.start()
        t.handled = False
        thread_list.append(t)

        # join threads
        for th in thread_list:
            if not th.is_alive():
                th.join()
                t.handled = True

        thread_list = [t for t in thread_list if not t.handled]











if __name__ == "__main__":
    main()