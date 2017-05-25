class Client:
    def __init__(self, name, sock, is_admin=False, is_muted=False):
        self.name = name
        self.sock = sock
        self.is_admin = is_admin
        self.is_muted = is_muted

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        return self.is_muted

    def toggle_admin(self):
        self.is_admin = not self.is_admin
        return self.is_admin
