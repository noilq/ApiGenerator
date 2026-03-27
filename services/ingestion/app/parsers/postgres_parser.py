from app.parsers.base import SchemaAdapter

class PostgresAdapter(SchemaAdapter):
    def ingest(self, payload):
        conn = connect(payload["dsn"])
        tables = fetch_tables(conn)
        return build_schema(tables)
