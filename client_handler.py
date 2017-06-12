"""
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


if not auth[UserDetailsTypeEnum.IS_IN_DATABASE]:
    self.send_msg(new_socket, "Incorrect username or password!", LoginAuthStateEnum.INCORRECT_AUTH)
    new_socket.close()
    print "Login failed: Name: {0} Reason: incorrect username or password!".format(username)

username = auth[UserDetailsTypeEnum.USERNAME]
elif username not in self.connected_user_list():
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

"""

