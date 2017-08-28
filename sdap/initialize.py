from sdap.db import Base, LOCAL_CONN, DBEngine
from sdap.utils import init_superuser
from sdap.config import CONF


def init():
    # create dapadmin db
    _db_cfg = CONF['db']
    engine = DBEngine(_db_cfg['admin_user'], _db_cfg['admin_pass'], None, _db_cfg['addr'], _db_cfg['port'], utf8=False)
    engine.connect().execute("CREATE DATABASE IF NOT EXISTS dapadmin")
    # create tables
    Base.metadata.create_all(LOCAL_CONN.engine)
    init_superuser()
