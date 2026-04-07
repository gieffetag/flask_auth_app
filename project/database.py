from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import text


class Database:
    def __init__(self):
        self.engine = None

    def init_app(self, database_url, **kwargs):
        """Inizializza l'engine. Da chiamare in create_app()"""
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url, connect_args={"check_same_thread": False}
            )
        else:
            self.engine = create_engine(database_url, **kwargs)
        if database_url.startswith("sqlite"):

            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    def _execute(self, sql, conn, **kwargs):
        if not self.engine:
            raise RuntimeError("Database non inizializzato. Chiama init_app().")

        sql_text = text(sql)
        if conn is not None:
            # Usiamo la connessione esplicita passata dalla transazione
            return conn.execute(sql_text, kwargs)
        else:
            # Nessuna connessione: facciamo un'operazione autocommit
            with self.engine.begin() as c:
                return c.execute(sql_text, kwargs)

    def query(self, sql, conn=None, **kwargs):
        result = self._execute(sql, conn, **kwargs)
        return [dict(row) for row in result.mappings()]

    def execute(self, sql, conn=None, **kwargs):
        result = self._execute(sql, conn, **kwargs)
        return result.rowcount

    def insert(self, sql, conn=None, **kwargs):
        result = self._execute(sql, conn, **kwargs)
        return result.lastrowid

    @contextmanager
    def transaction(self):
        """Restituisce esplicitamente l'oggetto connessione da passare alle funzioni."""
        with self.engine.begin() as conn:
            yield conn


db = Database()
