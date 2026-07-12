"""Async Motor-compatible wrapper around mongomock for testing."""

import mongomock


class _AsyncCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    async def to_list(self, length=None):
        docs = list(self._cursor)
        if length is not None:
            return docs[:length]
        return docs

    def sort(self, key_or_list, direction=None):
        self._cursor = self._cursor.sort(key_or_list, direction)
        return self

    def limit(self, limit):
        self._cursor = self._cursor.limit(limit)
        return self

    def skip(self, skip):
        self._cursor = self._cursor.skip(skip)
        return self

    def batch_size(self, batch_size):
        return self


class _AsyncCollectionWrapper:
    def __init__(self, collection, database=None):
        self._collection = collection
        self._database = database
        self.name = collection.name
        self.full_name = collection.full_name

    @property
    def database(self):
        return self._database

    async def find_one(self, filter=None, *args, **kwargs):
        return self._collection.find_one(filter, *args, **kwargs)

    def find(self, *args, **kwargs):
        return _AsyncCursorWrapper(self._collection.find(*args, **kwargs))

    async def insert_one(self, document, *args, **kwargs):
        return self._collection.insert_one(document, *args, **kwargs)

    async def insert_many(self, documents, *args, **kwargs):
        return self._collection.insert_many(documents, *args, **kwargs)

    async def delete_many(self, filter=None, *args, **kwargs):
        return self._collection.delete_many(filter, *args, **kwargs)

    async def update_one(self, filter, update, *args, **kwargs):
        return self._collection.update_one(filter, update, *args, **kwargs)

    async def update_many(self, filter, update, *args, **kwargs):
        return self._collection.update_many(filter, update, *args, **kwargs)

    async def count_documents(self, filter=None, *args, **kwargs):
        return self._collection.count_documents(filter, *args, **kwargs)

    async def create_index(self, keys, *args, **kwargs):
        return self._collection.create_index(keys, *args, **kwargs)

    async def create_indexes(self, indexes, *args, **kwargs):
        return self._collection.create_indexes(indexes, *args, **kwargs)

    async def index_information(self):
        return self._collection.index_information()

    async def list_indexes(self):
        return self._collection.list_indexes()

    async def drop(self, *args, **kwargs):
        return self._collection.drop(*args, **kwargs)

    async def rename(self, new_name, *args, **kwargs):
        return self._collection.rename(new_name, *args, **kwargs)

    async def distinct(self, key, filter=None, *args, **kwargs):
        return self._collection.distinct(key, filter, *args, **kwargs)

    def aggregate(self, pipeline, *args, **kwargs):
        return _AsyncCursorWrapper(self._collection.aggregate(pipeline, *args, **kwargs))

    async def bulk_write(self, operations, *args, **kwargs):
        return self._collection.bulk_write(operations, *args, **kwargs)

    async def find_one_and_update(self, filter, update, *args, **kwargs):
        return self._collection.find_one_and_update(filter, update, *args, **kwargs)

    async def find_one_and_delete(self, filter, *args, **kwargs):
        return self._collection.find_one_and_delete(filter, *args, **kwargs)


class _AsyncDatabaseWrapper:
    def __init__(self, db, client=None):
        self._db = db
        self._client = client
        self.name = db.name

    @property
    def client(self):
        return self._client

    async def list_collection_names(self, *args, **kwargs):
        return self._db.list_collection_names(*args, **kwargs)

    def __getitem__(self, collection_name):
        return _AsyncCollectionWrapper(self._db[collection_name], database=self)

    async def command(self, command, *args, **kwargs):
        try:
            return self._db.command(command, *args, **kwargs)
        except NotImplementedError:
            cmd = command if isinstance(command, str) else next(iter(command), "")
            known = {
                "buildInfo": {"version": "8.0.0", "ok": 1.0},
                "ping": {"ok": 1.0},
                "hello": {"ok": 1.0, "ismaster": True},
                "isMaster": {"ok": 1.0, "ismaster": True},
                "connectionStatus": {"ok": 1.0, "authInfo": {"authenticatedUsers": []}},
                "listDatabases": {"ok": 1.0, "databases": []},
            }
            if cmd in known:
                return known[cmd]
            raise

    async def drop_collection(self, name_or_collection, *args, **kwargs):
        return self._db.drop_collection(name_or_collection, *args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class _AsyncMongoClientWrapper:
    """Drop-in replacement for motor.motor_asyncio.AsyncIOMotorClient backed by mongomock."""

    def __init__(self, *args, **kwargs):
        kwargs.pop("serverSelectionTimeoutMS", None)
        self._client = mongomock.MongoClient(*args, **kwargs)

    def __getitem__(self, db_name):
        return _AsyncDatabaseWrapper(self._client[db_name], client=self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass
