import hashlib
import base64
import os


class HashHandler:
    def __init__(self):
        pass

    @staticmethod
    def generate_salt():
        return base64.b64encode(os.urandom(32))

    @staticmethod
    def generate_hash(password, salt):
        return hashlib.sha512(password + salt).hexdigest()


# http://stackoverflow.com/questions/1054022/best-way-to-store-password-in-database - HASHING & SALT
# https://www.codeproject.com/Articles/704865/Salted-Password-Hashing-Doing-it-Right - HASHING
# http://stackoverflow.com/questions/420843/how-does-password-salt-help-against-a-rainbow-table-attack?noredirect=1&lq=1
