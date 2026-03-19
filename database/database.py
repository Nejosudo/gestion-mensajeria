import sqlite3
import os
import platform
from datetime import datetime, timedelta


def _get_db_path() -> str:
    """Devuelve la ruta del archivo .db en el directorio Roaming del sistema."""
    sistema = platform.system()
    if sistema == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sistema == "Darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:  # Linux
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))

    directorio = os.path.join(base, "MensajeriaApp")
    os.makedirs(directorio, exist_ok=True)
    return os.path.join(directorio, "mensajeria.db")


DB_PATH = _get_db_path()


def get_connection() -> sqlite3.Connection:
    """Crea y retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():

    """Crea las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Migración: Agregar columna liquidacion_id a Servicios si no existe ---
    try:
        cursor.execute("PRAGMA table_info(Servicios);")
        cols = [c[1] for c in cursor.fetchall()]
        if "liquidacion_id" not in cols:
            cursor.execute("ALTER TABLE Servicios ADD COLUMN liquidacion_id INTEGER NULL;")
            conn.commit()
    except Exception as e:
        print("[Migración liquidacion_id]", e)

    # --- Migración: Agregar columna base_actual a Mensajeros ---
    try:
        cursor.execute("PRAGMA table_info(Mensajeros);")
        cols = [c[1] for c in cursor.fetchall()]
        if "base_actual" not in cols:
            cursor.execute("ALTER TABLE Mensajeros ADD COLUMN base_actual REAL DEFAULT 0;")
            conn.commit()
    except Exception as e:
        print("[Migración base_actual]", e)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Mensajeros (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            telefono    TEXT    NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Servicios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mensajero_id    INTEGER NOT NULL,
            valor           REAL    NOT NULL DEFAULT 5000,
            fecha           TEXT    NOT NULL,
            descripcion     TEXT    DEFAULT '',
            liquidacion_id  INTEGER,
            FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE CASCADE
        );
    """)

    # --- Migración: Si la tabla Servicios tiene columna 'estado' y no tiene 'descripcion', migrar datos ---
    try:
        cursor.execute("PRAGMA table_info(Servicios);")
        cols = [c[1] for c in cursor.fetchall()]
        if "estado" in cols and "descripcion" not in cols:
            # Renombrar tabla vieja
            cursor.execute("ALTER TABLE Servicios RENAME TO Servicios_old;")
            # Crear nueva tabla
            cursor.execute("""
                CREATE TABLE Servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mensajero_id INTEGER NOT NULL,
                    valor REAL NOT NULL DEFAULT 5000,
                    fecha TEXT NOT NULL,
                    descripcion TEXT DEFAULT '',
                    FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE CASCADE
                );
            """)
            # Copiar datos (sin estado)
            cursor.execute("INSERT INTO Servicios (id, mensajero_id, valor, fecha) SELECT id, mensajero_id, valor, fecha FROM Servicios_old;")
            cursor.execute("DROP TABLE Servicios_old;")
            conn.commit()
    except Exception as e:
        print("[Migración Servicios]", e)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Liquidaciones (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            mensajero_id        INTEGER NOT NULL,
            fecha               TEXT    NOT NULL,
            subtotal_servicios  REAL    NOT NULL,
            comision_empresa    REAL    NOT NULL,
            descuento_aseo      REAL    NOT NULL DEFAULT 1000,
            base_prestada       REAL    NOT NULL DEFAULT 0,
            neto_mensajero      REAL    NOT NULL,
            FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# ── CRUD Mensajeros ─────────────────────────────────────────────────

def crear_mensajero(nombre: str, telefono: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Mensajeros (nombre, telefono) VALUES (?, ?)", (nombre, telefono))
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def obtener_mensajeros(busqueda: str = "") -> list[dict]:
    conn = get_connection()
    if busqueda:
        rows = conn.execute(
            "SELECT * FROM Mensajeros WHERE nombre LIKE ? OR telefono LIKE ? ORDER BY nombre",
            (f"%{busqueda}%", f"%{busqueda}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM Mensajeros ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def actualizar_mensajero(id_: int, nombre: str, telefono: str):
    conn = get_connection()
    conn.execute("UPDATE Mensajeros SET nombre=?, telefono=? WHERE id=?", (nombre, telefono, id_))
    conn.commit()
    conn.close()


def eliminar_mensajero(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM Mensajeros WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def actualizar_base_mensajero(id_: int, base: float):
    conn = get_connection()
    conn.execute("UPDATE Mensajeros SET base_actual=? WHERE id=?", (base, id_))
    conn.commit()
    conn.close()


# ── Servicios ────────────────────────────────────────────────────────

def crear_servicio(mensajero_id: int, valor: float = 5000) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO Servicios (mensajero_id, valor, fecha, descripcion) VALUES (?, ?, ?, '')",
        (mensajero_id, valor, fecha)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def obtener_servicios_pendientes(mensajero_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM Servicios WHERE mensajero_id=? AND liquidacion_id IS NULL ORDER BY fecha DESC",
        (mensajero_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_servicios_del_dia(mensajero_id: int) -> list[dict]:
    """Obtiene solo los servicios PENDIENTES del día para el mensajero."""
    conn = get_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM Servicios WHERE mensajero_id=? AND fecha LIKE ? AND liquidacion_id IS NULL ORDER BY fecha DESC",
        (mensajero_id, f"{hoy}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def actualizar_valor_servicio(id_servicio: int, nuevo_valor: float):
    conn = get_connection()
    conn.execute("UPDATE Servicios SET valor=? WHERE id=?", (nuevo_valor, id_servicio))
    conn.commit()
    conn.close()

def actualizar_descripcion_servicio(id_servicio: int, nueva_desc: str):
    conn = get_connection()
    conn.execute("UPDATE Servicios SET descripcion=? WHERE id=?", (nueva_desc, id_servicio))
    conn.commit()
    conn.close()


def eliminar_servicio(id_servicio: int):
    conn = get_connection()
    conn.execute("DELETE FROM Servicios WHERE id=?", (id_servicio,))
    conn.commit()
    conn.close()



# ── Liquidaciones ─────

def obtener_servicios_por_liquidacion(mensajero_id: int, fecha_liquidacion: str) -> list[dict]:
    """Obtiene los servicios liquidados para un mensajero en la fecha exacta de la liquidación (±1 min)."""
    conn = get_connection()
    # Buscar servicios asociados a la liquidación
    rows = conn.execute(
        "SELECT * FROM Servicios WHERE mensajero_id=? AND liquidacion_id=? ORDER BY fecha",
        (mensajero_id, fecha_liquidacion)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def ejecutar_liquidacion(mensajero_id: int, base: float = 0, pendientes: list = None) -> dict | None:
    """
    Agrupa servicios pendientes, descuenta base y registra la liquidación.
    """
    if pendientes is None:
        pendientes = obtener_servicios_pendientes(mensajero_id)
        
    if not pendientes:
        return None

    subtotal = sum(s["valor"] for s in pendientes)
    comision = subtotal * 0.20
    descuento_aseo = 1000
    # El neto es la ganancia por el trabajo (80% menos aseo)
    neto = (subtotal * 0.80) - descuento_aseo
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    # Registrar liquidación (la base se guarda por separado)
    cursor.execute("""
        INSERT INTO Liquidaciones (mensajero_id, fecha, subtotal_servicios,
                                   comision_empresa, descuento_aseo, base_prestada, neto_mensajero)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (mensajero_id, fecha, subtotal, comision, descuento_aseo, base, neto))
    liq_id = cursor.lastrowid

    # Asignar liquidacion_id a los servicios liquidados
    ids_servicios = [s["id"] for s in pendientes]
    placeholders = ",".join("?" * len(ids_servicios))
    cursor.execute(
        f"UPDATE Servicios SET liquidacion_id=? WHERE id IN ({placeholders})",
        (liq_id, *ids_servicios)
    )

    conn.commit()
    conn.close()

    return {
        "id": liq_id,
        "cantidad_servicios": len(pendientes),
        "subtotal": subtotal,
        "comision": comision,
        "descuento_aseo": descuento_aseo,
        "neto": neto,
        "fecha": fecha,
    }


def obtener_liquidaciones(filtro: str = "todo") -> list[dict]:
    """
    Devuelve liquidaciones filtradas. filtro: 'hoy', 'semana', 'mes', 'todo'.
    """
    conn = get_connection()
    hoy = datetime.now()

    query_base = """
        SELECT L.*, M.nombre AS mensajero_nombre, M.telefono AS mensajero_telefono
        FROM Liquidaciones L
        JOIN Mensajeros M ON L.mensajero_id = M.id
    """

    if filtro == "hoy":
        fecha_inicio = hoy.strftime("%Y-%m-%d")
        query = query_base + " WHERE L.fecha LIKE ? ORDER BY L.fecha DESC"
        rows = conn.execute(query, (f"{fecha_inicio}%",)).fetchall()
    elif filtro == "semana":
        inicio_semana = (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")
        query = query_base + " WHERE L.fecha >= ? ORDER BY L.fecha DESC"
        rows = conn.execute(query, (inicio_semana,)).fetchall()
    elif filtro == "mes":
        inicio_mes = hoy.strftime("%Y-%m-01")
        query = query_base + " WHERE L.fecha >= ? ORDER BY L.fecha DESC"
        rows = conn.execute(query, (inicio_mes,)).fetchall()
    else:
        query = query_base + " ORDER BY L.fecha DESC"
        rows = conn.execute(query).fetchall()

    conn.close()
    return [dict(r) for r in rows]
