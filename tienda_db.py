# tienda_db.py
import os
import sqlite3
from sqlite3 import Error

STOCK_INICIAL = 10  # Stock al que se restablece un producto cuando llega a 0


class BaseDatosTienda:
    def __init__(self, ruta="./", bd="tienda.sqlite3"):
        self.bd_path = os.path.join(ruta, bd)
        self.con = None
        self.cursor = None
        self.conectar()
        self.crear_tablas()

    def conectar(self):
        try:
            self.con = sqlite3.connect(self.bd_path, check_same_thread=False)
            self.con.row_factory = sqlite3.Row
            self.cursor = self.con.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.con.commit()
        except Error as e:
            print(f"[DB] Error al conectar: {e}")

    def cerrar(self):
        try:
            if self.con:
                self.con.close()
        except Error as e:
            print(f"[DB] Error al cerrar: {e}")

    def crear_tablas(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    precio REAL NOT NULL CHECK(precio >= 0),
                    stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                    imagen TEXT DEFAULT 'default.jpg'
                );
            """)

            try:
                self.cursor.execute("ALTER TABLE productos ADD COLUMN imagen TEXT DEFAULT 'default.jpg';")
                self.con.commit()
            except:
                pass

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nombre TEXT NOT NULL,
                    cliente_email TEXT,
                    total REAL NOT NULL CHECK(total >= 0),
                    estado TEXT NOT NULL DEFAULT 'pendiente',
                    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)

            # Agregar columna estado si no existe (tablas previas)
            try:
                self.cursor.execute("ALTER TABLE pedidos ADD COLUMN estado TEXT NOT NULL DEFAULT 'pendiente';")
                self.con.commit()
            except:
                pass

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedido_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unit REAL NOT NULL CHECK(precio_unit >= 0),
                    FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY(producto_id) REFERENCES productos(id)
                        ON DELETE RESTRICT ON UPDATE CASCADE
                );
            """)

            # Tabla de avisos para clientes
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS avisos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1,
                    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)

            self.con.commit()
        except Error as e:
            print(f"[DB] Error creando tablas: {e}")

    # ─────────── PRODUCTOS ───────────
    def crear_producto(self, nombre, descripcion, precio, stock, imagen="default.jpg"):
        try:
            self.cursor.execute("""
                INSERT INTO productos(nombre, descripcion, precio, stock, imagen)
                VALUES(?,?,?,?,?);
            """, (nombre.strip(), descripcion, float(precio), int(stock), imagen))
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] No se pudo crear producto: {e}")
            return None

    def listar_productos(self):
        try:
            self.cursor.execute("SELECT * FROM productos ORDER BY id DESC;")
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error listando productos: {e}")
            return []

    def obtener_producto(self, producto_id):
        try:
            self.cursor.execute("SELECT * FROM productos WHERE id=?;", (producto_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo producto: {e}")
            return None

    def actualizar_producto(self, producto_id, nombre, descripcion, precio, stock, imagen=None):
        try:
            if imagen is not None:
                self.cursor.execute("""
                    UPDATE productos
                    SET nombre=?, descripcion=?, precio=?, stock=?, imagen=?
                    WHERE id=?;
                """, (nombre.strip(), descripcion, float(precio), int(stock), imagen, producto_id))
            else:
                self.cursor.execute("""
                    UPDATE productos
                    SET nombre=?, descripcion=?, precio=?, stock=?
                    WHERE id=?;
                """, (nombre.strip(), descripcion, float(precio), int(stock), producto_id))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando producto: {e}")
            return False

    def actualizar_stock(self, producto_id, nuevo_stock):
        try:
            self.cursor.execute(
                "UPDATE productos SET stock=? WHERE id=?;",
                (int(nuevo_stock), producto_id)
            )
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando stock: {e}")
            return False

    def borrar_producto(self, producto_id):
        try:
            self.cursor.execute("DELETE FROM productos WHERE id=?;", (producto_id,))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error borrando producto: {e}")
            return False

    # ─────────── USUARIOS ───────────
    def crear_usuario(self, username, password_hash):
        try:
            username = username.strip()
            if not username or not password_hash:
                return None
            self.cursor.execute("SELECT id FROM usuarios WHERE username=?;", (username,))
            if self.cursor.fetchone():
                return None
            self.cursor.execute(
                "INSERT INTO usuarios(username, password_hash) VALUES(?, ?);",
                (username, password_hash)
            )
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] No se pudo crear usuario: {e}")
            return None

    def obtener_usuario_por_username(self, username):
        try:
            self.cursor.execute("SELECT * FROM usuarios WHERE username=?;", (username.strip(),))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo usuario: {e}")
            return None

    # ─────────── PEDIDOS ───────────
    def crear_pedido(self, cliente_nombre, cliente_email, items):
        try:
            self.cursor.execute("BEGIN;")
            total = 0.0
            lineas = []

            for it in items:
                pid = int(it["producto_id"])
                qty = int(it["cantidad"])
                self.cursor.execute("SELECT id, precio, stock FROM productos WHERE id=?;", (pid,))
                p = self.cursor.fetchone()
                if not p:
                    raise ValueError(f"Producto {pid} no existe")
                if p["stock"] < qty:
                    raise ValueError(f"Stock insuficiente para producto {pid}")
                precio_unit = float(p["precio"])
                total += precio_unit * qty
                lineas.append((pid, qty, precio_unit))

            self.cursor.execute("""
                INSERT INTO pedidos(cliente_nombre, cliente_email, total)
                VALUES(?,?,?);
            """, (cliente_nombre.strip(), cliente_email, total))
            pedido_id = self.cursor.lastrowid

            for (pid, qty, precio_unit) in lineas:
                self.cursor.execute("""
                    INSERT INTO pedido_items(pedido_id, producto_id, cantidad, precio_unit)
                    VALUES(?,?,?,?);
                """, (pedido_id, pid, qty, precio_unit))

                # Descontar stock
                self.cursor.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id=?;",
                    (qty, pid)
                )
                # Auto-restablecimiento si llegó a 0
                self.cursor.execute(
                    "UPDATE productos SET stock = ? WHERE id=? AND stock = 0;",
                    (STOCK_INICIAL, pid)
                )

            self.con.commit()
            return pedido_id
        except Exception as e:
            self.con.rollback()
            print(f"[DB] Error creando pedido: {e}")
            return None

    def listar_pedidos(self):
        try:
            self.cursor.execute("""
                SELECT p.*, GROUP_CONCAT(pr.nombre, ', ') as productos_nombres
                FROM pedidos p
                LEFT JOIN pedido_items pi ON pi.pedido_id = p.id
                LEFT JOIN productos pr ON pr.id = pi.producto_id
                GROUP BY p.id
                ORDER BY p.id DESC;
            """)
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error listando pedidos: {e}")
            return []

    def obtener_pedido(self, pedido_id):
        try:
            self.cursor.execute("SELECT * FROM pedidos WHERE id=?;", (pedido_id,))
            pedido = self.cursor.fetchone()
            if not pedido:
                return None, []
            self.cursor.execute("""
                SELECT pi.*, pr.nombre as producto_nombre
                FROM pedido_items pi
                JOIN productos pr ON pr.id = pi.producto_id
                WHERE pi.pedido_id=?;
            """, (pedido_id,))
            items = self.cursor.fetchall()
            return pedido, items
        except Error as e:
            print(f"[DB] Error obteniendo pedido: {e}")
            return None, []

    def actualizar_estado_pedido(self, pedido_id, estado):
        try:
            self.cursor.execute(
                "UPDATE pedidos SET estado=? WHERE id=?;",
                (estado, pedido_id)
            )
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando estado pedido: {e}")
            return False

    def reporte_ventas_hoy(self):
        """Devuelve pedidos y totales del día actual."""
        try:
            self.cursor.execute("""
                SELECT p.id, p.cliente_nombre, p.cliente_email, p.total,
                       p.estado, p.creado_en,
                       GROUP_CONCAT(pr.nombre || ' x' || pi.cantidad, ' | ') as detalle
                FROM pedidos p
                LEFT JOIN pedido_items pi ON pi.pedido_id = p.id
                LEFT JOIN productos pr ON pr.id = pi.producto_id
                WHERE DATE(p.creado_en) = DATE('now')
                GROUP BY p.id
                ORDER BY p.id DESC;
            """)
            pedidos = self.cursor.fetchall()
            self.cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as total_dia
                FROM pedidos
                WHERE DATE(creado_en) = DATE('now');
            """)
            total_dia = self.cursor.fetchone()["total_dia"]
            return pedidos, total_dia
        except Error as e:
            print(f"[DB] Error reporte ventas: {e}")
            return [], 0.0

    # ─────────── AVISOS ───────────
    def crear_aviso(self, titulo, mensaje):
        try:
            self.cursor.execute(
                "INSERT INTO avisos(titulo, mensaje) VALUES(?,?);",
                (titulo.strip(), mensaje.strip())
            )
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] Error creando aviso: {e}")
            return None

    def listar_avisos(self, solo_activos=False):
        try:
            if solo_activos:
                self.cursor.execute("SELECT * FROM avisos WHERE activo=1 ORDER BY id DESC;")
            else:
                self.cursor.execute("SELECT * FROM avisos ORDER BY id DESC;")
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error listando avisos: {e}")
            return []

    def togglear_aviso(self, aviso_id):
        try:
            self.cursor.execute(
                "UPDATE avisos SET activo = 1 - activo WHERE id=?;",
                (aviso_id,)
            )
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error toggling aviso: {e}")
            return False

    def borrar_aviso(self, aviso_id):
        try:
            self.cursor.execute("DELETE FROM avisos WHERE id=?;", (aviso_id,))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error borrando aviso: {e}")
            return False

    # ─────────── SEMILLA ───────────
    def semilla_productos(self):
        """Crea 10 productos de ejemplo si la tabla está vacía."""
        try:
            self.cursor.execute("SELECT COUNT(*) as c FROM productos;")
            if self.cursor.fetchone()["c"] > 0:
                return

            productos = [
                ("Girasol Eterno",        "Girasol hecho a mano con listón de seda, ideal para regalar.",       199.0, 10, "Girasol.jpeg"),
                ("Ramo de Dalias",         "Hermoso ramo de dalias eternas en tonos rosados y blancos.",          350.0, 10, "Dalia.jpeg"),
                ("Flores Amarillas",       "Ramo de flores amarillas, símbolo de alegría y amistad.",             500.0, 10, "Amarillas.jpeg"),
                ("Rosa Roja Eterna",       "Rosa roja preservada que dura años sin perder su belleza.",           250.0, 10, "default.jpg"),
                ("Bouquet Primaveral",     "Arreglo con flores variadas de temporada en colores pastel.",         450.0, 10, "default.jpg"),
                ("Corona Floral",          "Corona decorativa de flores secas, perfecta para el hogar.",         380.0, 10, "default.jpg"),
                ("Caja de Rosas",          "Caja elegante con 6 rosas eternas en colores a elegir.",             600.0, 10, "default.jpg"),
                ("Arreglo en Canasta",     "Canasta de mimbre con flores frescas y verdes decorativos.",          420.0, 10, "default.jpg"),
                ("Centro de Mesa",         "Arreglo floral elegante ideal para bodas y eventos especiales.",      750.0, 10, "default.jpg"),
                ("Mini Suculentas x3",     "Set de 3 mini suculentas en macetas decorativas de cerámica.",        320.0, 10, "default.jpg"),
            ]
            for p in productos:
                self.crear_producto(*p)
        except Error as e:
            print(f"[DB] Error semilla: {e}")