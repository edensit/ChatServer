class ChatRoom:
    def __init__(self, channel_id, name, max_clients, is_admin_only=False):
        self.channel_id = channel_id
        self.name = name
        self.max_clients = max_clients
        self.is_admin_only = is_admin_only
        self.client_list = []
