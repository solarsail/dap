from dap.api.login import Login
from dap.api.test import TestResource
from dap.api.rdbms import RDBTableAccess, RDBRowAccess

login = Login()
test = TestResource()
rdbms_table = RDBTableAccess()
rdbms_row = RDBRowAccess()

__all__ = [login, test, rdbms_table, rdbms_row]
