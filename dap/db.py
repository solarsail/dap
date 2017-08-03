from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dap.config import CONF


Base = declarative_base()

class DBEngine(object):
    def __init__(self, user, password, db, host='127.0.0.1', port=3306):
        conn_str = 'mysql://{}:{}@{}:{}'.format(user, password, host, port)
        if db:
            conn_str = '/'.join([conn_str, db])
        self.engine = create_engine(conn_str)
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

    def tables(self, db):
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(db)
        return tables


_db_cfg = CONF['db']
LOCAL_CONN = DBEngine(_db_cfg['username'], _db_cfg['password'], 'dapadmin')
