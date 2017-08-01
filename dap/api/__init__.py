from dap.api.test import TestResource
from dap.api.mysql import RDBTableAccess, RDBRowAccess
from dap.api.register import Register

test = TestResource()
mysql_table = RDBTableAccess()
mysql_row = RDBRowAccess()
register = Register()

__all__ = [test, mysql_table, mysql_row, register]
