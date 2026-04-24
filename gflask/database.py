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

    def _run(self, sql, conn, mode, **kwargs):
        """Metodo centrale per eseguire le query ed estrarre i dati in sicurezza."""
        if not self.engine:
            raise RuntimeError("Database non inizializzato. Chiama init_app().")

        sql_text = text(sql)

        # Funzione interna che sa cosa estrarre dal risultato in base al "mode"
        def extract_data(result):
            if mode == "query":
                return [dict(row) for row in result.mappings()]
            elif mode == "insert":
                return result.lastrowid
            else:  # execute
                return result.rowcount

        # Se ci viene passata una connessione aperta (es. in una transazione)
        if conn is not None:
            return extract_data(conn.execute(sql_text, kwargs))

        # Altrimenti gestiamo noi l'apertura e chiusura automatica
        # Usiamo connect() per le letture e begin() per le scritture
        context = self.engine.connect() if mode == "query" else self.engine.begin()
        with context as c:
            # Estraiamo i dati PRIMA che il context manager chiuda la connessione
            return extract_data(c.execute(sql_text, kwargs))

    def query(self, sql, conn=None, **kwargs):
        return self._run(sql, conn, "query", **kwargs)

    def execute(self, sql, conn=None, **kwargs):
        return self._run(sql, conn, "execute", **kwargs)

    def insert(self, sql, conn=None, **kwargs):
        return self._run(sql, conn, "insert", **kwargs)

    @contextmanager
    def transaction(self):
        """Restituisce esplicitamente l'oggetto connessione da passare alle funzioni."""
        with self.engine.begin() as conn:
            yield conn


db = Database()
