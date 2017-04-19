import string
import random

from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, Integer, String

from db import Base, DbConnection


def generate_random_str(length=32):
    """Generates a random string of a specified length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False, unique=True) # TODO: add unique constraint
    pswd = Column(String(87), nullable=False)
    db_addr = Column(String(16), nullable=False)
    db_port = Column(Integer, nullable=False)
    db_pswd = Column(String(32), nullable=False)

    def __repr__(self):
        return "<User(name='{}', db_addr='{}', db_port={}, db_pswd='{}')>".format(self.name, self.db_addr, self.db_port, self.db_pswd)

    @classmethod
    def new(cls, name, pswd, db_addr, db_port=3306):
        """Creates a new user instance.

        The user password is hashed using passlib; DB password is generated randomly.
        """
        pswd = pbkdf2_sha256.hash(pswd)
        db_pswd = generate_random_str()
        return User(name=name, pswd=pswd, db_addr=db_addr, db_port=db_port, db_pswd=db_pswd)

    @classmethod
    def auth(cls, session, name, pswd):
        """Perfroms user authentication.

        Returns the user object if success, None otherwise.
        """
        try:
            user = session.query(cls).filter_by(name=name).one()
            if pbkdf2_sha256.verify(pswd, user.pswd):
                return user
            else:
                # TODO: log
                return None
        except:
            # TODO: log
            return None



if __name__ == '__main__':
    conn = DbConnection('dapadmin', '123456')
    Base.metadata.create_all(conn.engine)

    with conn.new_session() as session:
        user = User.new(name='app1', pswd='123qwe', db_addr='192.168.1.33')
        print(user)
        session.add(user)

    with conn.new_session() as session:
        user = User.auth(session, 'app1', '123qwe')
        print(user)
