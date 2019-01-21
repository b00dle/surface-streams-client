

def run_asynchoro_test():
    import socket, asyncoro, time, random

    def server_proc(n, sock, coro=None):
        #for i in range(n):
        msg, addr = yield sock.recvfrom(1024)
        print('Received "%s" from %s:%s' % (msg, addr[0], addr[1]))
        sock.close()

    def client_proc(host, port, coro=None):
        sock = asyncoro.AsynCoroSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        msg = 'client socket: %s' % (sock.fileno())
        print(msg)
        yield sock.sendto(msg.encode("utf-8"), (host, port))
        sock.close()

    sock = asyncoro.AsynCoroSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    sock.bind(('127.0.0.1', 0))
    host, port = sock.getsockname()

    n = 10
    server_coro = asyncoro.Coro(server_proc, n, sock)
    for i in range(n):
        asyncoro.Coro(client_proc, host, port)
    server_coro.resume()