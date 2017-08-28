from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sdap.config import CONF


Base = declarative_base()

_column_name_cache = {}


class DBEngine(object):
    def __init__(self, user, password, db, host='127.0.0.1', port=3306, utf8=True):
        conn_str = 'mysql://{}:{}@{}:{}'.format(user, password, host, port)
        if db:
            conn_str = '/'.join([conn_str, db])
        if utf8:
            conn_str = '?'.join([conn_str, "charset=utf8"])
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
        if table in _column_name_cache:
            return _column_name_cache[table]
        else:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table)
            column_names = [c['name'] for c in columns]
            _column_name_cache[table] = column_names
            return column_names

    def tables(self, db):
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(db)
        return tables


_db_cfg = CONF['db']
LOCAL_CONN = DBEngine(_db_cfg['admin_user'], _db_cfg['admin_pass'], 'dapadmin', _db_cfg['addr'], _db_cfg['port'])
