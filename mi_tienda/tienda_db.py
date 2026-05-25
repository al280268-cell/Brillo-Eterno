# tienda_db.py
# ==========================================
# IMPORTACIÓN DE LIBRERÍAS
# ==========================================
import os       # Para construir rutas de archivos
import sqlite3  # Para conectar con la base de datos SQLite
import hashlib  # Para encriptar contraseñas con SHA256
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
        # Abre la conexión hacia nuestra base de datos local SQLite3 (tienda.sqlite3).
        # Es el puente que permite a la aplicación leer y escribir los datos reales.
        try:
            self.con = sqlite3.connect(self.bd_path, check_same_thread=False)
            self.con.row_factory = sqlite3.Row
            self.cursor = self.con.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.con.commit()
        except Error as e:
            print(f"[DB] Error al conectar: {e}")

    def cerrar(self):
        # Cierra el puente con la base de datos de forma segura.
        # Es importante hacerlo para no dejar la memoria ocupada ni dañar el archivo.
        try:
            if self.con:
                self.con.close()
        except Error as e:
            print(f"[DB] Error al cerrar: {e}")

    def crear_tablas(self):
        # (SETUP INICIAL) Levanta toda la estructura de bases de datos desde cero si no existe.
        # Crea las tablas como: productos, administradores, pedidos, ventas y usuarios.
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

            # Tabla de gastos diarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos_diarios(
                    fecha DATE PRIMARY KEY,
                    monto REAL NOT NULL DEFAULT 0.0
                );
            """)

            self.con.commit()
        except Error as e:
            print(f"[DB] Error creando tablas: {e}")

    # ─────────── PRODUCTOS ───────────
    def crear_producto(self, nombre, descripcion, precio, stock, imagen="default.jpg"):
        # Inserta un nuevo producto. Devuelve el ID generado.
        # Para arreglar fallos: Revisar que precio y stock se conviertan bien a int/float.
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
        # Consulta (READ) múltiple: Trae absolutamente todos los productos a la tienda para mostrarlos en el Catálogo principal.
        try:
            self.cursor.execute("SELECT * FROM productos ORDER BY id DESC;")
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error listando productos: {e}")
            return []

    def obtener_producto(self, producto_id):
        # Consulta (READ) específica: Busca y te devuelve 1 solo producto exacto filtrando por su ID.
        try:
            self.cursor.execute("SELECT * FROM productos WHERE id=?;", (producto_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo producto: {e}")
            return None

    def actualizar_producto(self, producto_id, nombre, descripcion, precio, stock, imagen=None):
        # Modifica (UPDATE) los datos completos de una flor (su precio, stock, descripción) si el Admin se equivocó al crearla.
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
        # Modifica (UPDATE) exclusivamente el número del inventario. Útil cuando llegan nuevas flores físicas al local.
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
        # Elimina (DELETE) permanentemente la flor/producto de la Base de Datos.
        try:
            self.cursor.execute("DELETE FROM productos WHERE id=?;", (producto_id,))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error borrando producto: {e}")
            return False

    # ─────────── USUARIOS ───────────

    def encriptar_password(self, password):
        # Convierte la contraseña en un hash SHA256 (cadena de 64 caracteres hexadecimales).
        # SHA256 es un algoritmo de encriptación de una sola vía: no se puede revertir.
        # Esto protege las contraseñas en caso de que alguien acceda a la base de datos.
        return hashlib.sha256(password.encode()).hexdigest()

    def crear_usuario(self, username, password):
        # Registra un nuevo usuario en la base de datos.
        # La contraseña se encripta internamente con SHA256 antes de guardarla.
        # Retorna el ID del nuevo usuario, o None si el username ya existe.
        try:
            username = username.strip()
            if not username or not password:
                return None
            # Verificar si el usuario ya existe
            self.cursor.execute("SELECT id FROM usuarios WHERE username=?;", (username,))
            if self.cursor.fetchone():
                return None  # El usuario ya existe
            # Encriptar la contraseña antes de guardarla
            password_hash = self.encriptar_password(password)
            self.cursor.execute(
                "INSERT INTO usuarios(username, password_hash) VALUES(?, ?);",
                (username, password_hash)
            )
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] No se pudo crear usuario: {e}")
            return None

    def verificar_usuario(self, username, password):
        # Verifica si el usuario y contraseña son correctos.
        # Encripta la contraseña recibida y la compara con el hash guardado en la DB.
        # Retorna la fila del usuario si coincide, o None si no.
        try:
            password_hash = self.encriptar_password(password)
            self.cursor.execute(
                "SELECT * FROM usuarios WHERE username=? AND password_hash=?;",
                (username.strip(), password_hash)
            )
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error verificando usuario: {e}")
            return None

    def obtener_usuario_por_username(self, username):
        # Busca un cliente por su nombre de usuario en el login, para verificar si la cuenta existe.
        try:
            self.cursor.execute("SELECT * FROM usuarios WHERE username=?;", (username.strip(),))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo usuario: {e}")
            return None

    # ─────────── PEDIDOS ───────────
    def crear_pedido(self, cliente_nombre, cliente_email, items):
        # Procesa un pedido y, muy importante, DESCUENTA EL STOCK.
        # Si falla el stock o falta un producto, usar rollback() para cancelar todo.
        # Si queremos quitar lo de rebajar stock en automático, comentar las líneas UPDATE productos SET stock = stock - ?.
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

            self.con.commit()
            return pedido_id
        except Exception as e:
            self.con.rollback()
            print(f"[DB] Error creando pedido: {e}")
            return None

    def listar_pedidos(self):
        # Consulta (READ) Avanzada con JOIN: SQL no solo te trae las compras de la tabla 'pedidos',sino que simultáneamente las fusiona (LEFT JOIN) con la tabla de 'productos' y 'pedido_items'
        # para que en la interfaz visual puedas ver exactamente qué nombres de flores se compró (productos_nombres).
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
        # Consulta (READ) Detallada: Sirve para revisar un ticket individual de compra.
        # Primero busca "quién compró y cuánto gastó" (en `pedidos`), y después realiza una 
        # segunda consulta para "qué flores exactas se llevó en este ticket" (en `pedido_items`).
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
        # Modifica (UPDATE): Actualiza un pedido para indicar si el ramo ya fue "entregado" al domicilio o sigue "pendiente".
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
        """
        ==================== EXPLICACIÓN ====================
        MÉTODO: reporte_ventas_hoy
        Operación: Realiza 4 consultas SQL independientes para reunir KPIs:
        1. Lista de Pedidos del día y el desglose de productos (Usando LEFT JOIN).
        2. Total de Ingresos (SUM).
        3. Producto Estrella (El más vendido del día usando MAX/SUM y GROUP BY).
        4. Gastos Diarios operacionales de la sucursal.
        ====================================================================
        """
        try:
            # 1. Extraemos los pedidos completos que coincidan con la fecha de 'hoy'
            self.cursor.execute("""
                SELECT p.id, p.cliente_nombre, p.cliente_email, p.total,
                       p.estado, p.creado_en,
                       GROUP_CONCAT(pr.nombre || ' x' || pi.cantidad, ' | ') as detalle
                FROM pedidos p
                LEFT JOIN pedido_items pi ON pi.pedido_id = p.id
                LEFT JOIN productos pr ON pr.id = pi.producto_id
                WHERE DATE(p.creado_en) = DATE('now', 'localtime')
                GROUP BY p.id
                ORDER BY p.id DESC;
            """)
            pedidos = self.cursor.fetchall()
            
            # 2. Calculamos los Ingresos Brutos del día
            self.cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as total_dia
                FROM pedidos
                WHERE DATE(creado_en) = DATE('now', 'localtime');
            """)
            total_dia = self.cursor.fetchone()["total_dia"]

            # 3. EXTRA: Buscamos el "Producto Estrella" (El que más unidades vendió hoy)
            # ordenación ascendente/descendente (DESC).
            self.cursor.execute("""
                SELECT pr.nombre, SUM(pi.cantidad) as total_vendido
                FROM pedido_items pi
                JOIN pedidos p ON p.id = pi.pedido_id
                JOIN productos pr ON pr.id = pi.producto_id
                WHERE DATE(p.creado_en) = DATE('now', 'localtime')
                GROUP BY pr.id
                ORDER BY total_vendido DESC
                LIMIT 1;
            """)
            estrella_row = self.cursor.fetchone()
            producto_estrella = estrella_row["nombre"] if estrella_row else "Sin ventas hoy"

            # 4. Extraemos la cantidad de gastos registrados.
            self.cursor.execute("""
                SELECT monto FROM gastos_diarios
                WHERE fecha = DATE('now', 'localtime');
            """)
            row = self.cursor.fetchone()
            gastos = row["monto"] if row else 0.0

            return pedidos, total_dia, gastos, producto_estrella
        except Error as e:
            print(f"[DB] Error reporte ventas: {e}")
            return [], 0.0, 0.0, "N/A"

    def guardar_gastos_hoy(self, monto):
        """
        ==================== EXPLICACIÓN ====================
        MÉTODO: guardar_gastos_hoy (Modificador o Editor de Gastos)
        Propósito: Permite al administrador insertar o EDITAR (modificar)
                   los gastos operacionales del día.
        Explicación SQL: Se usa "ON CONFLICT(fecha) DO UPDATE". Esto significa
        que si ya existe una fila para HOY, SQLite no falla, sino que
        sobrescribe (UPDATE) el monto, logrando así actualizar/editar 
        los datos de la misma fila, cumpliendo con la capacidad de edición iterativa.
        ====================================================================
        """
        try:
            self.cursor.execute("""
                INSERT INTO gastos_diarios(fecha, monto)
                VALUES(DATE('now', 'localtime'), ?)
                ON CONFLICT(fecha) DO UPDATE SET monto=?;
            """, (float(monto), float(monto)))
            self.con.commit()
            return True
        except Error as e:
            print(f"[DB] Error guardando gastos: {e}")
            return False

    # ─────────── AVISOS ───────────
    def crear_aviso(self, titulo, mensaje):
        # Inserta (CREATE): Almacena físicamente el texto del banner de la tienda pública dentro de SQLite3.
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
        # Trae los avisos/banners. Si el parámetro `solo_activos` es True (como en el índice de la tienda),
        # sólo mostrará aquellos que el administrador no haya escondido (apagado mediante la variable `activo`).
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
        # Alteración directa (UPDATE Matemático): Su fórmula `1 - activo` significa:
        # Si el valor actual de Activo es 0: la fórmula hace 1 - 0 = 1 (Se enciende / Activa).
        # Si el valor actual es 1: la fórmula hace 1 - 1 = 0 (Se apaga / Oculta).
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
        # Acción Destructiva (DELETE): Elimina de raíz un aviso.
        try:
            self.cursor.execute("DELETE FROM avisos WHERE id=?;", (aviso_id,))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error borrando aviso: {e}")
            return False

    # ─────────── SEMILLA ───────────
    def semilla_productos(self):
        try:
            self.cursor.execute("SELECT COUNT(*) as c FROM productos;")
            if self.cursor.fetchone()["c"] > 0:
                return
            productos = [
                ("Girasol Eterno",  "Girasol eterno hecho a mano con listón de seda de alta calidad. Un detalle único y duradero, perfecto para regalar en cumpleaños, aniversarios o sorprender con un toque especial lleno de luz y alegría.",  199.0, 10, "Girasol.jpeg"),
                ("Ramo de Dalias", "Elegante ramo de dalias eternas en tonos rosados y blancos, ideal para regalar en ocasiones especiales. Diseño delicado y sofisticado que aporta belleza duradera a cualquier espacio.",   350.0, 10, "Dalia.jpeg"),
                ("Flores Amarillas", "Ramo de flores amarillas eternas que simbolizan alegría, amistad y energía positiva. Perfecto para regalar a esa persona especial o decorar espacios con un toque vibrante y lleno de vida.",  500.0, 10, "Amarillas.jpeg"),
                ("Caja Corazón", "Caja en forma de corazón con 10 rosas eternas y una dalia con corona decorativa. Un regalo romántico y exclusivo ideal para aniversarios, San Valentín o sorprender con un detalle inolvidable.",  500.0, 10, "cajacorazon.png"),
                ("Ramo Rosas Eternas", "Ramo de 21 rosas eternas rojas envueltas en elegante papel coreano. Un detalle premium que simboliza amor eterno, perfecto para ocasiones románticas y regalos especiales.", 650.0, 10, "Ramorosasrojas.jpg"),
                ("Ramo Clásico", "Ramo clásico de 8 rosas eternas acompañado de una flor estrella. Diseño elegante y versátil, ideal para regalar en cualquier ocasión y transmitir amor, gratitud o admiración.", 400.0, 10, "ramo_clasico.jpeg"),
                ("Rosa Individual", "Rosa eterna individual de gran tamaño, cuidadosamente envuelta en papel coreano. Un detalle sencillo pero significativo, perfecto para sorprender con un gesto romántico.", 120.0, 10, "rosa_individual.jpeg"),
                ("Caja Floral con Peluche", "Caja de madera decorativa con un tierno peluche y 16 flores eternas. El regalo perfecto para expresar amor y ternura en cumpleaños, aniversarios o fechas especiales.", 720.0, 10, "CajaFloral_peluche.jpeg"),
                ("Ramo Rosas Eternas", "Ramo de 22 rosas eternas envueltas en papel coreano de alta calidad. Diseño elegante y duradero que simboliza amor eterno, ideal para sorprender con un regalo inolvidable.", 750.0, 10, "Ramorosas.jpeg"),            
                ("Ramo de Flor de Loto", "Ramo de 7 flores de loto eternas, símbolo de pureza, paz y renovación. Perfecto para regalar o decorar espacios con un estilo único y armonioso.", 420.0, 10, "flordeloto.jpeg"),
            ]
            for p in productos:
                self.crear_producto(*p)
        except Error as e:
            print(f"[DB] Error semilla: {e}")