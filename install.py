from dap.db import Base, LOCAL_CONN
from dap.utils import init_superuser


Base.metadata.create_all(LOCAL_CONN.engine)
init_superuser('admin', '123456')
