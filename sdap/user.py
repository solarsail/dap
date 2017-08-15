import string
import random
import logging

from passlib.hash import pbkdf2_sha256
from sqlalchemy import Column, Integer, String, Boolean

from sdap.db import Base, DBEngine
from sdap.config import CONF


log = logging.getLogger(__name__)


def generate_random_str(length=32):
    """Generates a random string of a specified length.

    Contains only ASCII letters (upper & lower cases) and digits.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


_user_cache = {}

class User(Base):
    """ORM class of DB table `user`.

    This effectively represents a client application (app),
    but named `User` for some historical reason.
    FIXME: Needs a rename.
    """
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
        """Perfroms app authentication.

        Args:
            session(object): a valid sqlalchemy session.
            key(str):        the api key.

        Returns:
            A user dict if success, None otherwise.
        """
        if key in _user_cache:
            return _user_cache[key]

        try:
            users = session.query(cls).all()
            for user in users:
                if pbkdf2_sha256.verify(key, user.key):
                    # Cannot use user object outside the session scope,
                    # since the object has to be bound to a DB session.
                    info = {
                        'id': user.id,
                        'app': user.app,
                        'desc': user.desc,
                        'user': user.user,
                        'pswd': user.pswd,
                        'is_admin': user.is_admin,
                    }
                    _user_cache[key] = info
                    return info

            else:
                log.warning("Invalid key: {}".format(key))
                return None
        except Exception as ex:
            log.exception(ex)
            return None

    @classmethod
    def modify_user(cls, session, app, func):
        """Loads the user which match the app name, and
        updates the user in both object representation and in DB.

        Args:
            app(str):       app name
            func(function): a function or lambda which has the following form:
                            ```
                            def func(user)
                            ```
                            If the function has a return value, it will be
                            returned by this method.

        Returns:
            Whatever `func` returns.

        Raises:
            HTTPBadRequestError: if app doesn't match any record in DB.
        """
        try:
            user = session.query(cls).filter_by(app=app).one()
            if func:
                ret = func(user)
                if not user.key:
                    _user_cache.pop(user.key, None)
                return ret
        except exc.NoResultFound:
            raise exceptions.HTTPBadRequestError("app not exist")

    @classmethod
    def get_user(cls, session, app):
        """Loads the user which match the app name.

        Returns:
            A user dict if the app matches.

        Raises:
            HTTPBadRequestError: if app doesn't match any record in DB.
        """
        try:
            user = session.query(cls).filter_by(app=app).one()
            return {
                'id': user.id,
                'app': user.app,
                'desc': user.desc,
                'user': user.user,
                'pswd': user.pswd,
                'is_admin': user.is_admin,
            }
        except exc.NoResultFound:
            raise exceptions.HTTPBadRequestError("app not exist")

    def issue_key(self):
        """Issues an api key for this app.

        Will hash the key and save into DB for future authentication purpose.

        Returns:
            The original key (not hashed). The application should memorize this key.
        """
        key = generate_random_str()
        hashed_key = pbkdf2_sha256.hash(key)
        self.key = hashed_key
        return key


_user_engines = {} # DB engine cache

def user_db_engine(user):
    """
    Get DB engine object from cache. Called in Login handler.

    Args:
        user(dict): user dict obtained from request context.

    Returns:
        The DB engine associated to the user/app (which operates on behalf
        of the DB user assigned to the app).
    """
    dbuser = user['user']
    conf = CONF['db']
    if dbuser not in _user_engines:
        engine = DBEngine(dbuser, user['pswd'], conf['shared_db'], conf['addr'], conf['port'])
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
