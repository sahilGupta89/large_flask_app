import os
import time
import psycopg2
from sqlalchemy import create_engine, exc


while True:
    try:
        if "DB_CONNECTION_STRING" in os.environ:
            conn = create_engine(os.environ["DB_CONNECTION_STRING"]).connect()

        if "PGDB_CONNECTION_STRING" in os.environ:
            # conn = create_engine(
            #     os.environ["PGDB_CONNECTION_STRING"]
            # ).connect()
            conn = psycopg2.connect(
                database="devdb",
                user="devuser",
                host="localhost",
                password="password"
             )
        print("")

        break
    except exc.DBAPIError:
        print(".", end="", flush=True)
        time.sleep(0.5)
