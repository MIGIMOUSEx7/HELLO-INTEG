import pymysql

# 1. Trick Django into thinking PyMySQL is the 'mysqlclient' driver
pymysql.install_as_MySQLdb()

# 2. Trick Django into thinking the MySQL driver version is 2.2.1+
# This prevents the "mysqlclient 2.2.1 or newer is required" error
pymysql.version_info = (2, 2, 1, 'final', 0)