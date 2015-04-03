import socket
import threading
import socketserver
import json


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock


def send(sock, data):
    try:
        sock.sendall(bytes(json.dumps(data), 'ascii'))
        return json.loads(str(sock.recv(1024), 'ascii'))
    except OSError:
        sock.close()


def requestHandlerFactory(data_handler):
    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def __init__(self, *args):
            self.data_handler = data_handler
            super().__init__(*args)

        def handle(self):
            data = json.loads(str(self.request.recv(1024), 'ascii'))

            response = self.data_handler(data)

            self.request.sendall(bytes(json.dumps(response), 'ascii'))

    return ThreadedTCPRequestHandler


def start(data_handler):
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = '0.0.0.0', 0

    server = ThreadedTCPServer((HOST, PORT), requestHandlerFactory(data_handler))
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    return port, server.shutdown