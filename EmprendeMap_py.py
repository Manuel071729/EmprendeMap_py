"""
EMPRENDEMAP — App v7  +  SQLite persistence
Flujo: Splash → Login/Registro → Home → Planes ←→ Perfil
                                       ↓
                                  Detalle de Local
Base de datos: emprendemap.db  (SQLite, se crea automáticamente)
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from pathlib import Path

# ── SQLite (incluido en Python, sin instalar nada extra) ──────────────
import sqlite3
import hashlib
import secrets
from datetime import date, timedelta
import urllib.request
import urllib.error
import json
import threading
import shutil
import base64
import io

BASE_DIR  = Path(__file__).parent
LOGO_PATH = BASE_DIR / "splash_logo.jpg"
DB_PATH   = BASE_DIR / "emprendemap.db"

# ── Color palette ────────────────────────────────────────────────────
C_ORANGE      = "#E8590A"
C_ORANGE_DARK = "#C44D07"
C_YELLOW      = "#FFF3B0"
C_YELLOW_DEEP = "#FFE566"
C_BG_PLANS    = "#FDF0D5"
C_CARD_WHITE  = "#FFFFFF"
C_CREAM_CARD  = "#FFFDF5"
C_PREM_CARD   = "#FFF4E6"
C_GREEN_SAVE  = "#2E7D32"
C_BTN_DARK    = "#222222"
C_BTN_BASIC   = "#C44D07"
C_BTN_PREM    = "#7B2D00"
C_WHITE       = "#FFFFFF"
C_TEXT_DARK   = "#1A1A1A"
C_TEXT_MID    = "#555555"
C_TEXT_SOFT   = "#999999"
C_INPUT_BG    = "#FFFFFF"
C_HEADER_BAR  = "#E8590A"
C_LINK        = "#C44D07"

# ── Plan data ─────────────────────────────────────────────────────────
OWNERS_PLANS = [
    {
        "badge": "PLAN BASE", "name": "FREE",
        "monthly": "$0.00", "yearly": "$0.00", "saving": "$0.00",
        "bg": C_CREAM_CARD,
        "features": [
            ("📍", "Mapa interactivo"),
            ("📊", "Analíticas Básicas"),
            ("📷", "5 Fotos"),
        ],
    },
    {
        "badge": "PLAN PREMIUM", "name": "PRO-MARKET",
        "monthly": "$14.99", "yearly": "$149.99", "saving": "$29.89",
        "bg": C_PREM_CARD,
        "features": [
            ("🔍", "Primeros en Búsqueda"),
            ("✅", "Insignia 'Verificado'"),
            ("🎬", "Video / Recorrido 360°"),
            ("⭐", "Recomendación Activa"),
        ],
    },
]

ENTREPRENEURS_PLANS = [
    {
        "badge": "PLAN SCOUT", "name": "Normal",
        "monthly": "$0.00", "yearly": "$0.00", "saving": "$0.00",
        "bg": C_CREAM_CARD,
        "features": [
            ("✉️", "Alertas de correo"),
            ("🔽", "Filtros avanzados"),
            ("♥",  "Comparar favoritos"),
            ("🎧", "Soporte"),
        ],
    },
    {
        "badge": "PLAN EXPLORADOR", "name": "PREMIUM",
        "monthly": "$19.99", "yearly": "$199.99", "saving": "$40.00",
        "bg": C_PREM_CARD,
        "features": [
            ("⚡", "Acceso anticipado"),
            ("📞", "Contacto en un clic"),
            ("📋", "Checklist legal"),
            ("💬", "Soporte prioritario"),
        ],
    },
]

# ── Available listings data (seed) ────────────────────────────────────
_LOCALES_SEED = [
    {
        "nombre": "Local Comercial Centro",
        "tipo": "Renta", "precio": "$450", "periodo": "mes",
        "zona": "Centro Histórico, San Salvador", "m2": "85 m²",
        "rating": "4.8", "verificado": 1, "emoji": "🏪",
        "desc": (
            "Local amplio en el corazón del Centro Histórico. "
            "Ideal para tienda, restaurante o cafetería. "
            "Excelente flujo peatonal, acceso fácil y estacionamiento cercano."
        ),
        "contacto": "+503 7000-1234", "tipo_detalle": "Local Comercial",
        "features": [
            ("📐", "85 m² de área total"), ("🚿", "2 baños incluidos"),
            ("❄️", "Aire acondicionado"),  ("🔌", "Instalación trifásica"),
            ("🅿️", "Estacionamiento cercano"), ("📡", "Fibra óptica disponible"),
        ],
    },
    {
        "nombre": "Bodega Industrial Norte",
        "tipo": "Renta", "precio": "$820", "periodo": "mes",
        "zona": "Zona Industrial, Soyapango", "m2": "240 m²",
        "rating": "4.5", "verificado": 1, "emoji": "🏭",
        "desc": (
            "Bodega con acceso para camiones de carga, rampa de descarga, "
            "oficina administrativa integrada y sistema de seguridad 24/7. "
            "Perfecta para distribuidoras y manufactura."
        ),
        "contacto": "+503 7000-5678", "tipo_detalle": "Bodega",
        "features": [
            ("📐", "240 m² de área total"), ("🚚", "Acceso para camiones"),
            ("🔒", "Seguridad 24/7"),       ("💡", "Alta tensión disponible"),
            ("🏢", "Oficina integrada 20 m²"), ("🌡️", "Ventilación industrial"),
        ],
    },
    {
        "nombre": "Oficina Premium Escalón",
        "tipo": "Renta", "precio": "$650", "periodo": "mes",
        "zona": "Colonia Escalón, San Salvador", "m2": "60 m²",
        "rating": "4.9", "verificado": 1, "emoji": "🏢",
        "desc": (
            "Oficina ejecutiva en edificio corporativo con lobby, recepción compartida, "
            "sala de reuniones disponible y vista panorámica de la ciudad. "
            "Ideal para startups y profesionales independientes."
        ),
        "contacto": "+503 7000-9012", "tipo_detalle": "Oficina",
        "features": [
            ("📐", "60 m² privados"),    ("🤝", "Sala de reuniones"),
            ("☕", "Área de café compartida"), ("📡", "Internet 500 Mbps"),
            ("🅿️", "2 parqueos incluidos"), ("🔐", "Acceso con tarjeta"),
        ],
    },
    {
        "nombre": "Kiosco Plaza Merliot",
        "tipo": "Venta", "precio": "$28,000", "periodo": "único",
        "zona": "Plaza Merliot, Santa Tecla", "m2": "12 m²",
        "rating": "4.6", "verificado": 0, "emoji": "🏬",
        "desc": (
            "Kiosco en zona de alto tráfico dentro de plaza comercial. "
            "Incluye vitrinas, iluminación LED y conexión eléctrica. "
            "Ideal para joyería, accesorios, comida rápida o tecnología."
        ),
        "contacto": "+503 7000-3456", "tipo_detalle": "Kiosco / Stand",
        "features": [
            ("📐", "12 m² estratégicos"), ("💡", "Iluminación LED"),
            ("🛒", "Alto tráfico peatonal"), ("🔧", "Vitrina incluida"),
            ("📋", "Documentos en regla"), ("🏪", "Vecinos comerciales"),
        ],
    },
    {
        "nombre": "Restaurante Equipado Zona Rosa",
        "tipo": "Renta", "precio": "$1,200", "periodo": "mes",
        "zona": "Zona Rosa, San Salvador", "m2": "120 m²",
        "rating": "4.7", "verificado": 1, "emoji": "🍽️",
        "desc": (
            "Local de restaurante completamente equipado con cocina industrial, "
            "campana extractora, refrigeración comercial y salón para 40 personas. "
            "Ubicado en la zona gastronómica más activa del país."
        ),
        "contacto": "+503 7000-7890", "tipo_detalle": "Restaurante",
        "features": [
            ("📐", "120 m² + terraza"), ("🍳", "Cocina industrial"),
            ("❄️", "Refrigeración comercial"), ("👥", "Capacidad 40 personas"),
            ("🌿", "Terraza exterior"),   ("🔥", "Gas natural conectado"),
        ],
    },
    {
        "nombre": "Stand Feria Agora Mall",
        "tipo": "Renta", "precio": "$180", "periodo": "mes",
        "zona": "Agora Mall, San Salvador", "m2": "6 m²",
        "rating": "4.4", "verificado": 1, "emoji": "🛍️",
        "desc": (
            "Stand modular en mall de alto tráfico. Perfecto para emprendedores "
            "que quieren tener presencia física sin costos de un local grande. "
            "Incluye mostrador, iluminación y acceso a WiFi del mall."
        ),
        "contacto": "+503 7000-2222", "tipo_detalle": "Stand / Módulo",
        "features": [
            ("📐", "6 m² modulares"), ("📶", "WiFi incluido"),
            ("💡", "Iluminación LED"),  ("🛒", "Alto tráfico"),
            ("🔧", "Mostrador incluido"), ("📅", "Contrato flexible"),
        ],
    },
]


# ═════════════════════════════════════════════════════════════════════
#  DATABASE LAYER  (SQLite — embedded directly in app.py)
# ═════════════════════════════════════════════════════════════════════

def _db_connect() -> sqlite3.Connection:
    """Connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _db_init() -> None:
    """
    Creates the 6 tables if they don't exist and inserts seed listings
    on first run. Call once in startup().
    """
    conn = _db_connect()
    cur = conn.cursor()

    # 1. users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password_h TEXT    NOT NULL,
            rol        TEXT    NOT NULL DEFAULT 'emprendedor',
            creado_en  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # 2. listings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT    NOT NULL,
            tipo           TEXT    NOT NULL,
            precio         TEXT    NOT NULL,
            periodo        TEXT    NOT NULL,
            zona           TEXT    NOT NULL,
            m2             TEXT    NOT NULL,
            rating         TEXT    NOT NULL DEFAULT '0.0',
            verificado     INTEGER NOT NULL DEFAULT 0,
            emoji          TEXT    NOT NULL DEFAULT '🏪',
            desc           TEXT    NOT NULL DEFAULT '',
            contacto       TEXT    NOT NULL DEFAULT '',
            tipo_detalle   TEXT    NOT NULL DEFAULT '',
            propietario_id INTEGER,
            creado_en      TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (propietario_id) REFERENCES usuarios(id)
        )
    """)

    # 3. features
    cur.execute("""
        CREATE TABLE IF NOT EXISTS caracteristicas (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            local_id INTEGER NOT NULL,
            icono    TEXT    NOT NULL,
            texto    TEXT    NOT NULL,
            FOREIGN KEY (local_id) REFERENCES locales(id) ON DELETE CASCADE
        )
    """)

    # 4. favorites
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL,
            local_id    INTEGER NOT NULL,
            guardado_en TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE (usuario_id, local_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (local_id)   REFERENCES locales(id)  ON DELETE CASCADE
        )
    """)

    # 5. contracted plans
    cur.execute("""
        CREATE TABLE IF NOT EXISTS planes_contratados (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id   INTEGER NOT NULL,
            badge        TEXT    NOT NULL,
            nombre_plan  TEXT    NOT NULL,
            precio_mes   TEXT    NOT NULL,
            precio_anio  TEXT    NOT NULL,
            grupo        TEXT    NOT NULL,
            periodo      TEXT    NOT NULL DEFAULT 'mensual',
            fecha_inicio TEXT    NOT NULL DEFAULT (date('now')),
            fecha_vence  TEXT,
            pagado       INTEGER NOT NULL DEFAULT 0,
            activo       INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    # 6. sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            token      TEXT    NOT NULL,
            creado_en  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    # 7. activity log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS actividad (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL,
            tipo        TEXT    NOT NULL,
            descripcion TEXT    NOT NULL,
            fecha       TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed listings (only if table is empty)
    if cur.execute("SELECT COUNT(*) FROM locales").fetchone()[0] == 0:
        for local in _LOCALES_SEED:
            cur.execute("""
                INSERT INTO locales
                    (nombre, tipo, precio, periodo, zona, m2, rating,
                     verificado, emoji, desc, contacto, tipo_detalle)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                local["nombre"], local["tipo"], local["precio"], local["periodo"],
                local["zona"], local["m2"], local["rating"], local["verificado"],
                local["emoji"], local["desc"], local["contacto"], local["tipo_detalle"],
            ))
            lid = cur.lastrowid
            for (ico, txt) in local["features"]:
                cur.execute(
                    "INSERT INTO caracteristicas (local_id, icono, texto) VALUES (?,?,?)",
                    (lid, ico, txt),
                )
        conn.commit()

    # Migration: add foto_perfil column if not exists
    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil BLOB")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN foto_offset_x INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE usuarios ADD COLUMN foto_offset_y INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Sanitize old long activity descriptions
    try:
        cur.execute("""
            UPDATE actividad
            SET descripcion = substr(descripcion, 1, 20) || '…'
            WHERE length(descripcion) > 20
        """)
        conn.commit()
    except Exception:
        pass

    conn.close()


def _db_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _db_row_to_local(row: sqlite3.Row, feats) -> dict:
    return {
        "id":           row["id"],
        "nombre":       row["nombre"],
        "tipo":         row["tipo"],
        "precio":       row["precio"],
        "periodo":      row["periodo"],
        "zona":         row["zona"],
        "m2":           row["m2"],
        "rating":       row["rating"],
        "verificado":   bool(row["verificado"]),
        "emoji":        row["emoji"],
        "desc":         row["desc"],
        "contacto":     row["contacto"],
        "tipo_detalle": row["tipo_detalle"],
        "features":     [(f["icono"], f["texto"]) for f in feats],
    }


# ── users ─────────────────────────────────────────────────────────────

def _db_registrar_usuario(nombre, email, password, rol):
    try:
        conn = _db_connect()
        conn.execute(
            "INSERT INTO usuarios (nombre, email, password_h, rol) VALUES (?,?,?,?)",
            (nombre, email, _db_hash(password), rol),
        )
        conn.commit()
        conn.close()
        return _db_login_usuario(email, password)
    except sqlite3.IntegrityError:
        return None


def _db_login_usuario(email, password):
    conn = _db_connect()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE email=? AND password_h=?",
        (email, _db_hash(password)),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "nombre": row["nombre"],
            "email": row["email"], "rol": row["rol"]}


# ── listings ──────────────────────────────────────────────────────────

def _db_get_locales():
    """Returns all listings with their features."""
    conn = _db_connect()
    rows = conn.execute("SELECT * FROM locales ORDER BY id").fetchall()
    result = []
    for row in rows:
        feats = conn.execute(
            "SELECT * FROM caracteristicas WHERE local_id=? ORDER BY id",
            (row["id"],),
        ).fetchall()
        result.append(_db_row_to_local(row, feats))
    conn.close()
    return result


def _db_get_locales_propietario(propietario_id):
    """Returns only the listings published by the given owner."""
    conn = _db_connect()
    rows = conn.execute(
        "SELECT * FROM locales WHERE propietario_id=? ORDER BY id DESC",
        (propietario_id,),
    ).fetchall()
    result = []
    for row in rows:
        feats = conn.execute(
            "SELECT * FROM caracteristicas WHERE local_id=? ORDER BY id",
            (row["id"],),
        ).fetchall()
        result.append(_db_row_to_local(row, feats))
    conn.close()
    return result


def _db_publicar_local(propietario_id, nombre, tipo, tipo_detalle,
                       precio, periodo, zona, m2, emoji, desc, contacto):
    """Inserts a new listing and returns its id."""
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO locales
            (propietario_id, nombre, tipo, tipo_detalle, precio, periodo,
             zona, m2, emoji, desc, contacto, verificado)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,0)
    """, (propietario_id, nombre, tipo, tipo_detalle, precio, periodo,
          zona, m2, emoji, desc, contacto))
    conn.commit()
    local_id = cur.lastrowid
    conn.close()
    return local_id


def _db_cambiar_rol(usuario_id, nuevo_rol):
    """Updates the user's role in the DB."""
    conn = _db_connect()
    conn.execute("UPDATE usuarios SET rol=? WHERE id=?", (nuevo_rol, usuario_id))
    conn.commit()
    conn.close()


# ── favorites ─────────────────────────────────────────────────────────

def _db_get_favoritos(usuario_id):
    conn = _db_connect()
    rows = conn.execute("""
        SELECT l.* FROM locales l
        JOIN favoritos f ON f.local_id = l.id
        WHERE f.usuario_id=?
        ORDER BY f.guardado_en DESC
    """, (usuario_id,)).fetchall()
    result = []
    for row in rows:
        feats = conn.execute(
            "SELECT * FROM caracteristicas WHERE local_id=? ORDER BY id",
            (row["id"],),
        ).fetchall()
        result.append(_db_row_to_local(row, feats))
    conn.close()
    return result


def _db_toggle_favorito(usuario_id, local_id):
    """Returns True if saved, False if removed."""
    conn = _db_connect()
    existe = conn.execute(
        "SELECT id FROM favoritos WHERE usuario_id=? AND local_id=?",
        (usuario_id, local_id),
    ).fetchone()
    if existe:
        conn.execute(
            "DELETE FROM favoritos WHERE usuario_id=? AND local_id=?",
            (usuario_id, local_id),
        )
        conn.commit(); conn.close()
        return False
    else:
        conn.execute(
            "INSERT INTO favoritos (usuario_id, local_id) VALUES (?,?)",
            (usuario_id, local_id),
        )
        conn.commit(); conn.close()
        return True


def _db_eliminar_favorito(usuario_id, local_id):
    conn = _db_connect()
    conn.execute(
        "DELETE FROM favoritos WHERE usuario_id=? AND local_id=?",
        (usuario_id, local_id),
    )
    conn.commit(); conn.close()


def _db_limpiar_favoritos(usuario_id):
    conn = _db_connect()
    conn.execute("DELETE FROM favoritos WHERE usuario_id=?", (usuario_id,))
    conn.commit(); conn.close()


# ── plans ─────────────────────────────────────────────────────────────

def _db_contratar_plan(usuario_id, badge, nombre_plan, precio_mes, precio_anio, grupo):
    fecha_inicio = date.today().isoformat()
    fecha_vence  = (date.today() + timedelta(days=30)).isoformat()
    conn = _db_connect()
    conn.execute(
        "UPDATE planes_contratados SET activo=0 WHERE usuario_id=?",
        (usuario_id,),
    )
    conn.execute("""
        INSERT INTO planes_contratados
            (usuario_id, badge, nombre_plan, precio_mes, precio_anio,
             grupo, fecha_inicio, fecha_vence, activo)
        VALUES (?,?,?,?,?,?,?,?,1)
    """, (usuario_id, badge, nombre_plan, precio_mes, precio_anio,
          grupo, fecha_inicio, fecha_vence))
    conn.commit(); conn.close()


def _db_get_plan_activo(usuario_id, grupo=None):
    conn = _db_connect()
    if grupo:
        row = conn.execute("""
            SELECT * FROM planes_contratados
            WHERE usuario_id=? AND activo=1 AND grupo=?
            ORDER BY id DESC LIMIT 1
        """, (usuario_id, grupo)).fetchone()
    else:
        row = conn.execute("""
            SELECT * FROM planes_contratados
            WHERE usuario_id=? AND activo=1
            ORDER BY id DESC LIMIT 1
        """, (usuario_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "label":       f"{row['badge']} — {row['nombre_plan']} ({row['precio_mes']}/mes)",
        "badge":       row["badge"],
        "nombre_plan": row["nombre_plan"],
        "precio_mes":  row["precio_mes"],
        "fecha_vence": row["fecha_vence"],
        "grupo":       row["grupo"],
    }


# ── sessions ──────────────────────────────────────────────────────────

def _db_guardar_sesion(usuario_id):
    token = secrets.token_hex(32)
    conn = _db_connect()
    conn.execute("""
        INSERT INTO sesiones (usuario_id, token)
        VALUES (?,?)
        ON CONFLICT(usuario_id) DO UPDATE SET token=excluded.token,
                                              creado_en=datetime('now')
    """, (usuario_id, token))
    conn.commit(); conn.close()


def _db_restaurar_sesion():
    conn = _db_connect()
    row = conn.execute("""
        SELECT u.* FROM usuarios u
        JOIN sesiones s ON s.usuario_id = u.id
        ORDER BY s.creado_en DESC LIMIT 1
    """).fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "nombre": row["nombre"],
            "email": row["email"], "rol": row["rol"]}


def _db_cerrar_sesion(usuario_id):
    conn = _db_connect()
    conn.execute("DELETE FROM sesiones WHERE usuario_id=?", (usuario_id,))
    conn.commit(); conn.close()


# ── profile photo ─────────────────────────────────────────────────────

def _db_guardar_foto(usuario_id, blob_bytes):
    conn = _db_connect()
    conn.execute(
        "UPDATE usuarios SET foto_perfil=? WHERE id=?",
        (blob_bytes, usuario_id),
    )
    conn.commit(); conn.close()


def _db_guardar_foto_con_offset(usuario_id, blob_bytes, offset_x, offset_y):
    conn = _db_connect()
    conn.execute(
        "UPDATE usuarios SET foto_perfil=?, foto_offset_x=?, foto_offset_y=? WHERE id=?",
        (blob_bytes, int(offset_x), int(offset_y), usuario_id),
    )
    conn.commit(); conn.close()


def _db_guardar_offset(usuario_id, offset_x, offset_y):
    conn = _db_connect()
    conn.execute(
        "UPDATE usuarios SET foto_offset_x=?, foto_offset_y=? WHERE id=?",
        (int(offset_x), int(offset_y), usuario_id),
    )
    conn.commit(); conn.close()


def _db_get_foto(usuario_id):
    """Returns (bytes_foto, offset_x, offset_y) or (None, 0, 0)."""
    conn = _db_connect()
    row = conn.execute(
        "SELECT foto_perfil, foto_offset_x, foto_offset_y FROM usuarios WHERE id=?",
        (usuario_id,),
    ).fetchone()
    conn.close()
    if row is None or row["foto_perfil"] is None:
        return None, 0, 0
    ox = row["foto_offset_x"] or 0
    oy = row["foto_offset_y"] or 0
    return bytes(row["foto_perfil"]), int(ox), int(oy)


def _make_circular_png(raw_bytes, offset_x=0, offset_y=0, size=200):
    """Generates a circular PNG from image bytes. Returns bytes or None."""
    try:
        from PIL import Image as PILImage, ImageDraw as PILDraw
        img  = PILImage.open(io.BytesIO(raw_bytes)).convert("RGBA")
        lado = min(img.width, img.height)
        cx   = img.width  // 2 + int(offset_x * lado / 200)
        cy   = img.height // 2 + int(offset_y * lado / 200)
        cx   = max(lado // 2, min(img.width  - lado // 2, cx))
        cy   = max(lado // 2, min(img.height - lado // 2, cy))
        left = cx - lado // 2
        top  = cy - lado // 2
        img  = img.crop((left, top, left + lado, top + lado))
        img  = img.resize((size, size), PILImage.LANCZOS)
        mask = PILImage.new("L", (size, size), 0)
        PILDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        result = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


# ── activity ──────────────────────────────────────────────────────────

def _db_registrar_actividad(usuario_id, tipo, descripcion):
    """Saves a user action. Keeps only the last 50 records."""
    if usuario_id is None:
        return
    conn = _db_connect()
    conn.execute(
        "INSERT INTO actividad (usuario_id, tipo, descripcion) VALUES (?,?,?)",
        (usuario_id, tipo, descripcion),
    )
    conn.execute("""
        DELETE FROM actividad WHERE usuario_id=? AND id NOT IN (
            SELECT id FROM actividad WHERE usuario_id=?
            ORDER BY id DESC LIMIT 50
        )
    """, (usuario_id, usuario_id))
    conn.commit(); conn.close()


def _db_get_stats_perfil(usuario_id):
    """
    Returns stats dict for the profile screen.
    Keys: listados, visitas_total, guardados, visitas_semana.
    """
    if usuario_id is None:
        return {
            "listados": 0, "visitas_total": 0,
            "guardados": 0, "visitas_semana": [0] * 7,
        }
    conn = _db_connect()

    listados = conn.execute(
        "SELECT COUNT(*) FROM locales WHERE propietario_id=?",
        (usuario_id,),
    ).fetchone()[0]

    visitas_total = conn.execute(
        "SELECT COUNT(*) FROM actividad WHERE usuario_id=? AND tipo='vista_detalle'",
        (usuario_id,),
    ).fetchone()[0]

    guardados = conn.execute(
        "SELECT COUNT(*) FROM favoritos WHERE usuario_id=?",
        (usuario_id,),
    ).fetchone()[0]

    # Visits by weekday (Mon=0 … Sun=6) for the current week
    from datetime import date, timedelta
    hoy   = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    visitas_semana = [0] * 7
    rows = conn.execute("""
        SELECT date(fecha) as dia, COUNT(*) as cnt
        FROM actividad
        WHERE usuario_id=? AND tipo='vista_detalle'
          AND date(fecha) >= ?
        GROUP BY dia
    """, (usuario_id, lunes.isoformat())).fetchall()
    for row in rows:
        try:
            from datetime import date as ddate
            d   = ddate.fromisoformat(row["dia"])
            idx = d.weekday()
            if 0 <= idx <= 6:
                visitas_semana[idx] = row["cnt"]
        except Exception:
            pass

    conn.close()
    return {
        "listados":       listados,
        "visitas_total":  visitas_total,
        "guardados":      guardados,
        "visitas_semana": visitas_semana,
    }


# ═════════════════════════════════════════════════════════════════════
class EmprendemapApp(toga.App):

    def startup(self):
        self.main_window = toga.MainWindow(title="EmprendeMap", resizable=True, size=(400, 780))

        # ── Initialize DB ─────────────────────────────────────────────
        _db_init()

        # ── In-memory user state ──────────────────────────────────────
        self._user_id    = None
        self._user_name  = "Usuario"
        self._user_email = ""
        self._user_rol   = "emprendedor"

        self._filtros          = set()
        self._ubicacion_actual = "Obteniendo ubicación..."

        # ── Attempt to restore saved session ─────────────────────────
        sesion = _db_restaurar_sesion()
        if sesion:
            self._user_id    = sesion["id"]
            self._user_name  = sesion["nombre"]
            self._user_email = sesion["email"]
            self._user_rol   = sesion["rol"]
            self.main_window.content = self._home()
        else:
            self.main_window.content = self._splash()

        self.main_window.show()

    # ── Property helpers that always read from DB ─────────────────────

    @property
    def _user_favs(self):
        """Current user's favorites, read from DB."""
        if self._user_id is None:
            return []
        return _db_get_favoritos(self._user_id)

    @property
    def _user_plan(self):
        """Active plan label for the current role, read from DB."""
        if self._user_id is None:
            return "Sin plan activo"
        grupo = "owners" if self._user_rol == "propietario" else "entrepreneurs"
        plan  = _db_get_plan_activo(self._user_id, grupo)
        return plan["label"] if plan else "Sin plan activo"

    def _set(self, screen):
        self.main_window.content = screen

    # ── UI Primitives ─────────────────────────────────────────────────

    def _page(self, bg=C_YELLOW):
        sc  = toga.ScrollContainer(horizontal=False)
        col = toga.Box(
            style=Pack(direction=COLUMN, background_color=bg, align_items=CENTER, flex=1)
        )
        sc.content = col
        return sc, col

    def _lbl(self, text, size=13, bold=False, color=C_TEXT_DARK, mt=0, mb=0):
        return toga.Label(
            text,
            style=Pack(font_size=size, font_weight="bold" if bold else "normal",
                       color=color, text_align=CENTER, margin_top=mt, margin_bottom=mb),
        )

    def _field(self, placeholder, password=False, width=300):
        cls = toga.PasswordInput if password else toga.TextInput
        return cls(
            placeholder=placeholder,
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=width),
        )

    def _field_group(self, label, placeholder, password=False, width=300):
        box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=14))
        box.add(self._lbl(label, size=12, color=C_TEXT_MID, mb=5))
        f = self._field(placeholder, password=password, width=width)
        box.add(f)
        return box, f

    def _btn_orange(self, text, handler, width=300):
        return toga.Button(
            text, on_press=handler,
            style=Pack(font_size=14, font_weight="bold", color=C_WHITE,
                       background_color=C_ORANGE, width=width, margin_top=4, margin_bottom=8),
        )

    def _btn_dark(self, text, handler, width=300):
        return toga.Button(
            text, on_press=handler,
            style=Pack(font_size=14, font_weight="bold", color=C_WHITE,
                       background_color=C_BTN_DARK, width=width, margin_bottom=8),
        )

    def _btn_white(self, text, handler, width=300):
        return toga.Button(
            text, on_press=handler,
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       background_color=C_WHITE, width=width, margin_bottom=8),
        )

    def _btn_link(self, text, handler):
        return toga.Button(
            text, on_press=handler,
            style=Pack(font_size=12, font_weight="bold", color=C_LINK, background_color=C_YELLOW),
        )

    def _or_sep(self):
        row = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                  margin_top=4, margin_bottom=4, width=300))
        row.add(toga.Box(style=Pack(height=1, flex=1, background_color="#CCCCCC", margin_right=10)))
        row.add(self._lbl("o", size=13, color=C_TEXT_SOFT))
        row.add(toga.Box(style=Pack(height=1, flex=1, background_color="#CCCCCC", margin_left=10)))
        return row

    def _spacer(self, h=20):
        return toga.Box(style=Pack(height=h))

    def _dots(self, active=0):
        row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        for i in range(3):
            c = C_ORANGE if i == active else C_TEXT_SOFT
            row.add(toga.Box(style=Pack(width=9, height=9, background_color=c, margin=5)))
        return row

    def _back_arrow(self, target_fn):
        return toga.Button(
            "←  Volver",
            on_press=lambda w: self._set(target_fn()),
            style=Pack(font_size=12, font_weight="bold", color=C_TEXT_DARK,
                       background_color=C_YELLOW, margin_top=14, margin_bottom=6),
        )

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 1 — SPLASH
    # ═══════════════════════════════════════════════════════════════
    def _splash(self):
        sc, col = self._page(bg=C_YELLOW)

        hero = toga.Box(style=Pack(direction=COLUMN, background_color=C_YELLOW_DEEP,
                                   align_items=CENTER, margin_bottom=0))
        if LOGO_PATH.exists():
            try:
                hero.add(toga.ImageView(
                    toga.Image(str(LOGO_PATH)),
                    style=Pack(width=300, height=190, margin_top=30, margin_bottom=8),
                ))
            except Exception:
                hero.add(self._splash_emoji())
        else:
            hero.add(self._splash_emoji())

        hero.add(toga.Box(style=Pack(height=5, background_color=C_ORANGE)))
        col.add(hero)

        col.add(self._spacer(28))
        col.add(self._lbl("¡Empecemos!", size=30, bold=True, color=C_TEXT_DARK))
        col.add(self._lbl("Todo comienza aquí", size=14, color=C_TEXT_MID, mt=4))
        col.add(self._spacer(12))
        col.add(self._lbl(
            "Conectamos propietarios de espacios\ncon emprendedores listos para crecer.",
            size=12, color=C_TEXT_MID, mt=0, mb=28,
        ))
        col.add(self._btn_orange("  Inicia sesión  ", lambda w: self._set(self._login())))
        col.add(self._btn_dark("  Crear cuenta  ", lambda w: self._set(self._register())))
        col.add(self._spacer(24))
        col.add(self._dots(active=0))
        col.add(self._spacer(16))
        col.add(self._lbl("v1.0.0  •  © 2026 EmprendeMap", size=10, color=C_TEXT_SOFT, mb=20))
        return sc

    def _splash_emoji(self):
        b = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=30))
        b.add(toga.Label("🏠", style=Pack(font_size=80, text_align=CENTER)))
        b.add(toga.Label("EmprendeMap",
                         style=Pack(font_size=22, font_weight="bold", color=C_ORANGE,
                                    text_align=CENTER, margin_top=8)))
        return b

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 2 — LOGIN
    # ═══════════════════════════════════════════════════════════════
    def _login(self):
        sc, col = self._page(bg=C_YELLOW)

        back_wrap = toga.Box(style=Pack(direction=ROW, width=320, margin_top=14, margin_bottom=6))
        back_wrap.add(self._back_arrow(self._splash))
        col.add(back_wrap)

        col.add(self._spacer(6))
        col.add(self._lbl("Bienvenido de nuevo", size=26, bold=True, color=C_TEXT_DARK))
        col.add(self._lbl("Ingresa tus credenciales para continuar",
                          size=13, color=C_TEXT_SOFT, mt=4, mb=28))

        email_grp, self._login_email = self._field_group("Correo electrónico", "Email o usuario")
        pass_grp,  self._login_pass  = self._field_group("Contraseña", "Contraseña", password=True)
        col.add(email_grp)
        col.add(pass_grp)

        col.add(self._lbl("¿Olvidaste tu contraseña?", size=12, color=C_LINK, mb=16))
        col.add(self._btn_orange("Inicia sesión", self._do_login))
        col.add(self._or_sep())
        col.add(self._btn_white("🌐  Continuar con Google", lambda w: self._social("Google")))
        col.add(self._spacer(16))

        link_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        link_row.add(self._lbl("¿No tienes una cuenta?  ", size=12, color=C_TEXT_MID))
        link_row.add(self._btn_link("Regístrate", lambda w: self._set(self._register())))
        col.add(link_row)
        col.add(self._spacer(10))
        col.add(self._dots(active=1))
        col.add(self._spacer(30))
        return sc

    def _do_login(self, w):
        email = self._login_email.value.strip()
        pwd   = self._login_pass.value.strip()
        if not email or not pwd:
            self.main_window.info_dialog("Campos requeridos", "Ingresa tu correo y contraseña.")
            return
        usuario = _db_login_usuario(email, pwd)
        if usuario is None:
            self.main_window.info_dialog(
                "Credenciales incorrectas",
                "El correo o la contraseña no son correctos.")
            return
        self._user_id    = usuario["id"]
        self._user_name  = usuario["nombre"]
        self._user_email = usuario["email"]
        self._user_rol   = usuario["rol"]
        _db_guardar_sesion(self._user_id)
        self._set(self._home())

    def _social(self, provider):
        self.main_window.info_dialog(
            f"Continuar con {provider}",
            f"Integración con {provider} disponible en producción.\nAccediendo como demo...",
        )
        self._set(self._home())

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 3 — REGISTER
    # ═══════════════════════════════════════════════════════════════
    def _register(self):
        sc, col = self._page(bg=C_YELLOW)

        back_wrap = toga.Box(style=Pack(direction=ROW, width=320, margin_top=14, margin_bottom=6))
        back_wrap.add(self._back_arrow(self._splash))
        col.add(back_wrap)

        col.add(self._spacer(6))
        col.add(self._lbl("Crear cuenta", size=26, bold=True, color=C_TEXT_DARK))
        col.add(self._lbl("Regístrate para comenzar",
                          size=13, color=C_TEXT_SOFT, mt=4, mb=28))

        name_grp,  self._reg_name  = self._field_group("Nombre completo", "Tu nombre")
        email_grp, self._reg_email = self._field_group("Correo electrónico", "Email")
        pass_grp,  self._reg_pass  = self._field_group("Contraseña", "Contraseña", password=True)
        conf_grp,  self._reg_conf  = self._field_group(
            "Confirmar contraseña", "Repite tu contraseña", password=True)

        col.add(name_grp)
        col.add(email_grp)
        col.add(pass_grp)
        col.add(conf_grp)

        # Centered role selector
        rol_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=18))
        rol_box.add(self._lbl("Soy un...", size=12, color=C_TEXT_MID, mb=6))
        self._rol = toga.Selection(
            items=["🏠  Propietario de espacio", "🤝  Emprendedor / Inquilino"],
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=300),
        )
        rol_box.add(self._rol)
        col.add(rol_box)

        col.add(self._btn_orange("Crear cuenta", self._do_register))
        col.add(self._or_sep())
        col.add(self._btn_white("🌐  Registrarse con Google", lambda w: self._social("Google")))
        col.add(self._spacer(16))

        link_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        link_row.add(self._lbl("¿Ya tienes cuenta?  ", size=12, color=C_TEXT_MID))
        link_row.add(self._btn_link("Inicia sesión", lambda w: self._set(self._login())))
        col.add(link_row)
        col.add(self._spacer(10))
        col.add(self._dots(active=2))
        col.add(self._spacer(30))
        return sc

    def _do_register(self, w):
        name = self._reg_name.value.strip()
        mail = self._reg_email.value.strip()
        pwd  = self._reg_pass.value.strip()
        conf = self._reg_conf.value.strip()
        if not all([name, mail, pwd, conf]):
            self.main_window.info_dialog("Campos requeridos", "Por favor completa todos los campos.")
            return
        if pwd != conf:
            self.main_window.info_dialog("Contraseñas no coinciden",
                                         "Las contraseñas ingresadas no son iguales.")
            return
        rol_text = str(self._rol.value or "")
        rol = "propietario" if "Propietario" in rol_text else "emprendedor"
        usuario = _db_registrar_usuario(name, mail, pwd, rol)
        if usuario is None:
            self.main_window.info_dialog(
                "Correo ya registrado",
                "Ya existe una cuenta con ese correo electrónico.")
            return
        self._user_id    = usuario["id"]
        self._user_name  = usuario["nombre"]
        self._user_email = usuario["email"]
        self._user_rol   = usuario["rol"]
        _db_guardar_sesion(self._user_id)
        self.main_window.info_dialog(
            "¡Bienvenido/a!",
            f"Cuenta creada como {rol}.\nHola, {name}! Exploremos los espacios.",
        )
        self._set(self._home())

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 4 — PLANS
    # ═══════════════════════════════════════════════════════════════
    def _plans(self):
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color=C_BG_PLANS, align_items=CENTER))

        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Home", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("Planes", style=Pack(font_size=14, font_weight="bold",
                                                color=C_WHITE, margin_left=8, flex=1)))
        bar.add(toga.Button("👤  Perfil", on_press=lambda w: self._set(self._profile()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        page.add(bar)

        es_propietario = self._user_rol == "propietario"
        titulo_rol  = "PROPIETARIOS" if es_propietario else "EMPRENDEDORES"
        icon_rol    = "🏠"           if es_propietario else "🤝"
        planes_rol  = OWNERS_PLANS   if es_propietario else ENTREPRENEURS_PLANS
        group_key   = "owners"       if es_propietario else "entrepreneurs"

        page.add(self._lbl(f"Planes para {titulo_rol}", size=14, bold=True,
                           color=C_ORANGE_DARK, mt=14, mb=4))
        page.add(self._lbl("💡  Pago anual = mayor ahorro", size=11, color=C_GREEN_SAVE, mb=14))

        cards_col = toga.Box(style=Pack(direction=COLUMN, margin_left=10, margin_right=10))
        cards_col.add(self._card(titulo_rol, icon_rol, planes_rol, group_key))
        page.add(cards_col)

        page.add(self._lbl("Cancela cuando quieras  •  Sin cargos ocultos",
                           size=10, color=C_TEXT_SOFT, mt=10, mb=16))
        sc.content = page
        return sc

    def _card(self, title, icon, plans, group_key):
        card = toga.Box(style=Pack(direction=COLUMN, background_color=C_CARD_WHITE))
        head = toga.Box(style=Pack(direction=COLUMN, background_color="#FFF0E0", align_items=CENTER))
        head.add(toga.Label(title, style=Pack(font_size=15, font_weight="bold",
                                              color=C_ORANGE_DARK, text_align=CENTER,
                                              margin_top=12, margin_bottom=4)))
        head.add(toga.Label(icon, style=Pack(font_size=36, text_align=CENTER, margin_bottom=8)))
        card.add(head)
        card.add(toga.Divider())
        for i, plan in enumerate(plans):
            card.add(self._plan(plan, group_key))
            if i < len(plans) - 1:
                card.add(toga.Divider())
        return card

    def _plan(self, plan, group_key):
        is_basic  = "BASIC" in plan["badge"] or "SCOUT" in plan["badge"] or "BÁSICO" in plan["name"]
        btn_color = C_BTN_BASIC if is_basic else C_BTN_PREM

        outer = toga.Box(style=Pack(direction=COLUMN, background_color=plan["bg"]))
        inner = toga.Box(style=Pack(direction=COLUMN, margin_top=12, margin_bottom=12,
                                    margin_left=14, margin_right=14))

        inner.add(toga.Label(plan["badge"],
                             style=Pack(font_size=11, font_weight="bold",
                                        color=btn_color, margin_bottom=2)))
        inner.add(toga.Label(plan["name"],
                             style=Pack(font_size=14, font_weight="bold",
                                        color=C_TEXT_DARK, margin_bottom=8)))

        rm = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=2))
        rm.add(toga.Label(plan["monthly"],
                          style=Pack(font_size=24, font_weight="bold", color=C_ORANGE)))
        rm.add(toga.Label(" / mes", style=Pack(font_size=11, color=C_TEXT_SOFT, margin_top=8)))
        inner.add(rm)

        ry = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=10))
        ry.add(toga.Label(plan["yearly"],
                          style=Pack(font_size=12, font_weight="bold", color=C_TEXT_DARK)))
        ry.add(toga.Label(" / año  —  ", style=Pack(font_size=11, color=C_TEXT_SOFT)))
        ry.add(toga.Label(f"Ahorras {plan['saving']}",
                          style=Pack(font_size=11, font_weight="bold", color=C_GREEN_SAVE)))
        inner.add(ry)
        inner.add(toga.Divider(style=Pack(margin_bottom=8)))

        for (ico, text) in plan["features"]:
            fr = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=4))
            fr.add(toga.Label(ico, style=Pack(font_size=12, margin_right=6)))
            fr.add(toga.Label(text, style=Pack(font_size=11, color=C_TEXT_MID, flex=1)))
            inner.add(fr)

        cta_label = "Elegir Plan Básico" if is_basic else "Elegir Plan Premium"

        def make_h(p=plan, g=group_key):
            def h(w): self._on_select(p, g)
            return h

        inner.add(toga.Button(cta_label, on_press=make_h(),
                              style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                         background_color=btn_color,
                                         margin_top=12, margin_bottom=4)))
        outer.add(inner)
        return outer

    def _on_select(self, plan, group_key):
        rol = "Propietario" if group_key == "owners" else "Emprendedor"
        if self._user_id is not None:
            _db_contratar_plan(self._user_id, plan["badge"], plan["name"],
                               plan["monthly"], plan["yearly"], group_key)
            _db_registrar_actividad(self._user_id, "plan",
                                    f"Contrataste el {plan['badge']}")
        self.main_window.info_dialog(
            title=f"Plan seleccionado — {rol}",
            message=(
                f"Elegiste el {plan['badge']} ({plan['name']})\n\n"
                f"  Mensual : {plan['monthly']} / mes\n"
                f"  Anual   : {plan['yearly']} / año\n"
                f"  Ahorras : {plan['saving']} al año\n\n"
                "Serás redirigido al proceso de pago."
            ),
        )

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 5 — USER PROFILE
    # ═══════════════════════════════════════════════════════════════
    def _profile(self):
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color="#FFF8F0", flex=1))

        # ── Top bar ────────────────────────────────────────────────
        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Home", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("Mi Perfil", style=Pack(font_size=14, font_weight="bold",
                                                    color=C_WHITE, margin_left=8, flex=1)))
        page.add(bar)

        # ── Identity card ──────────────────────────────────────────
        id_card = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                       align_items=CENTER, margin_top=10, margin_bottom=8))

        avatar_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                          background_color="#FFE0CC",
                                          margin_top=14, margin_bottom=8))
        rol_icon = "🏠" if self._user_rol == "propietario" else "🤝"

        # ── Circular profile photo ────────────────────────────────
        foto_bytes, off_x, off_y = _db_get_foto(self._user_id) if self._user_id else (None, 0, 0)

        if foto_bytes:
            try:
                circular = _make_circular_png(foto_bytes, off_x, off_y, size=200)
                src      = circular if circular else foto_bytes
                avatar_box.add(toga.ImageView(
                    toga.Image(data=src),
                    style=Pack(width=100, height=100, margin_top=14, margin_bottom=4),
                ))
            except Exception:
                avatar_box.add(toga.Label(rol_icon,
                    style=Pack(font_size=54, text_align=CENTER, margin_top=14, margin_bottom=4)))
        else:
            avatar_box.add(toga.Label(rol_icon,
                style=Pack(font_size=54, text_align=CENTER, margin_top=14, margin_bottom=4)))

        avatar_box.add(toga.Button(
            "✏️  Editar foto de perfil",
            on_press=lambda w: self._set(self._edit_avatar()),
            style=Pack(font_size=10, font_weight="bold", color=C_ORANGE_DARK,
                       background_color="#FFE8D6", margin_top=6, margin_bottom=6),
        ))

        # ── Role toggle button ────────────────────────────────────
        rol_actual  = self._user_rol
        rol_opuesto = "emprendedor" if rol_actual == "propietario" else "propietario"
        btn_texto   = "Propietario" if rol_actual == "propietario" else "Emprendedor"

        def _cambiar_rol(w):
            if self._user_id is not None:
                _db_cambiar_rol(self._user_id, rol_opuesto)
            self._user_rol = rol_opuesto
            self._set(self._profile())

        avatar_box.add(toga.Button(
            btn_texto, on_press=_cambiar_rol,
            style=Pack(font_size=11, font_weight="bold", color=C_WHITE,
                       background_color=C_ORANGE,
                       margin_top=6, margin_bottom=10),
        ))
        id_card.add(avatar_box)

        id_card.add(toga.Label(self._user_name,
            style=Pack(font_size=20, font_weight="bold", color=C_TEXT_DARK,
                       text_align=CENTER, margin_top=8)))
        if self._user_email:
            id_card.add(toga.Label(self._user_email,
                style=Pack(font_size=11, color=C_TEXT_SOFT, text_align=CENTER, margin_top=4)))

        id_card.add(self._spacer(12))

        # ── Stats from DB ─────────────────────────────────────────
        _stats = _db_get_stats_perfil(self._user_id)

        # ── OWNER stats: Guardados + Espacios (no Visitas) ────────
        # ── ENTREPRENEUR stats: Guardados + Visitas (no Espacios) ─
        stats_row = toga.Box(
            style=Pack(direction=ROW, align_items=CENTER,
                       margin_bottom=14, margin_left=6, margin_right=6)
        )

        if self._user_rol == "propietario":
            # Owner: Guardados (favorites of owner's listings) + Espacios published
            stat_items = [
                (str(_stats["guardados"]), "Guardados"),
                (str(_stats["listados"]),  "Espacios"),
            ]
        else:
            # Entrepreneur: Guardados (favorites) + Visitas (detail views)
            stat_items = [
                (str(_stats["guardados"]),     "Guardados"),
                (str(_stats["visitas_total"]), "Visitas"),
            ]

        for i, (value, label) in enumerate(stat_items):
            stat = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, flex=1))
            stat.add(toga.Label(value,
                style=Pack(font_size=18, font_weight="bold",
                           color=C_ORANGE, text_align=CENTER)))
            stat.add(toga.Label(label,
                style=Pack(font_size=10, color=C_TEXT_SOFT, text_align=CENTER)))
            stats_row.add(stat)
            if i < len(stat_items) - 1:
                stats_row.add(toga.Box(style=Pack(width=1, height=30, background_color="#DDDDDD")))
        id_card.add(stats_row)
        page.add(id_card)

        # ── Profile completeness (only if no photo) ───────────────
        if not foto_bytes:
            prog_box = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                           margin_top=4, margin_bottom=6,
                                           margin_left=10, margin_right=10))
            prog_box.add(toga.Label("Completitud del perfil — 70%",
                style=Pack(font_size=11, color=C_TEXT_MID, margin_top=10, margin_bottom=6)))
            bar_track = toga.Box(style=Pack(direction=ROW, margin_bottom=6))
            for i in range(10):
                c = C_ORANGE if i < 7 else "#EEEEEE"
                bar_track.add(toga.Box(style=Pack(flex=1, height=8, background_color=c, margin=2)))
            prog_box.add(bar_track)
            prog_box.add(toga.Label("Agrega foto para completar tu perfil",
                style=Pack(font_size=10, color=C_TEXT_SOFT, margin_bottom=10)))
            page.add(prog_box)

        # ── Active plan — read from DB ────────────────────────────
        plan_box = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                        margin_top=4, margin_bottom=6,
                                        margin_left=10, margin_right=10))
        plan_box.add(toga.Label("🏷️  Plan Activo",
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       margin_top=10, margin_bottom=4)))
        plan_box.add(toga.Label(self._user_plan,
            style=Pack(font_size=12, color=C_ORANGE_DARK, margin_bottom=8)))
        plan_box.add(toga.Button("Ver todos los planes",
            on_press=lambda w: self._set(self._plans()),
            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                       background_color=C_ORANGE, margin_bottom=12)))
        page.add(plan_box)

        # ── Weekly statistics ─────────────────────────────────────
        page.add(toga.Label("Estadísticas — Esta semana",
            style=Pack(font_size=14, font_weight="bold", color=C_TEXT_DARK,
                       margin_left=10, margin_top=12, margin_bottom=6)))

        stats_card = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                          margin_left=10, margin_right=10, margin_bottom=6))

        # ── OWNER metrics: Guardados + Espacios ───────────────────
        # ── ENTREPRENEUR metrics: Guardados + Visitas ─────────────
        if self._user_rol == "propietario":
            metrics = [
                ("💾  Guardados", str(_stats["guardados"]), "#E8A020"),
                ("📍  Espacios",  str(_stats["listados"]),  C_GREEN_SAVE),
            ]
        else:
            metrics = [
                ("💾  Guardados", str(_stats["guardados"]),     "#E8A020"),
                ("👁️  Visitas",   str(_stats["visitas_total"]), C_ORANGE),
            ]

        for i in range(0, len(metrics), 2):
            mrow = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                       margin_top=10, margin_bottom=10))
            for (label, value, color) in metrics[i:i+2]:
                mcol = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, flex=1))
                mcol.add(toga.Label(value,
                    style=Pack(font_size=20, font_weight="bold",
                               color=color, text_align=CENTER)))
                mcol.add(toga.Label(label,
                    style=Pack(font_size=10, color=C_TEXT_MID, text_align=CENTER)))
                mrow.add(mcol)
            stats_card.add(mrow)
            if i + 2 < len(metrics):
                stats_card.add(toga.Divider())
        page.add(stats_card)

        # ── Weekly bar chart (only for Entrepreneur) ──────────────
        if self._user_rol != "propietario":
            page.add(toga.Label("Visitas por día",
                style=Pack(font_size=11, color=C_TEXT_MID,
                           margin_left=10, margin_top=10, margin_bottom=8)))
            chart_box = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                             margin_left=10, margin_right=10, margin_bottom=10))
            dias    = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
            visitas = _stats["visitas_semana"]
            max_v   = max(visitas) if max(visitas) > 0 else 1
            max_h   = 55

            bars_row = toga.Box(style=Pack(direction=ROW, align_items="end",
                                           margin_top=4, margin_bottom=6))
            for dia, v in zip(dias, visitas):
                bar_col = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, flex=1))
                h = max(4, int((v / max_v) * max_h))
                bar_col.add(toga.Label(str(v),
                    style=Pack(font_size=8, color=C_TEXT_SOFT, text_align=CENTER)))
                bar_col.add(toga.Box(style=Pack(height=h,
                    background_color=C_ORANGE if v == max_v else "#F4A07A")))
                bar_col.add(toga.Label(dia,
                    style=Pack(font_size=9, color=C_TEXT_MID,
                               text_align=CENTER, margin_top=3)))
                bars_row.add(bar_col)
            chart_box.add(bars_row)
            page.add(chart_box)

        page.add(toga.Box(style=Pack(height=10)))
        page.add(toga.Button("Cerrar sesión", on_press=self._logout,
            style=Pack(font_size=13, font_weight="bold", color=C_ORANGE_DARK,
                       background_color="#FFE8D6",
                       margin_left=10, margin_right=10, margin_bottom=28)))

        sc.content = page
        return sc

    # ── Filters ───────────────────────────────────────────────────────
    FILTROS_MAP = {
        "Todos":       [],
        "Renta":       ["renta"],
        "Venta":       ["venta"],
        "Oficina":     ["oficina"],
        "Bodega":      ["bodega"],
        "Stand":       ["stand", "módulo", "kiosco"],
        "Restaurante": ["restaurante"],
    }

    def _apply_filter(self, label):
        if label == "Todos":
            self._filtros = set()
        else:
            if label in self._filtros:
                self._filtros.discard(label)
            else:
                self._filtros.add(label)
        self._set(self._home())

    def _locales_filtrados(self):
        """Returns filtered listings — reads from DB."""
        todos = _db_get_locales()
        if not self._filtros:
            return todos
        resultado = []
        for local in todos:
            tipo_str = local["tipo"].lower()
            detalle  = local["tipo_detalle"].lower()
            for label in self._filtros:
                palabras = self.FILTROS_MAP.get(label, [])
                if any(p in tipo_str or p in detalle for p in palabras):
                    if local not in resultado:
                        resultado.append(local)
        return resultado

    def _filter_screen(self):
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color="#FAFAFA"))

        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Volver", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("⚡  Filtrar Espacios",
                           style=Pack(font_size=13, font_weight="bold",
                                      color=C_WHITE, margin_left=6, flex=1)))
        n_activos = len(self._filtros)
        if n_activos:
            bar.add(toga.Label(f"{n_activos} activo{'s' if n_activos>1 else ''}",
                               style=Pack(font_size=11, color="#FFE0CC", margin_right=12)))
        page.add(bar)

        page.add(toga.Label("Toca para activar o desactivar un filtro",
            style=Pack(font_size=11, color=C_TEXT_SOFT, margin_left=14, margin_top=12, margin_bottom=4)))
        page.add(toga.Label("Puedes combinar varios filtros a la vez",
            style=Pack(font_size=11, color=C_TEXT_SOFT, margin_left=14, margin_bottom=14)))

        todos_locales = _db_get_locales()
        opciones = [
            ("🏷️",  "Todos",       "Ver todos los espacios disponibles"),
            ("🔑",  "Renta",       "Espacios disponibles para arrendar"),
            ("💰",  "Venta",       "Espacios disponibles para compra directa"),
            ("🏢",  "Oficina",     "Espacios ejecutivos y corporativos"),
            ("🏭",  "Bodega",      "Almacenamiento, logística y distribución"),
            ("🛍️", "Stand",        "Stands, módulos y kioscos en malls o ferias"),
            ("🍽️", "Restaurante",  "Locales para gastronomía y food service"),
        ]

        for (ico, label, desc) in opciones:
            es_todos  = label == "Todos"
            activo    = (es_todos and not self._filtros) or \
                        (not es_todos and label in self._filtros)
            bg        = "#FFF0E0" if activo else C_WHITE
            n_results = (
                len(todos_locales) if es_todos else
                len([l for l in todos_locales
                     if any(p in l["tipo"].lower() or p in l["tipo_detalle"].lower()
                            for p in self.FILTROS_MAP.get(label, []))])
            )
            row = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                       background_color=bg,
                                       margin_left=10, margin_right=10, margin_bottom=2))
            row.add(toga.Label(ico, style=Pack(font_size=22,
                                               margin_top=10, margin_bottom=10,
                                               margin_left=10, margin_right=8)))
            text_col = toga.Box(style=Pack(direction=COLUMN, flex=1,
                                           margin_top=10, margin_bottom=10))
            text_col.add(toga.Label(label,
                style=Pack(font_size=12, font_weight="bold",
                           color=C_ORANGE if activo else C_TEXT_DARK)))
            text_col.add(toga.Label(desc,
                style=Pack(font_size=10, color=C_TEXT_SOFT, margin_top=2)))
            text_col.add(toga.Label(f"{n_results} espacio{'s' if n_results != 1 else ''}",
                style=Pack(font_size=10, color=C_ORANGE_DARK, font_weight="bold", margin_top=2)))
            row.add(text_col)
            page.add(row)
            page.add(toga.Button(
                f"{'✔ ' if activo else ''}  {label}",
                on_press=lambda w, lv=label: self._toggle_filter_and_refresh(lv),
                style=Pack(font_size=10, font_weight="bold",
                           color=C_WHITE if activo else C_TEXT_MID,
                           background_color=C_ORANGE if activo else "#EEEEEE",
                           margin_left=10, margin_right=10, margin_bottom=2),
            ))
            page.add(toga.Divider())

        if self._filtros:
            page.add(toga.Box(style=Pack(height=10)))
            page.add(toga.Label("Filtros activos:",
                style=Pack(font_size=11, font_weight="bold",
                           color=C_TEXT_DARK, margin_left=14, margin_bottom=6)))
            chips_row = toga.Box(style=Pack(direction=ROW, margin_left=10,
                                            margin_right=10, margin_bottom=10))
            for f in self._filtros:
                chips_row.add(toga.Label(f"  {f}  ",
                    style=Pack(font_size=11, font_weight="bold",
                               color=C_WHITE, background_color=C_ORANGE, margin=3)))
            page.add(chips_row)

        page.add(toga.Box(style=Pack(height=14)))
        n_fil = len(self._locales_filtrados())
        page.add(toga.Button(
            f"Ver {n_fil} resultado{'s' if n_fil != 1 else ''}",
            on_press=lambda w: self._set(self._home()),
            style=Pack(font_size=13, font_weight="bold", color=C_WHITE,
                       background_color=C_ORANGE,
                       margin_left=14, margin_right=14, margin_bottom=8),
        ))
        if self._filtros:
            page.add(toga.Button("✕  Limpiar todos los filtros",
                on_press=lambda w: self._clear_filters(),
                style=Pack(font_size=12, font_weight="bold", color=C_ORANGE_DARK,
                           background_color="#FFE8D6",
                           margin_left=14, margin_right=14, margin_bottom=24)))
        else:
            page.add(toga.Box(style=Pack(height=24)))

        sc.content = page
        return sc

    def _toggle_filter_and_refresh(self, label):
        if label == "Todos":
            self._filtros = set()
        else:
            if label in self._filtros:
                self._filtros.discard(label)
            else:
                self._filtros.add(label)
        self._set(self._filter_screen())

    def _clear_filters(self):
        self._filtros = set()
        self._set(self._filter_screen())

    def _clear_filters_home(self):
        self._filtros = set()
        self._set(self._home())

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 5 — HOME
    # ═══════════════════════════════════════════════════════════════
    def _home(self):
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color="#FAFAFA"))

        # ── Top bar ────────────────────────────────────────────────
        top_bar = toga.Box(style=Pack(direction=ROW, background_color=C_WHITE,
                                       align_items=CENTER, margin_bottom=0))
        loc_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=12))

        _loc_label = toga.Label(
            f"📍 {self._ubicacion_actual}",
            style=Pack(font_size=11, color=C_TEXT_SOFT),
        )
        loc_col.add(_loc_label)
        loc_col.add(toga.Label(f"Hola, {self._user_name} 👋",
            style=Pack(font_size=14, font_weight="bold", color=C_TEXT_DARK)))
        top_bar.add(loc_col)

        # Background location fetch
        def _fetch_ubicacion():
            try:
                req = urllib.request.Request(
                    "https://ipapi.co/json/",
                    headers={"User-Agent": "EmprendeMap/1.0"},
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data   = json.loads(resp.read().decode())
                ciudad = data.get("city", "")
                pais   = data.get("country_name", "")
                nueva  = f"📍 {ciudad}, {pais}" if ciudad and pais else \
                         f"📍 {pais}" if pais else "📍 Ubicación desconocida"
                self._ubicacion_actual = nueva
                self.main_window.app.loop.call_soon_threadsafe(
                    lambda: setattr(_loc_label, "text", nueva))
            except Exception:
                pass

        if self._ubicacion_actual == "Obteniendo ubicación...":
            threading.Thread(target=_fetch_ubicacion, daemon=True).start()

        btns = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_right=10))

        # ── [OWNER ONLY] Publish new listing button ────────────────
        if self._user_rol == "propietario":
            btns.add(toga.Button(
                "＋",
                on_press=lambda w: self._set(self._publish_listing()),
                style=Pack(font_size=16, font_weight="bold",
                           background_color=C_ORANGE, color=C_WHITE, margin=4),
            ))

        btns.add(toga.Button("👤", on_press=lambda w: self._set(self._profile()),
                             style=Pack(font_size=14, background_color="#FFE0CC", margin=4)))
        top_bar.add(btns)
        page.add(top_bar)
        page.add(toga.Divider())

        # ── Main title ─────────────────────────────────────────────
        title_box = toga.Box(style=Pack(direction=COLUMN, margin_left=16,
                                         margin_top=14, margin_bottom=10))
        title_box.add(toga.Label("Descubre",
            style=Pack(font_size=24, font_weight="bold", color=C_TEXT_DARK)))
        title_box.add(toga.Label("Tu Nuevo Espacio",
            style=Pack(font_size=24, font_weight="bold", color=C_ORANGE)))
        page.add(title_box)

        # ── Search bar + filter button ─────────────────────────────
        search_row = toga.Box(style=Pack(direction=ROW, background_color="#F0F0F0",
                                          align_items=CENTER,
                                          margin_left=14, margin_right=14, margin_bottom=10))
        search_row.add(toga.Label("🔍", style=Pack(font_size=16, margin=10)))
        self._search_field = toga.TextInput(
            placeholder="Buscar zona, tipo de local...",
            style=Pack(font_size=13, background_color="#F0F0F0", color=C_TEXT_DARK, flex=1),
        )
        search_row.add(self._search_field)
        search_row.add(toga.Button("⚡", on_press=lambda w: self._set(self._filter_screen()),
                                   style=Pack(font_size=14, font_weight="bold",
                                              color=C_WHITE, background_color=C_ORANGE, margin=6)))
        page.add(search_row)

        # ── Type chips (quick filters, consistent with panel) ──────
        tipos_rapidos = ["Todos", "Renta", "Venta", "Oficina", "Bodega", "Stand", "Restaurante"]
        chips_row = toga.Box(style=Pack(direction=ROW, margin_left=6,
                                         margin_right=6, margin_bottom=14))
        for t in tipos_rapidos:
            es_todos = t == "Todos"
            activo   = (es_todos and not self._filtros) or \
                       (not es_todos and t in self._filtros)
            chips_row.add(toga.Button(t, on_press=lambda w, tv=t: self._apply_filter(tv),
                style=Pack(font_size=9,
                           font_weight="bold" if activo else "normal",
                           color=C_WHITE if activo else C_TEXT_MID,
                           background_color=C_ORANGE if activo else "#EEEEEE",
                           margin=2, flex=1)))
        page.add(chips_row)

        # ── Listings — role-based ─────────────────────────────────
        # OWNER: shows only their own published listings
        # ENTREPRENEUR: shows all published listings
        if self._user_rol == "propietario" and self._user_id is not None:
            locales_mostrar = _db_get_locales_propietario(self._user_id)
        else:
            locales_mostrar = self._locales_filtrados()

        sec_header = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                          margin_left=14, margin_right=14, margin_bottom=10))
        sec_label  = "Mis Espacios Publicados" if self._user_rol == "propietario" \
                     else "Espacios Disponibles"
        sec_header.add(toga.Label(sec_label,
            style=Pack(font_size=15, font_weight="bold", color=C_TEXT_DARK, flex=1)))
        sec_header.add(toga.Label(
            f"{len(locales_mostrar)} resultado{'s' if len(locales_mostrar) != 1 else ''}",
            style=Pack(font_size=11, color=C_TEXT_SOFT)))
        page.add(sec_header)

        # Active filter badges (only for entrepreneur)
        if self._filtros and self._user_rol != "propietario":
            badge_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                             margin_left=10, margin_right=10, margin_bottom=8))
            badge_row.add(toga.Label("Filtros: ", style=Pack(font_size=10, color=C_TEXT_SOFT)))
            for f in self._filtros:
                badge_row.add(toga.Label(f"  {f}  ",
                    style=Pack(font_size=10, font_weight="bold",
                               color=C_WHITE, background_color=C_ORANGE, margin_right=4)))
            badge_row.add(toga.Button("✕", on_press=lambda w: self._clear_filters_home(),
                style=Pack(font_size=10, color=C_ORANGE_DARK,
                           background_color="#FFE8D6", margin_left=4)))
            page.add(badge_row)

        # Listings grid
        locales_grid = toga.Box(style=Pack(direction=COLUMN, margin_left=10, margin_right=10))
        if locales_mostrar:
            for local in locales_mostrar:
                locales_grid.add(self._local_card(local))
                locales_grid.add(toga.Box(style=Pack(height=8)))
        else:
            empty_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                             margin_top=30, margin_bottom=30))
            empty_box.add(toga.Label("🔍",
                style=Pack(font_size=48, text_align=CENTER, margin_bottom=10)))
            if self._user_rol == "propietario":
                empty_box.add(toga.Label("Aún no has publicado espacios",
                    style=Pack(font_size=13, font_weight="bold",
                               color=C_TEXT_MID, text_align=CENTER, margin_bottom=8)))
                empty_box.add(toga.Label("Toca ＋ para publicar tu primer local",
                    style=Pack(font_size=11, color=C_TEXT_SOFT, text_align=CENTER)))
            else:
                empty_box.add(toga.Label("No hay espacios con los filtros seleccionados",
                    style=Pack(font_size=13, font_weight="bold",
                               color=C_TEXT_MID, text_align=CENTER, margin_bottom=8)))
                empty_box.add(toga.Label("Prueba con otro filtro",
                    style=Pack(font_size=11, color=C_TEXT_SOFT, text_align=CENTER)))
            locales_grid.add(empty_box)
        page.add(locales_grid)

        # ── Section: Quick access ──────────────────────────────────
        page.add(toga.Box(style=Pack(height=10)))
        quick_header = toga.Box(style=Pack(direction=COLUMN, margin_left=14, margin_bottom=10))
        quick_header.add(toga.Label("Accesos Rápidos",
            style=Pack(font_size=16, font_weight="bold", color=C_TEXT_DARK)))
        page.add(quick_header)

        quick_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                         margin_left=10, margin_right=10, margin_bottom=16))
        accesos = [
            ("💼", "Planes",    lambda w: self._set(self._plans())),
            ("♥",  "Favoritos", lambda w: self._set(self._favorites())),
            ("👤", "Perfil",    lambda w: self._set(self._profile())),
            ("🚪", "Salir",     self._logout),
        ]
        for (ico, label, handler) in accesos:
            btn_col = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, flex=1))
            btn_col.add(toga.Button(ico, on_press=handler,
                style=Pack(font_size=20, background_color="#FFF0E0", margin_bottom=4)))
            btn_col.add(toga.Label(label,
                style=Pack(font_size=9, color=C_TEXT_MID, text_align=CENTER)))
            quick_row.add(btn_col)
        page.add(quick_row)

        page.add(toga.Divider())
        page.add(toga.Label("EmprendeMap  •  © 2026",
            style=Pack(font_size=10, color=C_TEXT_SOFT, text_align=CENTER,
                       margin_top=8, margin_bottom=20)))

        sc.content = page
        return sc

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN — PUBLISH LISTING (Owner only)
    # ═══════════════════════════════════════════════════════════════
    def _publish_listing(self):
        sc, col = self._page(bg=C_YELLOW)

        # ── Top bar ────────────────────────────────────────────────
        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Volver", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("＋  Publicar Espacio",
                           style=Pack(font_size=13, font_weight="bold",
                                      color=C_WHITE, margin_left=6, flex=1)))

        # Wrap bar in a non-centered box so it spans full width
        bar_wrap = toga.Box(style=Pack(direction=COLUMN))
        bar_wrap.add(bar)
        col.add(bar_wrap)

        col.add(self._spacer(10))
        col.add(self._lbl("Publica tu espacio", size=20, bold=True, color=C_TEXT_DARK, mt=4))
        col.add(self._lbl("Completa los datos de tu local",
                          size=12, color=C_TEXT_SOFT, mt=4, mb=20))

        # ── Form fields ────────────────────────────────────────────
        nombre_grp,  self._pub_nombre  = self._field_group("Nombre del local", "Ej: Local Comercial Centro")
        zona_grp,    self._pub_zona    = self._field_group("Zona / Ubicación", "Ej: Centro Histórico, San Salvador")
        precio_grp,  self._pub_precio  = self._field_group("Precio", "Ej: $450")
        m2_grp,      self._pub_m2      = self._field_group("Metros cuadrados", "Ej: 85 m²")
        contacto_grp, self._pub_tel    = self._field_group("Teléfono de contacto", "Ej: +503 7000-1234")
        desc_grp,    self._pub_desc    = self._field_group("Descripción", "Describe tu espacio...")

        col.add(nombre_grp)
        col.add(zona_grp)
        col.add(precio_grp)
        col.add(m2_grp)
        col.add(contacto_grp)
        col.add(desc_grp)

        # ── Tipo de operación ──────────────────────────────────────
        tipo_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=14))
        tipo_box.add(self._lbl("Tipo de operación", size=12, color=C_TEXT_MID, mb=6))
        self._pub_tipo = toga.Selection(
            items=["Renta", "Venta"],
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=300),
        )
        tipo_box.add(self._pub_tipo)
        col.add(tipo_box)

        # ── Tipo detalle ───────────────────────────────────────────
        detalle_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=14))
        detalle_box.add(self._lbl("Tipo de local", size=12, color=C_TEXT_MID, mb=6))
        self._pub_tipo_detalle = toga.Selection(
            items=["Local Comercial", "Bodega", "Oficina",
                   "Kiosco / Stand", "Restaurante", "Stand / Módulo", "Otro"],
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=300),
        )
        detalle_box.add(self._pub_tipo_detalle)
        col.add(detalle_box)

        # ── Periodo ───────────────────────────────────────────────
        periodo_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=14))
        periodo_box.add(self._lbl("Periodo de pago", size=12, color=C_TEXT_MID, mb=6))
        self._pub_periodo = toga.Selection(
            items=["mes", "año", "único", "semana"],
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=300),
        )
        periodo_box.add(self._pub_periodo)
        col.add(periodo_box)

        # ── Emoji selector ────────────────────────────────────────
        emoji_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_bottom=14))
        emoji_box.add(self._lbl("Ícono representativo", size=12, color=C_TEXT_MID, mb=6))
        self._pub_emoji = toga.Selection(
            items=["🏪", "🏭", "🏢", "🏬", "🍽️", "🛍️", "🏠", "🏗️", "🏨"],
            style=Pack(font_size=13, background_color=C_INPUT_BG, color=C_TEXT_DARK, width=300),
        )
        emoji_box.add(self._pub_emoji)
        col.add(emoji_box)

        col.add(self._spacer(10))

        # ── Submit button ─────────────────────────────────────────
        col.add(self._btn_orange("📤  Publicar espacio", self._do_publish))
        col.add(self._spacer(30))
        return sc

    def _do_publish(self, w):
        """Validates and saves the new listing to DB."""
        nombre   = self._pub_nombre.value.strip()
        zona     = self._pub_zona.value.strip()
        precio   = self._pub_precio.value.strip()
        m2       = self._pub_m2.value.strip()
        contacto = self._pub_tel.value.strip()
        desc     = self._pub_desc.value.strip()

        if not all([nombre, zona, precio, m2, contacto, desc]):
            self.main_window.info_dialog(
                "Campos requeridos",
                "Por favor completa todos los campos antes de publicar.")
            return

        tipo         = str(self._pub_tipo.value)
        tipo_detalle = str(self._pub_tipo_detalle.value)
        periodo      = str(self._pub_periodo.value)
        emoji        = str(self._pub_emoji.value)

        # Save to DB
        _db_publicar_local(
            propietario_id=self._user_id,
            nombre=nombre,
            tipo=tipo,
            tipo_detalle=tipo_detalle,
            precio=precio,
            periodo=periodo,
            zona=zona,
            m2=m2,
            emoji=emoji,
            desc=desc,
            contacto=contacto,
        )

        _db_registrar_actividad(
            self._user_id, "vista_detalle",
            f"Publicaste '{nombre[:18]}'",
        )

        self.main_window.info_dialog(
            "¡Publicado! 🎉",
            f"Tu espacio \"{nombre}\" ha sido publicado exitosamente.\n"
            "Aparecerá en tu lista de espacios publicados.",
        )
        self._set(self._home())

    def _local_card(self, local):
        card = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE))

        # Simulated image zone with large emoji
        img_zone = toga.Box(style=Pack(direction=COLUMN, background_color="#FFE8D0",
                                        align_items=CENTER, height=100))
        price_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER,
                                         margin_top=6, margin_right=6))
        price_row.add(toga.Box(style=Pack(flex=1)))
        price_row.add(toga.Label(
            f"{local['precio']}/{local['periodo'][:3]}",
            style=Pack(font_size=9, font_weight="bold",
                       color=C_WHITE, background_color="#00000088"),
        ))
        img_zone.add(price_row)
        img_zone.add(toga.Label(local["emoji"],
            style=Pack(font_size=36, text_align=CENTER, margin_top=4)))
        if local["verificado"]:
            img_zone.add(toga.Label("✅ Verificado",
                style=Pack(font_size=9, color=C_ORANGE_DARK, text_align=CENTER)))
        card.add(img_zone)

        # Listing info
        info = toga.Box(style=Pack(direction=COLUMN, margin=8))
        # Rating row
        rating_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=2))
        rating_row.add(toga.Label("⭐", style=Pack(font_size=11)))
        rating_row.add(toga.Label(f" {local['rating']}",
            style=Pack(font_size=11, font_weight="bold", color=C_TEXT_DARK)))
        rating_row.add(toga.Label(f"  ·  {local['tipo']}",
            style=Pack(font_size=10, color=C_ORANGE)))
        info.add(rating_row)
        info.add(toga.Label(local["nombre"],
            style=Pack(font_size=12, font_weight="bold", color=C_TEXT_DARK, margin_bottom=2)))
        info.add(toga.Label(f"📍 {local['zona'].split(',')[0]}",
            style=Pack(font_size=10, color=C_TEXT_SOFT, margin_bottom=6)))
        # View detail button
        info.add(toga.Button("Ver detalle →",
            on_press=lambda w, loc=local: self._set(self._local_detail(loc)),
            style=Pack(font_size=10, font_weight="bold",
                       color=C_WHITE, background_color=C_ORANGE, margin_bottom=2)))
        card.add(info)
        return card

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN 6 — LISTING DETAIL
    # ═══════════════════════════════════════════════════════════════
    def _local_detail(self, local):
        # Register detail view in DB
        _db_registrar_actividad(
            self._user_id, "vista_detalle",
            f"Viste el detalle de '{local['nombre']}'",
        )
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color="#FAFAFA"))

        # ── Top bar ─────────────────────────────────────────────────
        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Volver", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("Detalle del Espacio",
                           style=Pack(font_size=13, font_weight="bold",
                                      color=C_WHITE, margin_left=6, flex=1)))

        def _toggle_fav(w, loc=local):
            if self._user_id is None:
                self.main_window.info_dialog(
                    "Inicia sesión", "Debes iniciar sesión para guardar favoritos.")
                return
            guardado = _db_toggle_favorito(self._user_id, loc["id"])
            if guardado:
                _db_registrar_actividad(self._user_id, "favorito_add",
                                        f"Guardaste '{loc['nombre'][:16]}'")
                self.main_window.info_dialog("Guardado ♥",
                                             f"'{loc['nombre']}' añadido a favoritos.")
            else:
                _db_registrar_actividad(self._user_id, "favorito_remove",
                                        f"Quitaste '{loc['nombre'][:16]}'")
                self.main_window.info_dialog("Eliminado",
                                             f"'{loc['nombre']}' quitado de favoritos.")

        bar.add(toga.Button("♡", on_press=_toggle_fav,
                            style=Pack(font_size=14, color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        page.add(bar)

        # ── Hero zone ────────────────────────────────────────────────
        hero = toga.Box(style=Pack(direction=COLUMN, background_color="#FFE0C0",
                                    align_items=CENTER, height=130))
        hero.add(toga.Label(local["emoji"],
            style=Pack(font_size=56, text_align=CENTER, margin_top=14)))
        if local["verificado"]:
            hero.add(toga.Label("✅  Propiedad Verificada",
                style=Pack(font_size=11, color=C_ORANGE_DARK, text_align=CENTER, margin_top=4)))
        page.add(hero)

        # ── Price ────────────────────────────────────────────────────
        price_row = toga.Box(style=Pack(direction=ROW, background_color=C_ORANGE, align_items=CENTER))
        price_row.add(toga.Label(f"  {local['precio']}",
            style=Pack(font_size=18, font_weight="bold", color=C_WHITE,
                       margin_top=8, margin_bottom=8, flex=1)))
        price_row.add(toga.Label(f"/ {local['periodo']}  ",
            style=Pack(font_size=11, color="#FFE0C0", margin_right=10)))
        page.add(price_row)

        # ── Name + rating + zone ────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        info_box = toga.Box(style=Pack(direction=COLUMN, background_color=C_WHITE,
                                        margin_top=0, margin_bottom=4,
                                        margin_left=14, margin_right=14))
        info_box.add(toga.Label(local["nombre"],
            style=Pack(font_size=16, font_weight="bold",
                       color=C_TEXT_DARK, margin_top=12, margin_bottom=6)))
        # Rating in compact row
        rt_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=4))
        rt_row.add(toga.Label("⭐ ", style=Pack(font_size=12)))
        rt_row.add(toga.Label(f"{local['rating']}",
            style=Pack(font_size=12, font_weight="bold", color=C_TEXT_DARK)))
        tipo_color = C_ORANGE if local["tipo"] == "Renta" else C_GREEN_SAVE
        rt_row.add(toga.Label(f"  ·  {local['tipo']}",
            style=Pack(font_size=11, font_weight="bold", color=tipo_color)))
        rt_row.add(toga.Label(f"  ·  {local['m2']}",
            style=Pack(font_size=11, color=C_TEXT_MID)))
        info_box.add(rt_row)
        info_box.add(toga.Label(f"📍  {local['zona']}",
            style=Pack(font_size=11, color=C_TEXT_MID, margin_bottom=12)))
        page.add(info_box)

        # ── TYPE ─────────────────────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        page.add(toga.Label("Tipo",
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       margin_top=12, margin_left=14, margin_bottom=8)))
        mod_color = C_ORANGE if local["tipo"] == "Renta" else C_GREEN_SAVE
        page.add(toga.Label(f"  {local['tipo']}  ",
            style=Pack(font_size=11, font_weight="bold",
                       color=C_WHITE, background_color=mod_color,
                       margin_left=14, margin_bottom=6)))
        page.add(toga.Label(f"  {local['tipo_detalle']}  ",
            style=Pack(font_size=11, font_weight="bold",
                       color=C_ORANGE_DARK, background_color="#FFF0E0",
                       margin_left=14, margin_bottom=8)))
        tipo_desc = {
            "Local Comercial": "Espacio apto para tienda, negocio al detalle o servicio al publico.",
            "Bodega":          "Ideal para almacenamiento, logistica y distribucion de mercaderia.",
            "Oficina":         "Espacio profesional para empresas, startups o trabajo remoto.",
            "Kiosco / Stand":  "Modulo en zona de alto trafico, ideal para emprendimientos.",
            "Restaurante":     "Local equipado o habilitado para operaciones gastronomicas.",
            "Stand / Modulo":  "Espacio flexible en mall o feria para presencia comercial.",
        }.get(local["tipo_detalle"], "Espacio disponible para emprendimiento.")
        page.add(toga.Label(tipo_desc,
            style=Pack(font_size=11, color=C_TEXT_MID,
                       margin_left=14, margin_right=14, margin_bottom=12)))

        # ── DESCRIPTION ──────────────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        page.add(toga.Label("Descripcion",
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       margin_top=12, margin_left=14, margin_bottom=8)))
        page.add(toga.Label(local["desc"],
            style=Pack(font_size=11, color=C_TEXT_MID,
                       margin_left=14, margin_right=14, margin_bottom=12)))

        # ── FEATURES ─────────────────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        page.add(toga.Label("Caracteristicas",
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       margin_top=12, margin_left=14, margin_bottom=8)))
        feat_box = toga.Box(style=Pack(direction=COLUMN,
                                        margin_left=14, margin_right=14, margin_bottom=12))
        for (ico, txt) in local["features"]:
            feat_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=6))
            feat_row.add(toga.Label(ico, style=Pack(font_size=15, margin_right=10)))
            feat_row.add(toga.Label(txt, style=Pack(font_size=11, color=C_TEXT_MID)))
            feat_box.add(feat_row)
        page.add(feat_box)

        # ── LOCATION ────────────────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        page.add(toga.Label("Ubicacion",
            style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK,
                       margin_top=12, margin_left=14, margin_bottom=8)))
        map_sim = toga.Box(style=Pack(direction=COLUMN, background_color="#E8F4E8",
                                       align_items=CENTER, height=80,
                                       margin_left=14, margin_right=14, margin_bottom=14))
        map_sim.add(toga.Label("🗺️",
            style=Pack(font_size=32, text_align=CENTER, margin_top=6)))
        map_sim.add(toga.Label(local["zona"],
            style=Pack(font_size=10, color=C_TEXT_MID, text_align=CENTER, margin_top=2)))
        page.add(map_sim)

        # ── CONTACT / CTA ────────────────────────────────────────────
        page.add(toga.Box(style=Pack(height=1, background_color="#EEEEEE")))
        page.add(toga.Label("Interesado en este espacio?",
            style=Pack(font_size=12, color=C_TEXT_MID,
                       margin_top=12, margin_left=14, margin_bottom=10)))
        page.add(toga.Button(
            f"📞  Contactar: {local['contacto']}",
            on_press=lambda w: self.main_window.info_dialog(
                "Contacto",
                f"Llamando a:\n{local['contacto']}\n\nDisponible con plan activo."),
            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                       background_color=C_ORANGE,
                       margin_left=14, margin_right=14, margin_bottom=8),
        ))
        page.add(toga.Button(
            "💬  Enviar mensaje",
            on_press=lambda w: self.main_window.info_dialog(
                "Mensaje enviado",
                f"Tu solicitud sobre '{local['nombre']}' fue enviada al propietario."),
            style=Pack(font_size=12, font_weight="bold", color=C_ORANGE,
                       background_color="#FFE8D6",
                       margin_left=14, margin_right=14, margin_bottom=24),
        ))

        sc.content = page
        return sc

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN — FAVORITES
    # ═══════════════════════════════════════════════════════════════
    def _favorites(self):
        sc   = toga.ScrollContainer(horizontal=False)
        page = toga.Box(style=Pack(direction=COLUMN, background_color="#FAFAFA"))

        # ── Top bar ────────────────────────────────────────────────
        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Home", on_press=lambda w: self._set(self._home()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("Mis Favoritos",
                           style=Pack(font_size=14, font_weight="bold",
                                      color=C_WHITE, margin_left=8, flex=1)))
        # Favorites list from DB
        favs = self._user_favs
        n    = len(favs)
        bar.add(toga.Label(f"{n} guardado{'s' if n != 1 else ''}",
                           style=Pack(font_size=11, color="#FFE0CC", margin_right=12)))
        page.add(bar)

        # ── Empty state ───────────────────────────────────────────
        if not favs:
            empty = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                         margin_top=60, margin_bottom=40,
                                         margin_left=20, margin_right=20))
            empty.add(toga.Label("♡",
                style=Pack(font_size=64, text_align=CENTER,
                           color="#DDDDDD", margin_bottom=16)))
            empty.add(toga.Label("Aún no tienes favoritos",
                style=Pack(font_size=16, font_weight="bold",
                           color=C_TEXT_MID, text_align=CENTER, margin_bottom=8)))
            empty.add(toga.Label(
                "Toca el ♡ en cualquier espacio para guardarlo aquí.",
                style=Pack(font_size=12, color=C_TEXT_SOFT,
                           text_align=CENTER, margin_bottom=28)))
            empty.add(toga.Button("Explorar espacios",
                on_press=lambda w: self._set(self._home()),
                style=Pack(font_size=13, font_weight="bold",
                           color=C_WHITE, background_color=C_ORANGE)))
            page.add(empty)
            sc.content = page
            return sc

        # ── Counter and order ─────────────────────────────────────
        page.add(toga.Label(
            f"  {n} espacio{'s' if n != 1 else ''} guardado{'s' if n != 1 else ''}",
            style=Pack(font_size=12, color=C_TEXT_SOFT, margin_top=10, margin_bottom=6)))
        page.add(toga.Divider())

        # ── Favorites list ────────────────────────────────────────
        for local in favs:
            # Horizontal card
            card = toga.Box(style=Pack(direction=ROW, background_color=C_WHITE,
                                        align_items=CENTER,
                                        margin_top=4, margin_bottom=4,
                                        margin_left=10, margin_right=10))
            # Emoji zone (thumbnail)
            thumb = toga.Box(style=Pack(direction=COLUMN, background_color="#FFE8D0",
                                         align_items=CENTER, width=72, height=72))
            thumb.add(toga.Label(local["emoji"],
                style=Pack(font_size=30, text_align=CENTER, margin_top=10)))
            if local["verificado"]:
                thumb.add(toga.Label("✅", style=Pack(font_size=10, text_align=CENTER)))
            card.add(thumb)

            # Listing info
            info = toga.Box(style=Pack(direction=COLUMN, flex=1,
                                        margin_left=12, margin_top=8, margin_bottom=8))
            info.add(toga.Label(local["nombre"],
                style=Pack(font_size=13, font_weight="bold", color=C_TEXT_DARK)))
            info.add(toga.Label(f"📍 {local['zona'].split(',')[0]}",
                style=Pack(font_size=11, color=C_TEXT_SOFT, margin_top=2)))
            # Price + type
            price_row = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_top=4))
            price_row.add(toga.Label(local["precio"],
                style=Pack(font_size=13, font_weight="bold", color=C_ORANGE)))
            price_row.add(toga.Label(f"/{local['periodo'][:3]}",
                style=Pack(font_size=10, color=C_TEXT_SOFT, margin_left=2)))
            tipo_color = C_ORANGE if local["tipo"] == "Renta" else C_GREEN_SAVE
            price_row.add(toga.Label(f"  · {local['tipo']}",
                style=Pack(font_size=10, font_weight="bold",
                           color=tipo_color, margin_left=6)))
            info.add(price_row)
            # Rating
            info.add(toga.Label(f"⭐ {local['rating']}",
                style=Pack(font_size=10, color=C_TEXT_MID, margin_top=2)))
            card.add(info)

            # Action buttons (right column)
            actions = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                           margin_right=10, margin_top=6, margin_bottom=6))
            actions.add(toga.Button("Ver →",
                on_press=lambda w, loc=local: self._set(self._local_detail(loc)),
                style=Pack(font_size=10, font_weight="bold",
                           color=C_WHITE, background_color=C_ORANGE, margin_bottom=6)))
            actions.add(toga.Button("🗑",
                on_press=lambda w, loc=local: self._remove_fav(loc),
                style=Pack(font_size=12, color=C_ORANGE_DARK, background_color="#FFE8D6")))
            card.add(actions)
            page.add(card)
            page.add(toga.Divider())

        page.add(toga.Box(style=Pack(height=10)))
        # ── Clear all button ──────────────────────────────────────
        clear_wrap = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                          margin_bottom=30, margin_left=10, margin_right=10))
        clear_wrap.add(toga.Button("🗑  Limpiar todos los favoritos",
            on_press=self._clear_favs,
            style=Pack(font_size=12, font_weight="bold",
                       color=C_ORANGE_DARK, background_color="#FFE8D6")))
        page.add(clear_wrap)

        sc.content = page
        return sc

    # ═══════════════════════════════════════════════════════════════
    #  SCREEN — PROFILE PHOTO EDITOR
    # ═══════════════════════════════════════════════════════════════
    def _edit_avatar(self):
        foto_bytes, off_x, off_y = _db_get_foto(self._user_id) if self._user_id else (None, 0, 0)

        sc, col = self._page(bg="#FFF8F0")

        bar = toga.Box(style=Pack(direction=ROW, background_color=C_HEADER_BAR, align_items=CENTER))
        bar.add(toga.Button("←  Perfil", on_press=lambda w: self._set(self._profile()),
                            style=Pack(font_size=12, font_weight="bold", color=C_WHITE,
                                       background_color=C_ORANGE_DARK, margin=10)))
        bar.add(toga.Label("Editar foto de perfil",
                           style=Pack(font_size=13, font_weight="bold",
                                      color=C_WHITE, margin_left=6, flex=1)))
        bar_wrap = toga.Box(style=Pack(direction=COLUMN))
        bar_wrap.add(bar)
        col.add(bar_wrap)

        col.add(toga.Box(style=Pack(height=20)))
        col.add(toga.Label("Vista previa",
            style=Pack(font_size=12, font_weight="bold",
                       color=C_TEXT_DARK, margin_bottom=10, text_align=CENTER)))

        preview_inner = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER,
                                             background_color="#FFF8F0",
                                             width=150, height=150, margin_bottom=16))
        _preview_label = toga.Label(
            "🏠" if self._user_rol == "propietario" else "🤝",
            style=Pack(font_size=64, text_align=CENTER, margin_top=20),
        )

        def _render_preview(ox, oy):
            preview_inner.clear()
            if foto_bytes:
                try:
                    circ = _make_circular_png(foto_bytes, ox, oy, size=144)
                    src  = circ if circ else foto_bytes
                    preview_inner.add(toga.ImageView(
                        toga.Image(data=src),
                        style=Pack(width=144, height=144),
                    ))
                    return
                except Exception:
                    pass
            preview_inner.add(_preview_label)

        _render_preview(off_x, off_y)
        col.add(preview_inner)

        if foto_bytes:
            col.add(toga.Label("Ajusta la posición dentro del círculo",
                style=Pack(font_size=11, color=C_TEXT_MID,
                           margin_bottom=14, text_align=CENTER)))

            col.add(toga.Label("◀  Posición horizontal  ▶",
                style=Pack(font_size=10, color=C_TEXT_SOFT,
                           margin_bottom=4, text_align=CENTER)))
            _slider_x = toga.Slider(min=-100, max=100, value=off_x,
                                    style=Pack(width=280, margin_bottom=2))
            _val_x = toga.Label(str(int((off_x + 100) / 2) + 1),
                style=Pack(font_size=11, font_weight="bold", color=C_ORANGE,
                           text_align=CENTER, margin_bottom=6))
            col.add(_slider_x)
            col.add(_val_x)

            col.add(toga.Label("▲  Posición vertical  ▼",
                style=Pack(font_size=10, color=C_TEXT_SOFT,
                           margin_top=10, margin_bottom=4, text_align=CENTER)))
            _slider_y = toga.Slider(min=-100, max=100, value=off_y,
                                    style=Pack(width=280, margin_bottom=2))
            _val_y = toga.Label(str(int((off_y + 100) / 2) + 1),
                style=Pack(font_size=11, font_weight="bold", color=C_ORANGE,
                           text_align=CENTER, margin_bottom=6))
            col.add(_slider_y)
            col.add(_val_y)

            def _on_slider(widget):
                ox = int(_slider_x.value)
                oy = int(_slider_y.value)
                _val_x.text = str(int((ox + 100) / 2) + 1)
                _val_y.text = str(int((oy + 100) / 2) + 1)
                _render_preview(ox, oy)

            _slider_x.on_change = _on_slider
            _slider_y.on_change = _on_slider

            col.add(toga.Box(style=Pack(height=10)))

            def _guardar_posicion(w):
                if self._user_id is not None:
                    _db_guardar_offset(self._user_id,
                                       int(_slider_x.value), int(_slider_y.value))
                self._set(self._profile())

            col.add(toga.Button("✅  Guardar posición", on_press=_guardar_posicion,
                style=Pack(font_size=12, font_weight="bold",
                           color=C_WHITE, background_color=C_GREEN_SAVE,
                           width=280, margin_bottom=10)))

        col.add(toga.Box(style=Pack(height=6)))

        async def _cambiar_foto(widget):
            try:
                result = await self.main_window.open_file_dialog(
                    title="Elige una nueva foto de perfil",
                    file_types=["png", "jpg", "jpeg", "webp"],
                    multiple_select=False,
                )
                if result is None:
                    return
                ruta = result[0] if isinstance(result, list) else result
                raw  = Path(ruta).read_bytes()
                if self._user_id is not None:
                    _db_guardar_foto_con_offset(self._user_id, raw, 0, 0)
                self._set(self._edit_avatar())
            except Exception:
                pass

        col.add(toga.Button(
            "📷  Cambiar foto" if foto_bytes else "📷  Agregar foto",
            on_press=_cambiar_foto,
            style=Pack(font_size=12, font_weight="bold",
                       color=C_WHITE, background_color=C_ORANGE,
                       width=280, margin_bottom=10),
        ))

        if foto_bytes:
            def _eliminar_foto(w):
                if self._user_id is not None:
                    _db_guardar_foto_con_offset(self._user_id, None, 0, 0)
                self._set(self._edit_avatar())

            col.add(toga.Button("🗑  Eliminar foto", on_press=_eliminar_foto,
                style=Pack(font_size=11, font_weight="bold",
                           color=C_ORANGE_DARK, background_color="#FFE8D6",
                           width=280, margin_bottom=10)))

        col.add(toga.Box(style=Pack(height=30)))
        return sc

    def _remove_fav(self, local):
        # Delete individual favorite from DB
        if self._user_id is not None:
            _db_eliminar_favorito(self._user_id, local["id"])
        self._set(self._favorites())

    def _clear_favs(self, w=None):
        # Clear all favorites from DB
        if self._user_id is not None:
            _db_limpiar_favoritos(self._user_id)
        self._set(self._favorites())

    def _logout(self, w=None):
        # Delete persistent session from DB
        if self._user_id is not None:
            _db_cerrar_sesion(self._user_id)
        self._user_id    = None
        self._user_name  = "Usuario"
        self._user_email = ""
        self._user_rol   = "emprendedor"
        self._set(self._splash())


# ═════════════════════════════════════════════════════════════════════
def main():
    return EmprendemapApp("EmprendeMap", "com.emprendemap.app")