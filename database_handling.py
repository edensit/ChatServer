import sqlite3
import hash_handling


class BaseError(Exception):
    pass


class LoginError(BaseError):
    pass


class RegisterError(BaseError):
    pass


class DatabaseHandler:
    def __init__(self):
        try:
            self.conn = sqlite3.connect("usersdatabase.db")
        except sqlite3.Error:
            pass
        else:
            self.sql_db = self.conn.cursor()

    def is_correct_login(self, username, password):
        self.sql_db.execute("SELECT * FROM users_table WHERE Username = ? COLLATE NOCASE", (username,))
        auth_details = self.sql_db.fetchall()

        hashed_password = auth_details[0][1]
        salt = auth_details[0][4]
        hashed_enterd_pass_salt = hash_handling.HashHandler.generate_hash(password, salt)

        if hashed_password == hashed_enterd_pass_salt:
            return True
        return False

    def insert_new_user(self, username, password):
        try:
            self.sql_db.execute("INSERT OR IGNORE INTO users_table"
                                " (Username, Password) VALUES (?, ?);", (username, password))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise RegisterError("User already exists")
        except sqlite3.OperationalError:
            raise RegisterError("SQLite DB locked")


# http://stackoverflow.com/questions/1054022/best-way-to-store-password-in-database - HASHING & SALT
# https://www.codeproject.com/Articles/704865/Salted-Password-Hashing-Doing-it-Right - HASHING
# http://stackoverflow.com/questions/420843/how-does-password-salt-help-against-a-rainbow-table-attack?noredirect=1&lq=1


