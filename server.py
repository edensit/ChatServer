import cPickle
import select
import socket
import struct
import re
import chat_client
from handlers import database_handling


class UserDetailsTypeEnum:
    IS_IN_DATABASE = 0
    USERNAME = 1
    IS_ADMIN = 2
    IS_MUTED = 3


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


class RegisterStateEnum:
    CORRECT_REGISTER = 1
    INCORRECT_REGISTER = 2
    ILLEGAL_USERNAME = 3
    ILLEGAL_PASSWORD = 4


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

        self.COMMAND_SWITCH = {
            "mute": self.mute_command_handler,
            "kick": self.kick_command_handler,
            "ban": self.ban_command_handler,
            "unban": self.unban_command_handler,
            "banslist": self.banlist_command_handler,
            "addadmin": self.addadmin_command_handler,
            "removeadmin": self.removeadmin_command_handler,
            "adminslist": self.adminlist_command_handler, }

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

    def broadcast_data(self, msg, d_type=SendTypeEnum.TYPE_MSG, sock=None):
        try:
            is_muted = self.find_client_instance(sock).is_muted
        except ValueError:
            is_muted = False

        if not is_muted:
            for current_socket in self.connection_list:
                if current_socket != self.chat_server_socket and current_socket != sock:
                    try:
                        self.send_msg(current_socket, msg, d_type)
                    except socket.error:
                        self.close_connection(current_socket)
        else:
            self.send_msg(sock, "You are muted :)", d_type)

    # ---------------------------------------------------#
    # ----------------EEEEEEEEEEEEEEEEEEEEE--------------#
    # ---------------------------------------------------#

    def sock_to_name(self, sock):
        if sock is self.chat_server_socket:
            pass
        else:
            for client in self.client_list:
                if client.sock is sock:
                    return client.name
            raise ValueError("Could not find {0} in {1}".format(sock, "client_list"))

    def find_client_instance(self, sock):
        for client in self.client_list:
            if client.sock is sock:
                return client
        raise ValueError("Could not find {0} in {1}".format(sock, "client_list"))

    def find_sock_by_name(self, name):
        for client in self.client_list:
            if client.name == name:
                return client.sock
        raise ValueError("Could not find {0} in {1}".format(name, "client_list"))

    def connected_user_list(self):
        return [self.sock_to_name(sock) for sock in self.connection_list]

    def push_connected_user_list(self):
        users_list = self.connected_user_list()
        self.broadcast_data(cPickle.dumps(users_list), SendTypeEnum.TYPE_USER_LIST)

    def login_handler(self, data, new_socket, address):  # Rewrite!
        login_auth_split = data.split(":::")
        username = login_auth_split[0]
        password = login_auth_split[1]
        print "Connection attempt: [ Username: {0} Password: {1} ] Received data: {2}".format(username, password, data)

        auth = self.database_handler.is_correct_login(username, password)
        if auth[UserDetailsTypeEnum.IS_IN_DATABASE]:
            username = auth[UserDetailsTypeEnum.USERNAME]
            if username not in self.connected_user_list():
                if auth[UserDetailsTypeEnum.IS_ADMIN]:
                    username = "[Admin]{0}".format(username)
                self.connection_list.append(new_socket)
                self.client_list.append(chat_client.Client(username, new_socket, auth[UserDetailsTypeEnum.IS_ADMIN],
                                                           auth[UserDetailsTypeEnum.IS_MUTED]))
                self.broadcast_data("{0} connected to the server".format(username), sock=new_socket)

                self.send_msg(new_socket, "", LoginAuthStateEnum.CORRECT_AUTH)
                print "Login successful: {0} {1} connected to the server".format(username, address)

                self.push_connected_user_list()
            else:
                self.send_msg(new_socket, "already connected!", LoginAuthStateEnum.ALREADY_CONNECTED)
                new_socket.close()
                print "Login failed: {0} connected to the server".format(username)
        else:
            self.send_msg(new_socket, "Incorrect username or password!", LoginAuthStateEnum.INCORRECT_AUTH)
            new_socket.close()
            print "Login failed: Name: {0} Reason: incorrect username or password!".format(username)

    def registration_handler(self, data, new_socket, address):
        register_details_split = data.split(":::")
        username = register_details_split[0]
        password = register_details_split[1]
        print "Registration attempt: [ Username: {0} Password: {1} ] Received data: {2}".format(username, password,
                                                                                                data)
        if not re.match("^[A-Za-z0-9_-]{4,}", username):
            self.send_msg(new_socket, 'ILLEGAL USERNAME', RegisterStateEnum.ILLEGAL_USERNAME)
            print "Unsuccessfully registered: Name: {0} Address: {1} Reason: {2}".format(username, address,
                                                                                         "ILLEGAL USERNAME")
        elif not re.match("[A-Za-z0-9@#$%^&+=]{8,}", password):
            self.send_msg(new_socket, 'ILLEGAL PASSWORD', RegisterStateEnum.ILLEGAL_PASSWORD)
            print "Unsuccessfully registered: Name: {0} Address: {1} Reason: {2}".format(username, address,
                                                                                         "ILLEGAL PASSWORD")
        else:
            try:
                self.database_handler.insert_new_user(username, password)
            except database_handling.RegisterError as error:
                print error
                self.send_msg(new_socket, "Bad registration", RegisterStateEnum.INCORRECT_REGISTER)
                print "Unsuccessfully registered: Name: {0} Address: {1} Reason: {2}".format(username, address, error)
            else:
                self.send_msg(new_socket, "You have successfully registered.", RegisterStateEnum.CORRECT_REGISTER)
                print "Successfully registered: Name: {0} Address: {1}".format(username, address)

        new_socket.close()

    def private_massage_handler(self, data, username, current_socket):
        try:
            send_to = data[1:data.index(" ")]
            data = data[data.index(" "):]
        except ValueError:
            self.send_msg(current_socket, "The syntax of the command is incorrect."
                                          " Use the following syntax: @[NAME] [MASSAGE]", SendTypeEnum.TYPE_MSG)
        else:
            try:
                sock_to_send = self.find_sock_by_name(send_to)
            except ValueError:
                self.send_msg(current_socket, "Could not find {0}".format(send_to), SendTypeEnum.TYPE_MSG)
            else:
                self.send_msg(sock_to_send, "[{0} to you] {1}".format(username, data), SendTypeEnum.TYPE_MSG)

    def mute_command_handler(self, args, admin_socket):
        args = args.strip()
        try:
            client_socket = self.find_sock_by_name(args)
            is_muted = self.find_client_instance(client_socket).toggle_mute()
            admin_name = self.sock_to_name(admin_socket)

        except ValueError:
            self.send_msg(admin_socket, "Could not find {0}".format(args), SendTypeEnum.TYPE_MSG)
        else:
            if is_muted:
                self.send_msg(client_socket, "You have been muted!".format(args), SendTypeEnum.TYPE_MSG)
                self.broadcast_data("{0} have been muted by {1}".format(args, admin_name), sock=admin_socket)
            else:
                self.send_msg(admin_socket, "{0} have been unmuted!".format(args), SendTypeEnum.TYPE_MSG)
                self.send_msg(client_socket, "You have been unmuted!".format(args), SendTypeEnum.TYPE_MSG)
                self.broadcast_data("{0} have been unmuted by {1}".format(args, admin_name), sock=admin_socket)

    def kick_command_handler(self, args, admin_socket):
        args = args.strip()
        try:
            client_socket = self.find_sock_by_name(args)
            admin_name = self.sock_to_name(admin_socket)
        except ValueError:
            self.send_msg(admin_socket, "Could not find {0}".format(args), SendTypeEnum.TYPE_MSG)
        else:
            self.send_msg(client_socket, "You have been kicked from the server!".format(args), SendTypeEnum.TYPE_MSG)
            self.close_connection(client_socket)

            self.send_msg(admin_socket, "{0} have been successfully kicked from the server!".format(args),
                          SendTypeEnum.TYPE_MSG)
            self.broadcast_data("{0} kicked by {1}".format(args, admin_name), sock=admin_socket)

            self.push_connected_user_list()

    def ban_command_handler(self, args, admin_socket):
        pass

    def unban_command_handler(self, args, admin_socket):
        pass

    def banlist_command_handler(self, args, admin_socket):
        pass

    def addadmin_command_handler(self, args, admin_socket):
        pass

    def removeadmin_command_handler(self, args, admin_socket):
        pass

    def adminlist_command_handler(self, args, admin_socket):
        pass

    def raw_command_handler(self, data, current_socket):
        try:
            command = data[1:data.index(" ")]
            args = data[data.index(" "):]
        except ValueError:
            self.send_msg(current_socket, "The syntax of the command is incorrect."
                                          " Use the following syntax: ![command] [arg]", SendTypeEnum.TYPE_MSG)
        else:
            if command.lower() in self.COMMAND_SWITCH:
                client = self.find_client_instance(current_socket)
                if client.is_admin:
                    self.COMMAND_SWITCH[command.lower()](args, current_socket)
                else:
                    self.send_msg(current_socket, "You do not have access to this command!", SendTypeEnum.TYPE_MSG)
            else:
                self.send_msg(current_socket, "Unknown Command!", SendTypeEnum.TYPE_MSG)

    def message_handler(self, data, username, current_socket):
        if data.startswith("@"):  # private massage
            self.private_massage_handler(data, username, current_socket)
        elif data.startswith("!"):  # command
            self.raw_command_handler(data, current_socket)
        else:
            self.broadcast_data("[{0}] {1}".format(username, data), sock=current_socket)

    def poke_handler(self, data, username, current_socket):
        send_to = data[:data.index(":::")]
        msg = data[data.index(":::") + 3:]
        data = username + ":::" + msg

        try:
            sock_to_poke = self.find_sock_by_name(send_to)
        except ValueError:
            self.send_msg(current_socket, "Could not find {0}".format(send_to), SendTypeEnum.TYPE_MSG)
        else:
            self.send_msg(sock_to_poke, data, SendTypeEnum.TYPE_POKE)
            self.send_msg(current_socket, "You poked {0} with message: {1}".format(send_to, msg), SendTypeEnum.TYPE_MSG)

    # ---------------------------------------------------#
    # ----------------CONNECTION MANAGEMENT--------------#
    # ---------------------------------------------------#

    def run(self):  # Rewrite!
        while True:
            rlist, wlist, xlist = select.select(self.connection_list, [], [])
            for current_socket in rlist:
                if current_socket is self.chat_server_socket:
                    (new_socket, address) = self.chat_server_socket.accept()
                    recv_data = new_socket.recv(1024).strip()
                    (d_type, arg), data = struct.unpack("!II", recv_data[:8]), recv_data[8:]

                    if d_type == ReceiveTypeEnum.TYPE_LOGIN:
                        self.login_handler(data, new_socket, address)
                    elif d_type == ReceiveTypeEnum.TYPE_REGISTER:
                        self.registration_handler(data, new_socket, address)
                    else:
                        pass
                else:
                    username = self.sock_to_name(current_socket)
                    try:
                        recv_data = current_socket.recv(1024)
                    except socket.error:
                        self.broadcast_data("{0} left the server".format(username), sock=current_socket)
                        print "{0} {1} left the server".format(username, current_socket.getsockname())
                        self.close_connection(current_socket)

                        self.push_connected_user_list()
                    else:
                        (d_type, arg), data = struct.unpack("!II", recv_data[:8]), recv_data[8:]

                        if d_type == ReceiveTypeEnum.TYPE_MSG:
                            self.message_handler(data, username, current_socket)
                        elif d_type == ReceiveTypeEnum.TYPE_COMMAND:  # command
                            pass
                        elif d_type == ReceiveTypeEnum.TYPE_POKE:
                            self.poke_handler(data, username, current_socket)
