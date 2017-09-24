#!/usr/bin/env python3

import threading
import socket
import select
import sys

def init_tcp_socket(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the port
    server_address = ("0.0.0.0", port)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    return sock


def accept_connection(desk, port, connections_queue):
    sock = init_tcp_socket(port)
    while True:
        connection, client_address = sock.accept()
        print("%s connection from %s" % (desk, client_address))
        connections_queue.put(connection)


def copy_in_to_out(in_conn, out_conn):
    data = None
    while True:
        write_list = [] if data is None else [out_conn]
        r, w, _ = select.select([in_conn], write_list, [])

        if data is None and in_conn in r:
            data = in_conn.recv(1024*16)
            if len(data) == 0:
                print("incoming closed")
                break

        if data is not None and out_conn in w:
            try:
                out_conn.sendall(data)
                data = None
            except ConnectionError as ex:
                print("outgoing connection error %s %s" %(ex, type(ex)))
                break

    in_conn.close()
    out_conn.close()


def main(incoming_port, outgoing_port):
    in_sock = init_tcp_socket(incoming_port)
    out_sock = init_tcp_socket(outgoing_port)

    in_conn = None
    out_conn = None

    while True:
        r, _, e = select.select([in_sock, out_sock], [], [])

        for sock in r:
            if sock == in_sock:
                in_conn, _ = in_sock.accept()
                in_conn.setblocking(False)
            elif sock == out_sock:
                out_conn, _ = out_sock.accept()
                out_conn.setblocking(False)

        if in_conn is not None and out_conn is not None:
            runner = lambda : copy_in_to_out(in_conn, out_conn)
            threading.Thread(target=runner).start()
            in_conn = out_conn = None

if len(sys.argv) < 3:
    print("usage %s <incoming port> <outgoing port>" % sys.argv[0])
    sys.exit(1)

main(int(sys.argv[1]), int(sys.argv[2]))
