import string
import random
import logging

from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, Integer, String, Boolean

from dap.db import Base, DBEngine
from dap.config import CONF


log = logging.getLogger(__name__)


def generate_random_str(length=32):
    """Generates a random string of a specified length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))



class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    app = Column(String(32), nullable=False, unique=True)  # app name
    desc = Column(String(256), nullable=False)             # app description
    user = Column(String(32), nullable=False, unique=True) # generated DB user
    pswd = Column(String(32), nullable=False)              # generated DB password
    key = Column(String(87), nullable=True)                # hashed API key
    is_admin = Column(Boolean, nullable=False)             # flag of admin key (used by this service only)

    def __repr__(self):
        return "<User(app='{}', desc='{}', user='{}', pswd='{}', is_admin={})>".format(self.app, self.desc, self.user, self.pswd, self.is_admin)

    @classmethod
    def new(cls, app, desc, is_admin=False):
        """Creates a new user instance.

        The user password is hashed using passlib; DB password is generated randomly.
        """
        user = "app_{}".format(generate_random_str(6))
        pswd = generate_random_str()
        return User(app=app, desc=desc, user=user, pswd=pswd, key=None, is_admin=is_admin)

    @classmethod
    def auth(cls, session, key):
        """
        Perfroms user authentication.

        Returns the user object if success, None otherwise.
        """
        try:
            users = session.query(cls).all()
            for user in users:
                if pbkdf2_sha256.verify(key, user.key):
                    # Cannot use user object outside the session scope,
                    # since the object has to be bound to a DB session.
                    return {
                        'id': user.id,
                        'app': user.app,
                        'desc': user.desc,
                        'user': user.user,
                        'pswd': user.pswd,
                        'is_admin': user.is_admin,
                    }

            else:
                log.warning("Invalid key: {}".format(key))
                return None
        except Exception as ex:
            log.exception(ex)
            return None

    def issue_key(self):
        """Issues an api key for this app."""
        key = generate_random_str()
        hashed_key = pbkdf2_sha256.hash(key)
        self.key = hashed_key
        return key


_user_engines = {} # DB connection cache

def user_db_engine(user):
    """
    Get DB engine object from cache. Called in Login handler.

    Args:
        user(dict): user dict obtained from request context.
    """
    dbuser = user['name']
    if dbuser not in _user_engines:
        engine = DBEngine(dbuser, user['pswd'], CONF['shared_db']['name'])
        _user_engines[dbuser] = engine

    return _user_engines[dbuser]



if __name__ == '__main__':
    conn = DBEngine('dapadmin', '123456')
    Base.metadata.create_all(conn.engine)

    with conn.new_session() as session:
        user = User.new(app='app1', desc='app1 description')
        key = user.issue_key()
        print(user)
        session.add(user)

    with conn.new_session() as session:
        user = User.auth(session, key)
        print(user)
