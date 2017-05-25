import sqlite3
import hash_handling


class UserDetailsTypeEnum:
    USERNAME = 0
    PASSWORD = 1
    IS_ADMIN = 2
    IS_MUTED = 3
    SALT = 4


class BaseError(Exception):
    pass


class LoginError(BaseError):
    pass


class RegisterError(BaseError):
    pass


class DatabaseHandler:
    def __init__(self):
        try:
            self.conn = sqlite3.connect("database\usersdatabase.db")
        except sqlite3.Error:
            pass
        else:
            self.sql_db = self.conn.cursor()

    def is_correct_login(self, username, password):
        username = username.decode('utf8')
        password = password.decode('utf8')
        self.sql_db.execute("SELECT * FROM users_table WHERE Username = ? COLLATE NOCASE", (username,))

        auth_details = self.sql_db.fetchall()
        if auth_details:

            username = auth_details[0][UserDetailsTypeEnum.USERNAME]
            hashed_password = auth_details[0][UserDetailsTypeEnum.PASSWORD]
            is_admin = bool(auth_details[0][UserDetailsTypeEnum.IS_ADMIN])
            is_muted = bool(auth_details[0][UserDetailsTypeEnum.IS_MUTED])
            salt = auth_details[0][UserDetailsTypeEnum.SALT]
            hashed_enterd_pass_salt = hash_handling.HashHandler.generate_hash(password, salt)

            if hashed_password == hashed_enterd_pass_salt:
                return (True, username, is_admin, is_muted)
            return False,
        else:
            return False,

    def insert_new_user(self, username, password):
        self.sql_db.execute("SELECT * FROM users_table WHERE Username = ? COLLATE NOCASE", (username,))
        auth_details = self.sql_db.fetchall()

        if not auth_details:
            salt = hash_handling.HashHandler.generate_salt()
            salted_password = hash_handling.HashHandler.generate_hash(password, salt)

            try:
                self.sql_db.execute("INSERT OR IGNORE INTO users_table"
                                    " (Username, Password, Salt) VALUES (?, ?, ?);", (username, salted_password, salt))
                self.conn.commit()
            except sqlite3.IntegrityError:
                raise RegisterError("User already exists")
            except sqlite3.OperationalError:
                raise RegisterError("SQLite DB locked")
        else:
            raise RegisterError("User already exists")



# http://stackoverflow.com/questions/1054022/best-way-to-store-password-in-database - HASHING & SALT
# https://www.codeproject.com/Articles/704865/Salted-Password-Hashing-Doing-it-Right - HASHING
# http://stackoverflow.com/questions/420843/how-does-password-salt-help-against-a-rainbow-table-attack?noredirect=1&lq=1


