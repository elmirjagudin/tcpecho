#!/usr/bin/env python3

import threading
import socket
import queue
import select
# import sys
#

#
# # Create a TCP/IP socket
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
# # Bind the socket to the port
# server_address = ('localhost', INCOMING_PORT)
# print('starting up on {} port {}'.format(*server_address))
# sock.bind(server_address)
#
# # Listen for incoming connections
# sock.listen(1)
#
#
# while True:
#     # Wait for a connection
#     print('waiting for a connection')
#     connection, client_address = sock.accept()
#     print(connection)
#     try:
#         print('connection from', client_address)
#
#         # Receive the data in small chunks and retransmit it
#         while True:
#             data = connection.recv(16)
#             print('received {!r}'.format(data))
#             if data:
#                 print('sending data back to the client')
#                 connection.sendall(data)
#             else:
#                 print('no data from', client_address)
#                 break
#
#     finally:
#         # Clean up the connection
#         connection.close()

INCOMING_PORT = 2001
OUTGOING_PORT = 2000

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




def _incoming():
    global incoming_connection
    sock = init_tcp_socket(INCOMING_PORT)
    while True:
        connection, client_address = sock.accept()
        print("incoming connection from", client_address)
        incoming_connection = connection
#        connection.sendfile(connection.makefile("rb"))
#        connection.close()



def _outgoing():
    sock = init_tcp_socket(OUTGOING_PORT)
    while True:
        connection, client_address = sock.accept()
        print("outgoing connection from", client_address)
        while incoming_connection is None:
            import time; time.sleep(0.1)


        shutil.copyfileobj(incoming_connection.makefile("rb"),
                           connection.makefile("wb"))

        incoming_connection.close()
        connection.close()


#threading.Thread(target=incoming).start()
#threading.Thread(target=outgoing).start()

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
            out_conn.send(data)
            data = None

    in_conn.close()
    out_conn.close()


def main():
    in_sock = init_tcp_socket(INCOMING_PORT)
    out_sock = init_tcp_socket(OUTGOING_PORT)

    in_conn = None
    out_conn = None

    while True:
        r, _, _ = select.select([in_sock, out_sock], [], [])

        for sock in r:
            if sock == in_sock:
                in_conn, _ = in_sock.accept()
                in_conn.setblocking(False)
                print("in accept", in_conn)
            elif sock == out_sock:
                out_conn, _ = out_sock.accept()
                out_conn.setblocking(False)

        # TODO: check in in_conn or out_conn have been closed
        # while waiting for the other end

        if in_conn is not None and out_conn is not None:
            runner = lambda : copy_in_to_out(in_conn, out_conn)
            threading.Thread(target=runner).start()
            in_conn = out_conn = None




#    incoming_connection = queue.Queue(1)
#    outgoing_connection = queue.Queue(1)

#    threading.Thread(
#        target=lambda : accept_connection("incoming",
#                                          INCOMING_PORT,
#                                          incoming_connection)).start()
#    threading.Thread(
#        target=lambda : accept_connection("outgoing",
#                                          OUTGOING_PORT,
#                                          outgoing_connection)).start()



main()









