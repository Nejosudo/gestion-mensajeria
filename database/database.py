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

    # Primero: Crear las tablas base si no existen para evitar errores en las migraciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Mensajeros (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            telefono    TEXT    NOT NULL,
            base_actual REAL    DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Servicios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mensajero_id    INTEGER,
            valor           REAL    NOT NULL DEFAULT 5000,
            fecha           TEXT    NOT NULL,
            descripcion     TEXT    DEFAULT '',
            liquidacion_id  INTEGER,
            FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Liquidaciones (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            mensajero_id        INTEGER,
            mensajero_nombre    TEXT,
            mensajero_telefono  TEXT,
            fecha               TEXT    NOT NULL,
            subtotal_servicios  REAL    NOT NULL,
            comision_empresa    REAL    NOT NULL,
            descuento_aseo      REAL    NOT NULL DEFAULT 1000,
            base_prestada       REAL    NOT NULL DEFAULT 0,
            neto_mensajero      REAL    NOT NULL,
            FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE SET NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Gastos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            fecha       TEXT    NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Clientes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL UNIQUE,
            direccion   TEXT    DEFAULT '',
            telefono    TEXT    DEFAULT '',
            fecha_registro TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Turnero (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            mensajero_id INTEGER UNIQUE NOT NULL,
            fecha_entrada TEXT NOT NULL,
            FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE CASCADE
        );
    """)

    # --- Migración: Clientes columns ---
    try:
        cursor.execute("PRAGMA table_info(Clientes);")
        cols = [c[1] for c in cursor.fetchall()]
        if "fecha_registro" not in cols:
            cursor.execute("ALTER TABLE Clientes ADD COLUMN fecha_registro TEXT DEFAULT '';")
            conn.commit()
    except Exception as e:
        print("[Migración Clientes]", e)

    # --- Migración: Agregar columnas faltantes si la tabla ya existía pero es vieja ---
    try:
        cursor.execute("PRAGMA table_info(Servicios);")
        cols = [c[1] for c in cursor.fetchall()]
        if "liquidacion_id" not in cols:
            cursor.execute("ALTER TABLE Servicios ADD COLUMN liquidacion_id INTEGER NULL;")
        if "cliente_id" not in cols:
            cursor.execute("ALTER TABLE Servicios ADD COLUMN cliente_id INTEGER NULL;")
        if "cliente_nombre" not in cols:
            cursor.execute("ALTER TABLE Servicios ADD COLUMN cliente_nombre TEXT NULL;")
        conn.commit()
    except Exception as e:
        print("[Migración Servicios Cols]", e)

    try:
        cursor.execute("PRAGMA table_info(Mensajeros);")
        cols = [c[1] for c in cursor.fetchall()]
        if "base_actual" not in cols:
            cursor.execute("ALTER TABLE Mensajeros ADD COLUMN base_actual REAL DEFAULT 0;")
            conn.commit()
    except Exception:
        pass

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

    # --- Migración: Quitar ON DELETE CASCADE de Liquidaciones y Servicios ---
    try:
        cursor.execute("PRAGMA foreign_key_list(Liquidaciones);")
        fks = cursor.fetchall()
        # Si tiene ON DELETE CASCADE, recreamos la tabla
        has_cascade = any(fk["on_delete"] == "CASCADE" for fk in fks)
        
        # También checamos si faltan las nuevas columnas de nombre/teléfono
        cursor.execute("PRAGMA table_info(Liquidaciones);")
        cols = [c[1] for c in cursor.fetchall()]
        has_new_cols = "mensajero_nombre" in cols

        if has_cascade or not has_new_cols:
            print("[Migración] Reenlazando Liquidaciones para evitar borrado en cascada...")
            # 1. Renombrar vieja
            cursor.execute("ALTER TABLE Liquidaciones RENAME TO Liquidaciones_old;")
            # 2. Crear nueva (con la definición actualizada en init_db pero aquí repetida por seguridad)
            cursor.execute("""
                CREATE TABLE Liquidaciones (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    mensajero_id        INTEGER,
                    mensajero_nombre    TEXT,
                    mensajero_telefono  TEXT,
                    fecha               TEXT    NOT NULL,
                    subtotal_servicios  REAL    NOT NULL,
                    comision_empresa    REAL    NOT NULL,
                    descuento_aseo      REAL    NOT NULL DEFAULT 1000,
                    base_prestada       REAL    NOT NULL DEFAULT 0,
                    neto_mensajero      REAL    NOT NULL,
                    FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE SET NULL
                );
            """)
            # 3. Copiar datos e intentar traer nombres de Mensajeros si existen
            cursor.execute("""
                INSERT INTO Liquidaciones (
                    id, mensajero_id, fecha, subtotal_servicios, 
                    comision_empresa, descuento_aseo, base_prestada, neto_mensajero,
                    mensajero_nombre, mensajero_telefono
                )
                SELECT 
                    L.id, L.mensajero_id, L.fecha, L.subtotal_servicios, 
                    L.comision_empresa, L.descuento_aseo, L.base_prestada, L.neto_mensajero,
                    M.nombre, M.telefono
                FROM Liquidaciones_old L
                LEFT JOIN Mensajeros M ON L.mensajero_id = M.id;
            """)
            cursor.execute("DROP TABLE Liquidaciones_old;")
            conn.commit()

        # Lo mismo para Servicios
        cursor.execute("PRAGMA foreign_key_list(Servicios);")
        fks_s = cursor.fetchall()
        if any(fk["on_delete"] == "CASCADE" for fk in fks_s):
            print("[Migración] Reenlazando Servicios para evitar borrado en cascada...")
            cursor.execute("ALTER TABLE Servicios RENAME TO Servicios_old;")
            cursor.execute("""
                CREATE TABLE Servicios (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    mensajero_id    INTEGER,
                    valor           REAL    NOT NULL DEFAULT 5000,
                    fecha           TEXT    NOT NULL,
                    descripcion     TEXT    DEFAULT '',
                    liquidacion_id  INTEGER,
                    FOREIGN KEY (mensajero_id) REFERENCES Mensajeros(id) ON DELETE SET NULL
                );
            """)
            cursor.execute("INSERT INTO Servicios SELECT * FROM Servicios_old;")
            cursor.execute("DROP TABLE Servicios_old;")
            conn.commit()

    except Exception as e:
        print("[Migración Cascade]", e)

    # --- Configuración del sistema ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );
    """)

    # Inicializar contraseña por defecto si no existe
    cursor.execute("SELECT valor FROM Configuracion WHERE clave='password'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Configuracion (clave, valor) VALUES ('password', 'ya le llego')")

    conn.commit()
    conn.close()

# ── Password Management ──

def get_app_password() -> str:
    """Retorna la contraseña actual del sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM Configuracion WHERE clave='password'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "ya le llego"

def set_app_password(nueva_pass: str):
    """Actualiza la contraseña del sistema."""
    conn = get_connection()
    conn.execute("UPDATE Configuracion SET valor = ? WHERE clave = 'password'", (nueva_pass,))
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
    return nuevo_id if nuevo_id is not None else 0


def obtener_mensajeros(busqueda: str = "") -> list[dict]:
    conn = get_connection()
    query = """
        SELECT M.*, 
               (SELECT COUNT(*) FROM Servicios WHERE mensajero_id = M.id AND liquidacion_id IS NULL) as servicios_pendientes
        FROM Mensajeros M
    """
    params = []
    if busqueda:
        query += " WHERE M.nombre LIKE ? OR M.telefono LIKE ?"
        params = [f"%{busqueda}%", f"%{busqueda}%"]
    
    query += " ORDER BY M.nombre"
    rows = conn.execute(query, params).fetchall()
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

def crear_servicio(mensajero_id: int, valor: float = 5000, descripcion: str = "", cliente_id: int = None, cliente_nombre: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Si no se pasó cliente_id pero sí cliente_nombre, intentar buscarlo
    if cliente_nombre and not cliente_id:
        c = cursor.execute("SELECT id FROM Clientes WHERE nombre = ?", (cliente_nombre.strip(),)).fetchone()
        if c: cliente_id = c[0]

    cursor.execute(
        "INSERT INTO Servicios (mensajero_id, valor, fecha, descripcion, cliente_id, cliente_nombre) VALUES (?, ?, ?, ?, ?, ?)",
        (mensajero_id, valor, fecha, descripcion, cliente_id, cliente_nombre)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id if nuevo_id is not None else 0

def actualizar_servicio_completo(id_servicio: int, valor: float, descripcion: str, cliente_id: int = None, cliente_nombre: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if cliente_nombre and not cliente_id:
        c = cursor.execute("SELECT id FROM Clientes WHERE nombre = ?", (cliente_nombre.strip(),)).fetchone()
        if c: cliente_id = c[0]

    cursor.execute(
        "UPDATE Servicios SET valor=?, descripcion=?, cliente_id=?, cliente_nombre=? WHERE id=?", 
        (valor, descripcion, cliente_id, cliente_nombre, id_servicio)
    )
    conn.commit()
    conn.close()


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

def actualizar_descripcion_servicio(id_servicio: int, descripcion: str):
    conn = get_connection()
    conn.execute(
        "UPDATE Servicios SET descripcion=? WHERE id=?", 
        (descripcion, id_servicio)
    )
    conn.commit()
    conn.close()


def eliminar_servicio(id_servicio: int):
    conn = get_connection()
    conn.execute("DELETE FROM Servicios WHERE id=?", (id_servicio,))
    conn.commit()
    conn.close()


# ── Gastos ────────────────────────────────────────────────────────

def crear_gasto(descripcion: str, monto: float) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO Gastos (descripcion, monto, fecha) VALUES (?, ?, ?)",
        (descripcion, monto, fecha)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id if nuevo_id is not None else 0


def obtener_gastos(filtro: str = "todo") -> list[dict]:
    conn = get_connection()
    hoy = datetime.now()
    query = "SELECT * FROM Gastos"
    params = []

    if filtro == "hoy":
        query += " WHERE fecha LIKE ?"
        params.append(f"{hoy.strftime('%Y-%m-%d')}%")
    elif filtro == "semana":
        inicio_semana = (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")
        query += " WHERE fecha >= ?"
        params.append(inicio_semana)
    elif filtro == "mes":
        inicio_mes = hoy.strftime("%Y-%m-01")
        query += " WHERE fecha >= ?"
        params.append(inicio_mes)
    elif "-" in filtro and len(filtro) == 10: # Formato YYYY-MM-DD
        query += " WHERE fecha LIKE ?"
        params.append(f"{filtro}%")
    elif ".." in filtro: # Formato YYYY-MM-DD..YYYY-MM-DD
        inicio, fin = filtro.split("..")
        query += " WHERE fecha >= ? AND fecha <= ?"
        params.append(f"{inicio} 00:00:00")
        params.append(f"{fin} 23:59:59")

    query += " ORDER BY fecha DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def eliminar_gasto(id_gasto: int):
    conn = get_connection()
    conn.execute("DELETE FROM Gastos WHERE id=?", (id_gasto,))
    conn.commit()
    conn.close()



# ── Liquidaciones ─────

def eliminar_liquidacion(id_liquidacion: int):
    """
    Elimina una liquidación de la base de datos.
    Los servicios asociados conservan su liquidacion_id (no vuelven a quedar pendientes)
    pero al no existir ya el registro en la tabla Liquidaciones, ya no se contabilizan
    en los informes financieros.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Ya no se resetean los servicios a NULL
    cursor.execute("DELETE FROM Liquidaciones WHERE id = ?", (id_liquidacion,))
    conn.commit()
    conn.close()

def obtener_servicios_por_liquidacion(id_liquidacion: int) -> list[dict]:
    """Obtiene los servicios asociados a una liquidación específica."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM Servicios WHERE liquidacion_id=? ORDER BY fecha",
        (id_liquidacion,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def ejecutar_liquidacion(mensajero_id: int, base: float = 0, pendientes: list | None = None) -> dict | None:
    """
    Agrupa servicios pendientes, descuenta base y registra la liquidación.
    """
    if pendientes is None:
        pendientes = obtener_servicios_pendientes(mensajero_id)
        
    if not pendientes:
        return None

    subtotal = sum(s["valor"] for s in pendientes)
    comision = subtotal * 0.20
    # El neto es la ganancia por el trabajo (80%)
    neto = subtotal * 0.80
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener datos actuales del mensajero para persistencia
    mensajero = conn.execute("SELECT nombre, telefono FROM Mensajeros WHERE id=?", (mensajero_id,)).fetchone()
    m_nombre = mensajero["nombre"] if mensajero else "Mensajero Eliminado"
    m_telefono = mensajero["telefono"] if mensajero else ""

    # Registrar liquidación (la base se guarda por separado)
    # Aseo: mil por cada día único que contenga servicios
    dias_unicos = set(s["fecha"].split(" ")[0] for s in pendientes)
    aseo = len(dias_unicos) * 1000
    
    # El neto es el subtotal menos la comisión y el aseo
    neto = subtotal - comision - aseo
    
    cursor.execute("""
        INSERT INTO Liquidaciones (mensajero_id, mensajero_nombre, mensajero_telefono, fecha,
                                   subtotal_servicios, comision_empresa, descuento_aseo,
                                   base_prestada, neto_mensajero)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (mensajero_id, m_nombre, m_telefono, fecha, subtotal, comision, aseo, base, neto))
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
        "mensajero": m_nombre,
        "cantidad_servicios": len(pendientes),
        "subtotal": subtotal,
        "comision": comision,
        "descuento_aseo": aseo,
        "neto": neto,
        "fecha": fecha,
    }


def obtener_liquidaciones(filtro: str = "todo") -> list[dict]:
    """
    Devuelve liquidaciones filtradas. filtro: 'hoy', 'semana', 'mes', 'todo'.
    Ademas incluye el total de servicios como num_servicios.
    """
    conn = get_connection()
    hoy = datetime.now()

    query_base = """
        SELECT L.*, 
               COALESCE(L.mensajero_nombre, M.nombre) AS mensajero_nombre, 
               COALESCE(L.mensajero_telefono, M.telefono) AS mensajero_telefono,
               (SELECT COUNT(*) FROM Servicios WHERE liquidacion_id = L.id) AS num_servicios
        FROM Liquidaciones L
        LEFT JOIN Mensajeros M ON L.mensajero_id = M.id
    """

    if filtro == "hoy":
        fecha_inicio = hoy.strftime("%Y-%m-%d")
        query = query_base + " WHERE L.fecha LIKE ? GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query, (f"{fecha_inicio}%",)).fetchall()
    elif filtro == "semana":
        inicio_semana = (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")
        query = query_base + " WHERE L.fecha >= ? GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query, (inicio_semana,)).fetchall()
    elif filtro == "mes":
        inicio_mes = hoy.strftime("%Y-%m-01")
        query = query_base + " WHERE L.fecha >= ? GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query, (inicio_mes,)).fetchall()
    elif "-" in filtro and len(filtro) == 10: # Formato YYYY-MM-DD
        query = query_base + " WHERE L.fecha LIKE ? GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query, (f"{filtro}%",)).fetchall()
    elif ".." in filtro: # Formato YYYY-MM-DD..YYYY-MM-DD
        inicio, fin = filtro.split("..")
        query = query_base + " WHERE L.fecha >= ? AND L.fecha <= ? GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query, (f"{inicio} 00:00:00", f"{fin} 23:59:59")).fetchall()
    else:
        query = query_base + " GROUP BY L.id ORDER BY L.fecha DESC"
        rows = conn.execute(query).fetchall()

    conn.close()
    return [dict(row) for row in rows]
# ── Clientes ────────────────────────────────────────────────────────

def crear_cliente(nombre: str, direccion: str = "", telefono: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO Clientes (nombre, direccion, telefono, fecha_registro) VALUES (?, ?, ?, ?)",
            (nombre, direccion, telefono, fecha)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        nuevo_id = 0
    conn.close()
    return nuevo_id if nuevo_id is not None else 0

def obtener_clientes(busqueda: str = "", filtro: str = "todo") -> list[dict]:
    conn = get_connection()
    hoy = datetime.now()
    
    # Construir la condición de fecha para las subconsultas
    fecha_cond = ""
    f_params = []
    
    if filtro == "hoy":
        fecha_cond = " AND fecha LIKE ?"
        f_params.append(f"{hoy.strftime('%Y-%m-%d')}%")
    elif filtro == "semana":
        inicio_semana = (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")
        fecha_cond = " AND fecha >= ?"
        f_params.append(inicio_semana)
    elif filtro == "mes":
        inicio_mes = hoy.strftime("%Y-%m-01")
        fecha_cond = " AND fecha >= ?"
        f_params.append(inicio_mes)
    elif "-" in filtro and len(filtro) == 10: # YYYY-MM-DD
        fecha_cond = " AND fecha LIKE ?"
        f_params.append(f"{filtro}%")
    elif ".." in filtro: # YYYY-MM-DD..YYYY-MM-DD
        inicio, fin = filtro.split("..")
        fecha_cond = " AND fecha >= ? AND fecha <= ?"
        f_params.append(f"{inicio} 00:00:00")
        f_params.append(f"{fin} 23:59:59")

    query = f"""
        SELECT C.*, 
               (SELECT COUNT(*) FROM Servicios WHERE (cliente_id = C.id OR cliente_nombre = C.nombre) {fecha_cond}) as total_servicios,
               (SELECT MAX(fecha) FROM Servicios WHERE (cliente_id = C.id OR cliente_nombre = C.nombre) {fecha_cond}) as ultima_fecha
        FROM Clientes C
    """
    
    params = []
    # Usar los parámetros de fecha en ambas subconsultas (total_servicios y ultima_fecha)
    # Sin embargo, como están en el SELECT, debemos duplicar f_params para cada subconsulta
    full_params = f_params + f_params
    
    if busqueda:
        query += " WHERE C.nombre LIKE ? OR C.direccion LIKE ? OR C.telefono LIKE ?"
        full_params += [f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"]
    
    query += " ORDER BY C.nombre"
    rows = conn.execute(query, full_params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def actualizar_cliente(id_: int, nombre: str, direccion: str, telefono: str):
    conn = get_connection()
    conn.execute("UPDATE Clientes SET nombre=?, direccion=?, telefono=? WHERE id=?", (nombre, direccion, telefono, id_))
    conn.commit()
    conn.close()

def eliminar_cliente(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM Clientes WHERE id=?", (id_,))
    conn.commit()
    conn.close()

def sugerir_clientes(busqueda: str) -> list[str]:
    """Retorna una lista de nombres de clientes que coincidan con el inicio de la búsqueda."""
    if not busqueda: return []
    conn = get_connection()
    rows = conn.execute(
        "SELECT nombre FROM Clientes WHERE nombre LIKE ? LIMIT 5",
        (f"{busqueda}%",)
    ).fetchall()
    conn.close()
    return [r["nombre"] for r in rows]


# ── Turnero ─────────────────────────────────────────────────────────

def registrar_en_turno(mensajero_id: int):
    """Agrega un mensajero al final de la cola del turnero."""
    conn = get_connection()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO Turnero (mensajero_id, fecha_entrada) VALUES (?, ?)",
            (mensajero_id, fecha)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Ya está en turno, actualizar fecha para mover al final si se desea, 
        # o simplemente ignorar. Aquí lo ignoramos porque el usuario dice "se van registrando".
        pass
    conn.close()

def obtener_cola_turnos() -> list[dict]:
    """Obtiene la lista de mensajeros en el turnero ordenados por llegada."""
    conn = get_connection()
    query = """
        SELECT T.*, M.nombre, M.telefono
        FROM Turnero T
        JOIN Mensajeros M ON T.mensajero_id = M.id
        ORDER BY T.fecha_entrada ASC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def quitar_de_turno(mensajero_id: int):
    """Elimina un mensajero de la cola."""
    conn = get_connection()
    conn.execute("DELETE FROM Turnero WHERE mensajero_id = ?", (mensajero_id,))
    conn.commit()
    conn.close()

def avanzar_turno(mensajero_id: int):
    """Mueve al mensajero al final de la cola (actualiza su fecha de entrada)."""
    conn = get_connection()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE Turnero SET fecha_entrada = ? WHERE mensajero_id = ?",
        (fecha, mensajero_id)
    )
    conn.commit()
    conn.close()

def obtener_siguiente_en_turno() -> dict | None:
    """Retorna el primer mensajero en la cola."""
    conn = get_connection()
    query = """
        SELECT T.*, M.nombre, M.telefono
        FROM Turnero T
        JOIN Mensajeros M ON T.mensajero_id = M.id
        ORDER BY T.fecha_entrada ASC
        LIMIT 1
    """
    row = conn.execute(query).fetchone()
    conn.close()
    return dict(row) if row else None

def limpiar_turnero():
    """Vacía toda la cola."""
    conn = get_connection()
    conn.execute("DELETE FROM Turnero")
    conn.commit()
    conn.close()
