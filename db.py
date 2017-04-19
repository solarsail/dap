from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DbConnection(object):
    def __init__(self, user, password, host='127.0.0.1', port=3306):
        self.engine = create_engine('mysql://{}:{}@{}:{}/{}_db'.format(user, password, host, port, user))
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

LOCAL_CONN = DbConnection('dapadmin', '123456') # TODO: use config
Base.metadata.create_all(LOCAL_CONN.engine)
