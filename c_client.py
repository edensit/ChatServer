class Client:
    def __init__(self, name, sock, is_admin=False, is_muted=False):
        self.name = name
        self.sock = sock
        self.is_admin = is_admin
        self.is_muted = is_muted
