from dap.api.login import Login
from dap.api.test import TestResource
from dap.api.mysql import RDBTableAccess, RDBRowAccess

login = Login()
test = TestResource()
mysql_table = RDBTableAccess()
mysql_row = RDBRowAccess()

__all__ = [login, test, mysql_table, mysql_row]
