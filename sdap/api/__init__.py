from sdap.api.mysql import RDBTableAccess, RDBRowAccess, RDBTableCount
from sdap.api.register import Register
from sdap.api.privilege import Privilege
from sdap.api.key_mgmt import KeyManagement

mysql_table = RDBTableAccess()
mysql_row = RDBRowAccess()
mysql_count = RDBTableCount()
register = Register()
privilege = Privilege()
key_mgmt = KeyManagement()

__all__ = [mysql_table, mysql_row, mysql_count, register, privilege, key_mgmt]
