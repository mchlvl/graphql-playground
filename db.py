from databases import Database

DATABASE_URL = "postgresql://user:pass@localhost/graphql_db"
database = Database(DATABASE_URL)


async def connect():
    await database.connect()


async def disconnect():
    await database.disconnect()
