"""Database interface for gatekeeper_api"""

import mysql.connector
from mysql.connector import errorcode
from mysql.connector import pooling  # Added for thread-safe pooling

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
    # Class-level pool to be shared safely across all instances and threads
    _pool = None

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
            print("Wrong database name")
            return False
        
        # Initialize the pool exactly once if it doesn't exist
        if DB._pool is None:
            try:
                # We connect to host without specifying DB first, matching your original logic
                DB._pool = pooling.MySQLConnectionPool(
                    pool_name="gatekeeper_pool",
                    pool_size=15,  # Allows up to 15 concurrent car processing tasks
                    user=self.config['user'],
                    password=self.config['password'],
                    host=self.config['host']
                )
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Wrong user name or password")
                    return False
                else:
                    print(err)
                    return False

        try:
            # Grab a completely fresh, isolated connection from the pool
            cnx = DB._pool.get_connection()
            cur = cnx.cursor()
            cur.execute("USE {}".format(DB_NAME))
            cur.close()
            return cnx
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                print("\nDatabase does not exist")
                self.create_database()
                print("Database {} created successfully.".format(DB_NAME))
                # Try getting the connection again now that the DB exists
                cnx = DB._pool.get_connection()
                cnx.database = DB_NAME
                return cnx
            else:
                print(err)
                return False

    def create_database(self):
        # Establish a temporary un-pooled connection just to build the database layout
        try:
            connection = mysql.connector.connect(
                user=self.config['user'], 
                password=self.config['password'],
                host=self.config['host']
            )
        except mysql.connector.Error as err:
            print("Mysql not connected: {}".format(err))
            return False

        cur = connection.cursor()
        try:
            cur.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
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
        cur.close()
        connection.close()

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
            connection.close()  # With pooling, closing returns it safely to the pool instead of destroying it

    def drop(self):
        # Use a raw connection to drop, ensuring pool objects aren't locked
        try:
            connection = mysql.connector.connect(
                user=self.config['user'], 
                password=self.config['password'],
                host=self.config['host']
            )
            cur = connection.cursor()
            print("Dropping database {}".format(DB_NAME))
            cur.execute("DROP DATABASE {}".format(DB_NAME))
            print("Database {} dropped successfully.".format(DB_NAME))
            cur.close()
            connection.close()
            # Clear out the old pool structure since the schema is gone
            DB._pool = None
        except Exception as err:
            print("Failed to drop database safely: {}".format(err))
