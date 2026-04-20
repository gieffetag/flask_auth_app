import random
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields

from flask_login import UserMixin

from . import utils
from .database import db


@dataclass(slots=True)
class User(UserMixin):
    user_id: str = ""
    email: str = ""
    password: str = ""
    name: str = ""
    is_active_account: int = 0
    is_verified: int = 0
    verification_code: str = ""
    is_admin: str = ""
    ins_ts: str = field(default_factory=utils.now)
    upd_ts: str = field(default_factory=utils.now)
    # errors: dict = field(init=False)

    @classmethod
    def create_table(cls):
        sql = """
        CREATE TABLE IF NOT EXISTS user (
            user_id                  VARCHAR(32) NOT NULL PRIMARY KEY,
            email                    varchar(100) NOT NULL,
            password                 varchar(100) NOT NULL,
            name                     varchar(255),
            is_active_account        tinyint(1) not null default 0,
            is_verified              tinyint(1) not null default 0,
            verification_code        varchar(6) not null default '',
            is_admin                 varchar(1) NOT NULL default 'N',
            ins_ts                   DATETIME NOT NULL,
            upd_ts                   DATETIME NOT NULL,
            UNIQUE(email)
        );
        """
        db.execute(sql)

    def check(self):
        self.errors = {}
        return len(self.errors) == 0

    @property
    def is_active(self):
        return True if self.is_active_account else False

    def get_id(self):
        return self.user_id if self.user_id else None

    def add(self):
        self.user_id = self.email.replace("@", "_")
        self.is_active_account = 1
        sql = """
            insert into user
                (user_id, email, password, name, is_active_account, is_admin, ins_ts, upd_ts)
            values
                (:user_id, :email, :password, :name, :is_active_account, :is_admin, :ins_ts, :upd_ts)
        """  # noqa: E501
        with db.transaction() as conn:
            db.execute(sql, conn, **asdict(self))
        return self.user_id

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        if not self.user_id:
            raise ValueError("User id cannot be null")
        sql = """
            update user set
                verification_code = :verification_code,
                is_verified = 0
            where user_id = :user_id
        """
        with db.transaction() as conn:
            db.execute(
                sql,
                conn,
                user_id=self.user_id,
                verification_code=self.verification_code,
            )
        return self.verification_code

    def verified(self):
        if not self.user_id:
            raise ValueError("User id cannot be null")
        self.verification_code = ""
        self.is_verified = 1
        sql = """
            update user set
                verification_code = :verification_code,
                is_verified = :is_verified
            where user_id = :user_id
        """
        with db.transaction() as conn:
            db.execute(
                sql,
                conn,
                user_id=self.user_id,
                verification_code=self.verification_code,
                is_verified=self.is_verified,
            )
        return self.verification_code

    def update_password(self, new_password_hash):
        if not self.user_id:
            raise ValueError("User id cannot be null")
        self.password = new_password_hash
        self.is_verified = 1
        self.verification_code = ""
        sql = """
            update user set
                password = :password,
                is_verified = 1,
                verification_code = '',
                upd_ts = :upd_ts
            where user_id = :user_id
        """
        with db.transaction() as conn:
            db.execute(
                sql,
                conn,
                user_id=self.user_id,
                password=self.password,
                upd_ts=utils.now(),
            )

    def update_name(self, new_name):
        if not self.user_id:
            raise ValueError("User id cannot be null")
        self.name = new_name
        sql = "update user set name = :name, upd_ts = :upd_ts where user_id = :user_id"
        with db.transaction() as conn:
            db.execute(
                sql, conn, name=self.name, upd_ts=utils.now(), user_id=self.user_id
            )

    def update_email(self, new_email):
        if not self.user_id:
            raise ValueError("User id cannot be null")
        self.email = new_email
        self.is_verified = 0
        sql = """
            update user set
                email = :email,
                is_verified = 0,
                upd_ts = :upd_ts
            where user_id = :user_id
        """
        with db.transaction() as conn:
            db.execute(
                sql, conn, email=self.email, upd_ts=utils.now(), user_id=self.user_id
            )

    def delete_account(self):
        if not self.user_id:
            raise ValueError("User id cannot be null")
        sql = "delete from user where user_id = :user_id"
        with db.transaction() as conn:
            db.execute(sql, conn, user_id=self.user_id)

    @classmethod
    def select(cls, **kwargs):
        sql = ["select * from user"]
        if kwargs:
            sql.append("where 1 = 1")
            field_list = [f.name for f in fields(cls)]
            for k in kwargs:
                if k not in field_list:
                    raise RuntimeError(f"Campo {k} non presente nella tabella")
                sql.append(f"and {k} = :{k}")
        sql = "\n".join(sql)
        result = db.query(sql, **kwargs)
        return [cls(**rec) for rec in result]

    @classmethod
    def get(cls, user_id):
        sql = "select * from user where user_id = :user_id"
        result = db.query(sql, user_id=user_id)
        return cls(**result[0]) if result else None


class Counter:
    def __init__(self, name):
        self.name = name

    @classmethod
    def create_table(cls):
        sql = """
            CREATE TABLE IF NOT EXISTS `counter` (
              `counter` int(10) NOT NULL,
              `name` varchar(255) NOT NULL,
              PRIMARY KEY (`name`)
            )
        """
        db.execute(sql)

    def get(self):
        with db.transaction() as conn:
            sql = "select counter from counter where name = :name"
            res = db.query(sql, conn, name=self.name)
            if res:
                sql = "update counter set counter = counter + 1 where name = :name"
            else:
                sql = "insert into counter (counter, name) values (1, :name)"
            db.execute(sql, conn, name=self.name)
            sql = "select counter from counter where name = :name"
            res = db.query(sql, conn, name=self.name)
        return res[0]["counter"]


def create_all():
    Counter.create_table()
    User.create_table()


def drop_all():
    for tbl in ("counter", "user"):
        sql = f"DROP TABLE IF EXISTS {tbl}"
        db.execute(sql)
