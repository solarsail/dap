from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dap.config import CONF


Base = declarative_base()

class DBEngine(object):
    def __init__(self, user, password, host='127.0.0.1', port=3306, db=None):
        db = db if db else '{}_db'.format(user)
        self.engine = create_engine('mysql://{}:{}@{}:{}/{}'.format(user, password, host, port, db))
        self.session = sessionmaker(bind=self.engine)


    @contextmanager
    def new_session(self):
        session = self.session(bind=self.engine)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


    def connect(self):
        return self.engine.connect()


    def columns(self, table):
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table)
        return [c['name'] for c in columns]

_db_cfg = CONF['db']
LOCAL_CONN = DBEngine(_db_cfg['username'], _db_cfg['password'])
Base.metadata.create_all(LOCAL_CONN.engine)
