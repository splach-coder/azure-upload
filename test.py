import mysql.connector

db_config = {
    "host": "mysql-webapp-internal.mysql.database.azure.com", 
    "user": "mysqldb_webapp_internal_write",  
    "password": "HdAYnxZe3954u@d",
    "database": "mysqldb-webapp-internal",
    "port": 3306,
    "ssl_ca": "C:/Users/pc/Downloads/DigiCertGlobalRootG2.crt.pem", 
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

cursor.execute("SHOW TABLES")
for table in cursor:
    print(table)

cursor.close()
conn.close()