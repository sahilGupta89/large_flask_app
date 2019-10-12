import os
import time

from sqlalchemy import create_engine, exc
print('inside>>>>>>>>>>>>>>')
while True:
    try:
        if "DB_CONNECTION_STRING" in os.environ:
            conn = create_engine(os.environ["DB_CONNECTION_STRING"]).connect()

        if "PGDB_CONNECTION_STRING" in os.environ:
            conn = create_engine(
                os.environ["PGDB_CONNECTION_STRING"]
            ).connect()
        print("")

        break
    except exc.DBAPIError:
        print(".", end="", flush=True)
        time.sleep(0.5)
