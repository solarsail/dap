from dap.db import Base, LOCAL_CONN, DBEngine
from dap.utils import init_superuser
from dap.config import CONF

# create dapadmin db
_db_cfg = CONF['db']
engine = DBEngine(_db_cfg['username'], _db_cfg['password'], db=None)
engine.connect().execute("CREATE DATABASE IF NOT EXISTS dapadmin")
# create tables
Base.metadata.create_all(LOCAL_CONN.engine)
init_superuser()
