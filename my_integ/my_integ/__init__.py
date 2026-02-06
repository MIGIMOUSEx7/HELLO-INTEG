import pymysql

# This is the magic line that tricks Django's version check
pymysql.version_info = (2, 2, 1, 'final', 0) 

pymysql.install_as_MySQLdb()