"""Database interface for gatekeeper_api"""

import mysql.connector
from mysql.connector import errorcode

DB_NAME = 'gatekeeper_api'

TABLES = {}

TABLES['gatekeeper_api'] = (
    "CREATE TABLE `gatekeeper_api` ("
    "  `plate_no` int(11) NOT NULL,"
    "  `fuel_type` varchar(14) NOT NULL,"
    "  `permission` enum('yes', 'no'),"
    "  `dt` DATETIME(6) NOT NULL,"
    "  PRIMARY KEY (`plate_no`)"
    ") ENGINE=InnoDB")


class DB:
    __mysql = None

    # mysql configuration
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': '',
    }

    QueryResult = {}
    insert_id = ""
    rowcount = 0
    field = '*'

    def __init__(self, connect=False, **kwargs):
        for key in kwargs:
            if key in self.config:
                self.config[key] = kwargs[key]
        if connect:
            self.connect()

    def connect(self):
        if self.config['database'] != DB_NAME:
            print("Wrong data base name")
            return False
        elif self.__mysql is None:
            try:
                cnx = mysql.connector.connect(user=self.config['user'], password=self.config['password'],
                                              host=self.config['host'])
                self.__mysql = cnx
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Wrong user name or password")
                    return False
                else:
                    print(err)
                    return False
            try:
                cur = cnx.cursor()
                cur.execute("USE {}".format(DB_NAME))
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("\nDatabase does not exist")
                    self.create_database()
                    print("Database {} created successfully.".format(DB_NAME))
                    cnx.database = DB_NAME
                else:
                    print(err)
                    exit(1)
        return self.__mysql

    def create_database(self):
        connection = self.connect()
        if not connection:
            print("Mysql not connected")
            return False
        data = {}
        cur = connection.cursor()
        try:
            cur.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)
        cur.execute("USE {}".format(DB_NAME))
        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                cur.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")

    def insert(self, table, data={}, ignore=False, debug=False):
        ky = []
        val = []
        param = {}
        for key, value in data.items():
            ky.append(key)
            val.append('%(' + key + ')s')
            param[key] = value
        if ignore:
            ins = "INSERT IGNORE INTO " + table + " (" + ','.join(ky) + ") VALUES (" + ','.join(val) + ")"
        else:
            ins = "INSERT INTO " + table + " (" + ','.join(ky) + ") VALUES (" + ','.join(val) + ")"
        self.query(ins, param, 0, debug)

    def query(self, query, param={}, block=0, debug=False):
        connection = self.connect()
        if not connection:
            print("Mysql is not connected")
            return False
        cur = connection.cursor()
        try:
            cur.execute(query, param)
            if hasattr(cur, 'lastrowid'):
                self.insert_id = cur.lastrowid
            self.rowcount = cur.rowcount
            if debug:
                print(cur.statement)
            connection.commit()
        except Exception as err:
            print("An error occurred: {}".format(err))
        finally:
            cur.close()
            connection.close()

    def drop(self):
        connection = self.connect()
        cur = connection.cursor()
        print("Dropping database {}".format(DB_NAME))
        cur.execute("DROP DATABASE {}".format(DB_NAME))
        print("Database {} dropped successfully.".format(DB_NAME))
        cur.close()
        connection.close()
