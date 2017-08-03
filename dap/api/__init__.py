from dap.api.test import TestResource
from dap.api.mysql import RDBTableAccess, RDBRowAccess
from dap.api.register import Register
from dap.api.privilege import Privilege
from dap.api.key_mgmt import KeyManagement

test = TestResource()
mysql_table = RDBTableAccess()
mysql_row = RDBRowAccess()
register = Register()
privilege = Privilege()
key_mgmt = KeyManagement()

__all__ = [test, mysql_table, mysql_row, register, privilege, key_mgmt]
