import sqlite3


class BaseError(Exception):
    pass


class LoginError(BaseError):
    pass


class RegisterError(BaseError):
    pass


class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect("usersdatabase.db")
        self.sql_db = self.conn.cursor()

    def is_correct_login(self, username, password):
        self.sql_db.execute("SELECT * FROM users_table WHERE Username = ?"
                            " COLLATE NOCASE AND Password = ?", (username, password))
        return self.sql_db.fetchall()

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
# http://stackoverflow.com/questions/420843/how-does-password-salt-help-against-a-rainbow-table-attack?noredirect=1&lq=1


