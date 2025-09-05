import sqlite3
from datetime import datetime, timedelta
import bcrypt

conexion = None

def conectar(ruta="gimnasio.db"):
    global conexion
    if conexion is None:
        conexion = sqlite3.connect(ruta)
        conexion.row_factory = sqlite3.Row  # importante para acceso por nombre
    return conexion

# ------------------ Credenciales ------------------
def crear_tabla_credenciales():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS credenciales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            rol TEXT DEFAULT 'admin',
            creado_en TEXT DEFAULT (DATE('now'))
        )
    """)
    conn.commit()

def crear_usuario(username: str, password_plano: str, rol: str = "admin"):
    conn = conectar()
    pw_hash = bcrypt.hashpw(password_plano.encode("utf-8"), bcrypt.gensalt())
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO credenciales (username, password_hash, rol) VALUES (?, ?, ?)",
        (username, pw_hash, rol)
    )
    conn.commit()

def verificar_credenciales(username: str, password_plano: str) -> bool:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM credenciales WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        return False
    try:
        return bcrypt.checkpw(password_plano.encode("utf-8"), row["password_hash"])
    except Exception:
        return False

def contar_usuarios_login() -> int:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM credenciales")
    (n,) = cur.fetchone()
    return int(n)

# ------------------ Usuarios ------------------
def crear_tabla_usuarios():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            telefono TEXT,
            membresia TEXT,
            fecha_registro TEXT,
            fecha_vencimiento TEXT
        )
    """)
    conn.commit()

def agregar_usuario(nombre, apellido, telefono, membresia):
    conn = conectar()
    fecha_registro = datetime.now().strftime("%Y-%m-%d")
    dias_membresia = {"mensual": 30, "trimestral": 90}.get(membresia.lower(), 365)
    fecha_vencimiento = (datetime.now() + timedelta(days=dias_membresia)).strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuarios (nombre, apellido, telefono, membresia, fecha_registro, fecha_vencimiento)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, apellido, telefono, membresia, fecha_registro, fecha_vencimiento))
    conn.commit()
    return cur.lastrowid

def obtener_usuarios():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, apellido, telefono, membresia, fecha_registro, fecha_vencimiento
        FROM usuarios
    """)
    return cur.fetchall()

def obtener_usuario(id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, apellido, telefono, membresia, fecha_registro, fecha_vencimiento
        FROM usuarios WHERE id = ?
    """, (id,))
    return cur.fetchone()

def actualizar_usuario(id, nombre, apellido, telefono, membresia):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE usuarios
        SET nombre = ?, apellido = ?, telefono = ?, membresia = ?
        WHERE id = ?
    """, (nombre, apellido, telefono, membresia, id))
    conn.commit()

def eliminar_usuario(id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
