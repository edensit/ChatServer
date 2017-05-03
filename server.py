import socket
import select
import struct
import cPickle
import c_client
import database_handling


class ReceiveTypeEnum:
    TYPE_LOGIN = 1
    TYPE_REGISTER = 2
    TYPE_MSG = 3
    TYPE_COMMAND = 4
    TYPE_POKE = 5


class SendTypeEnum:
    TYPE_MSG = 1
    TYPE_USER_LIST = 2
    TYPE_POKE = 3


class LoginAuthStateEnum:
    CORRECT_AUTH = 1
    INCORRECT_AUTH = 2
    ALREADY_CONNECTED = 3


class BaseError(Exception):
    pass


class ChatServer:
    def __init__(self):
        self.database_handler = database_handling.DatabaseHandler()

        self.HOST = "0.0.0.0"
        self.PORT = 8820
        self.chat_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.chat_server_socket.bind((self.HOST, self.PORT))
        self.chat_server_socket.listen(5)

        self.client_list = []
        self.connection_list = [self.chat_server_socket]

        print "Server Started!"

    @staticmethod
    def send_msg(sock, data, d_type):
        s = struct.pack("!I", d_type) + data.strip()
        sock.send(s)

    def close_connection(self, sock):
        sock.close()
        self.connection_list.remove(sock)
        try:
            self.client_list.remove(self.find_client_instance(sock))
        except ValueError:
            pass

    def broadcast_data(self, sock, msg, d_type=SendTypeEnum.TYPE_MSG):
        for current_socket in self.connection_list:
            if current_socket != self.chat_server_socket and current_socket != sock:
                try:
                    self.send_msg(current_socket, msg, d_type)
                except socket.error:
                    self.close_connection(current_socket)

    def sock_to_name(self, sock):
        if sock is self.chat_server_socket:
            pass
        else:
            for client in self.client_list:
                if client.sock is sock:
                    return client.name
            raise ValueError("Could not find %s in %s" % (sock, "client_list"))

    def find_client_instance(self, sock):
        for client in self.client_list:
            if client.sock is sock:
                return client
            raise ValueError("Could not find %s in %s" % (sock, "client_list"))

    def find_sock_by_name(self, name):
        for client in self.client_list:
            if client.name == name:
                return client.sock
        raise ValueError("Could not find %s in %s" % (name, "client_list"))

    def connected_user_list(self):
        return [self.sock_to_name(sock) for sock in self.connection_list]

    def handle_login(self, data, new_socket, address):
        login_auth_split = data.split(":::")
        username = login_auth_split[0]
        password = login_auth_split[1]
        print data + ", " + username + ", " + password

        if self.database_handler.is_correct_login(username, password):
            if username not in self.connected_user_list():
                self.connection_list.append(new_socket)
                self.client_list.append(c_client.Client(username, new_socket))
                self.broadcast_data(new_socket, "%s connected to the server" % username)

                self.send_msg(new_socket, "", LoginAuthStateEnum.CORRECT_AUTH)
                print "Login successful: %s %s connected to the server" % (username, address)

                users_list = self.connected_user_list()
                self.broadcast_data(new_socket, cPickle.dumps(users_list), SendTypeEnum.TYPE_USER_LIST)
                self.send_msg(new_socket, cPickle.dumps(users_list), SendTypeEnum.TYPE_USER_LIST)
            else:
                self.send_msg(new_socket, "already connected!", LoginAuthStateEnum.ALREADY_CONNECTED)
                new_socket.close()
                print "Login failed: %s connected to the server" % username
        else:
            self.send_msg(new_socket, "Incorrect username or password!", LoginAuthStateEnum.INCORRECT_AUTH)
            new_socket.close()
            print "Login failed: Name: %s Reason: incorrect username or password!" % username

    def handle_register(self, data):
        reg_details_split = data.split(":::")
        username = reg_details_split[0]
        password = reg_details_split[1]
        mail = reg_details_split[2]
        print data + ", " + username + ", " + password + ", " + mail

        try:
            self.database_handler.insert_new_user(username, password)
        except database_handling.RegisterError as error:
            print error

    def handle_msg(self, data, username, current_socket):
        if data.startswith("@"):
            send_to = data[1:data.index(" ")]
            data = data[data.index(" "):]
            try:
                sock_to_send = self.find_sock_by_name(send_to)
            except ValueError:
                self.send_msg(current_socket, "Could not find %s" % send_to, SendTypeEnum.TYPE_MSG)
            else:
                self.send_msg(sock_to_send, "[%s to you] %s" % (username, data), SendTypeEnum.TYPE_MSG)
        else:
            self.broadcast_data(current_socket, "[%s] %s" % (username, data))

    def handle_poke(self, data, username, current_socket):
        send_to = data[:data.index(":::")]
        msg = data[data.index(":::") + 3:]
        data = username + ":::" + msg

        try:
            sock_to_poke = self.find_sock_by_name(send_to)
        except ValueError:
            self.send_msg(current_socket, "Could not find %s" % send_to, SendTypeEnum.TYPE_MSG)
        else:
            self.send_msg(sock_to_poke, data, SendTypeEnum.TYPE_POKE)
            self.send_msg(current_socket, "You poked %s with message: %s" % (send_to, msg), SendTypeEnum.TYPE_MSG)

    def run(self):
        while True:
            rlist, wlist, xlist = select.select(self.connection_list, [], [])
            for current_socket in rlist:
                if current_socket is self.chat_server_socket:
                    (new_socket, address) = self.chat_server_socket.accept()
                    recv_data = new_socket.recv(1024).strip()
                    (d_type, arg), data = struct.unpack("!II", recv_data[:8]), recv_data[8:]

                    if d_type == ReceiveTypeEnum.TYPE_LOGIN:
                        self.handle_login(data, new_socket, address)
                    elif d_type == ReceiveTypeEnum.TYPE_REGISTER:
                        self.handle_register(data)
                    else:
                        pass
                else:
                    username = self.sock_to_name(current_socket)
                    try:
                        recv_data = current_socket.recv(1024)
                    except socket.error:
                        self.broadcast_data(current_socket, "%s left the server" % username)
                        print "%s %s left the server" % (username, address)
                        self.close_connection(current_socket)

                        users_list = self.connected_user_list()
                        self.broadcast_data(current_socket, cPickle.dumps(users_list), SendTypeEnum.TYPE_USER_LIST)
                    else:
                        (d_type, arg), data = struct.unpack("!II", recv_data[:8]), recv_data[8:]

                        if d_type == ReceiveTypeEnum.TYPE_MSG:
                            self.handle_msg(data, username, current_socket)
                        elif d_type == ReceiveTypeEnum.TYPE_COMMAND:  # command
                            pass
                        elif d_type == ReceiveTypeEnum.TYPE_POKE:
                            self.handle_poke(data, username, current_socket)
