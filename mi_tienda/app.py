import os
import json
import urllib.request
import urllib.parse
import stripe
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from tienda_db import BaseDatosTienda
from functools import wraps

app = Flask(__name__)
app.secret_key = "cambia-esto-por-algo-seguro"

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'imagenes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ─── API STRIPE: Configuración de pagos ────────────────────────────────
# Las llaves de Stripe se cargan desde el archivo .env para seguridad
# En producción NUNCA se ponen las llaves directo en el código
import dotenv
try:
    dotenv.load_dotenv()   # Carga las variables del archivo .env
except Exception:
    pass
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')

# ─── Helpers y configuración ───────────────────────────────────────
# Aquí definimos tipos permitidos.
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
# Verifica si una imagen subida tiene un formato permitido.
# Si se rompe (ej. suben archivos no permitidos), verifica que el "filename" no venga vacío.
# Para cambiarlo: Agrega más formatos al SET ALLOWED_IMAGE_EXTENSIONS arriba.


db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")
db.semilla_productos()


# ─── API EXTERNA #1: Tipo de Cambio MXN → USD ────────────────────────────
def obtener_tipo_cambio_usd():
    """
    Consulta el tipo de cambio MXN a USD en tiempo real.
    Usa la API gratuita de open.er-api.com (no requiere API key).
    Retorna el valor de 1 MXN en USD, o None si falla.
    """
    try:
        url = 'https://open.er-api.com/v6/latest/MXN'
        req = urllib.request.Request(url, headers={'User-Agent': 'BrilloEterno/1.0'})
        with urllib.request.urlopen(req, timeout=5) as respuesta:
            datos = json.loads(respuesta.read().decode())
            return datos['rates']['USD']
    except Exception as e:
        print(f"[API] No se pudo obtener tipo de cambio: {e}")
        return None


# ─── API EXTERNA #2: Generador de Código QR ──────────────────────────────
def generar_url_qr(texto, tamano=200):
    """
    Genera una URL de imagen QR usando la API de goqr.me/qrserver.
    No requiere API key. El QR se genera en el servidor de la API.
    """
    texto_encoded = urllib.parse.quote(str(texto))
    return f"https://api.qrserver.com/v1/create-qr-code/?size={tamano}x{tamano}&data={texto_encoded}"



# ─── Helpers de sesión ────────────────────────────────────────────────────────
def is_admin():
    return session.get("admin", False)
    # Retorna True si en la sesión actual existe la llave "admin".
    # Para arreglar: Si siempre da falso, asegúrate que en login admin se declare session["admin"] = True

def requires_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash("Ingresa con tu cuenta de administrador para continuar.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper
    # Decorador que protege cualquier ruta si no eres administrador.
    # Si se rompe (bloquea todo): Verifica que el decorador siempre retorne f(*args, **kwargs).

def current_user():
    return session.get("user")
    #Función útil para saber en cualquier momento QUIÉN está conectado actualmente leyendo la Session temporal de Flask.

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Inicia sesión para acceder a esta página.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def carrito_session():
    if "carrito" not in session:
        session["carrito"] = {}
    return session["carrito"]

@app.context_processor
def inject_carrito_count():
    """Inyecta la cantidad total de items del carrito en TODAS las plantillas."""
    cart = session.get("carrito", {})
    total_items = sum(int(v) for v in cart.values())
    return dict(carrito_count=total_items)


# ─── Catálogo (público) ───────────────────────────────────────────────────────
@app.route("/")
def index():
    productos = db.listar_productos()
    avisos = db.listar_avisos(solo_activos=True)
    # API #1: Obtener tipo de cambio para mostrar precios en USD
    tipo_cambio = obtener_tipo_cambio_usd()
    return render_template("index.html", productos=productos, carrito=carrito_session(),
                           avisos=avisos, tipo_cambio=tipo_cambio)

@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    p = db.obtener_producto(producto_id)
    if not p:
        return "Producto no encontrado", 404
    return render_template("producto.html", p=p, carrito=carrito_session())
    # Carga la página de detalles de un solo producto.
    # Si arroja 404 por error, asegurarnos de que producto_id proviene como INT (entero) desde la base de datos.


# ─── Carrito ──────────────────────────────────────────────────────────────────
@app.route("/carrito")
@login_required
def carrito():
    cart = carrito_session()
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        p = db.obtener_producto(int(pid_str))
        if not p:
            continue
        subtotal = float(p["precio"]) * int(qty)
        total += subtotal
        items.append({"p": p, "qty": int(qty), "subtotal": subtotal})
        
    # Lógica de Fechas (Backend)
    # Aquí calculamos las fechas de entrega directamente en Python (Servidor).
    
    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    
    hoy = datetime.now()
    fecha_c = hoy
    agregados = 0
    
    # Bucle para Calcular "3 Días Hábiles" (Click & Collect)
    # Se suma un día al reloj, y si el valor devuelto por weekday() es menor a 5 
    # (es decir, de Lunes [0] a Viernes [4]), entonces sí cuenta como día válido.
    while agregados < 3:
        fecha_c += timedelta(days=1)
        if fecha_c.weekday() < 5:  
            agregados += 1
            
    # Calcular "2 Días Naturales" simples (Punto Medio)
    fecha_m = hoy + timedelta(days=2)
    
    # Formateo manual equivalente a toLocaleDateString() en español para inyectarlo directo a Jinja2
    fecha_click_str = f"{DIAS[fecha_c.weekday()]}, {fecha_c.day} de {MESES[fecha_c.month - 1]}"
    fecha_medio_str = f"{DIAS[fecha_m.weekday()]}, {fecha_m.day} de {MESES[fecha_m.month - 1]}"

    return render_template("carrito.html", items=items, total=total, fecha_click=fecha_click_str, fecha_medio=fecha_medio_str)
    # Muestra los productos guardados en memoria (sesión).
    # Para cambiar: Si queremos que el carrito no se borre al cerrar navegador, debes guardarlo en la Base de Datos.
    # Si se rompe (no carga nada): Verificar que carrito_session() retorne un dict válido.

@app.route("/carrito/agregar", methods=["POST"])
@login_required
def carrito_agregar():
    # Añade un ID de producto y su cantidad al Diccionario del carrito en Session Flask.
    pid = request.form.get("producto_id", type=int)
    qty = request.form.get("cantidad", type=int, default=1)
    p = db.obtener_producto(pid)
    if not p:
        flash("Producto no existe.")
        return redirect(url_for("index"))
    cart = carrito_session()
    current_qty = int(cart.get(str(pid), 0))
    requested_qty = max(qty, 1)

    if current_qty + requested_qty > p["stock"]:
        flash(f"No hay suficiente stock. Solamente quedan {p['stock']} disponibles de este producto.")
        return redirect(request.referrer.split('#')[0] + f'#producto-{pid}' if request.referrer else url_for("index") + f'#producto-{pid}')

    cart[str(pid)] = current_qty + requested_qty
    session["carrito"] = cart
    flash("Agregado al carrito.")
    return redirect(request.referrer.split('#')[0] + f'#producto-{pid}' if request.referrer else url_for("index") + f'#producto-{pid}')

@app.route("/carrito/quitar", methods=["POST"])
@login_required
def carrito_quitar():
    # Quita un elemento de la memoria del dict 'carrito'.
    pid = request.form.get("producto_id", type=int)
    cart = carrito_session()
    cart.pop(str(pid), None)
    session["carrito"] = cart
    return redirect(url_for("carrito"))


# ─── Auth usuarios ────────────────────────────────────────────────────────────
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Proporciona usuario y contraseña.")
            return redirect(url_for("registro"))
        password_hash = generate_password_hash(password)
        user_id = db.crear_usuario(username, password_hash)
        if not user_id:
            flash("Usuario ya existe o datos inválidos.")
            return redirect(url_for("registro"))
        session["user"] = {"id": user_id, "username": username}
        flash("Registro exitoso. Estás logueado.")
        return redirect(url_for("index"))
    return render_template("registro.html")
    # Crea un nuevo cliente.
    # Si se rompe (dice que el usuario ya existe pero no es así): Comprobar si password_hash recibe un dato válido.

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Proporciona usuario y contraseña.")
            return redirect(url_for("login"))
            
        # Lógica FUSIONADA: Si es admin, lo manda al panel de control de inmediato. Si no, sigue con el proceso normal de login.
        if username == "admin" and password == "BrilloEterno123":
            session["admin"] = True
            flash("Bienvenido al panel de control, Administrador.")
            return redirect(url_for("admin_productos"))
            
        user = db.obtener_usuario_por_username(username)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Usuario o contraseña inválidos.")
            return redirect(url_for("login"))
        session["user"] = {"id": user["id"], "username": user["username"]}
        flash("Has iniciado sesión.")
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    # Borra la key 'user' de la sesión del navegador.
    session.pop("user", None)
    flash("Sesión cerrada.")
    return redirect(url_for("index"))


# ─── Checkout con Stripe API ────────────────────────────────────────
@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """
    API STRIPE: Crea una sesión de pago con Stripe Checkout.
    El cliente es redirigido a la página segura de Stripe para ingresar
    sus datos de tarjeta. Stripe maneja toda la seguridad PCI.
    """
    nombre = request.form.get("nombre", "").strip()
    email  = request.form.get("email", "").strip() or None

    if not nombre:
        flash("Requerimos tu nombre completo.")
        return redirect(url_for("carrito"))

    cart = carrito_session()
    if not cart:
        flash("Tu carrito está vacío.")
        return redirect(url_for("index"))

    # Guardar datos del cliente en sesión para después del pago
    session["checkout_nombre"] = nombre
    session["checkout_email"] = email

    # Construir los line_items para Stripe (cada producto del carrito)
    line_items = []
    for pid_str, qty in cart.items():
        p = db.obtener_producto(int(pid_str))
        if not p:
            continue
        line_items.append({
            'price_data': {
                'currency': 'mxn',
                'product_data': {
                    'name': p['nombre'],
                    'description': (p['descripcion'] or '')[:200],
                },
                'unit_amount': int(float(p['precio']) * 100),  # Stripe usa centavos
            },
            'quantity': int(qty),
        })

    try:
        # Crear sesión de Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('checkout_exito', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('carrito', _external=True),
            customer_email=email,
        )
        # Redirigir al cliente a la página de pago de Stripe
        return redirect(checkout_session.url, code=303)
    except stripe.error.StripeError as e:
        flash(f"Error con Stripe: {str(e)}")
        return redirect(url_for("carrito"))


@app.route("/checkout/exito")
@login_required
def checkout_exito():
    """
    Callback de Stripe: Se ejecuta cuando el pago fue exitoso.
    Crea el pedido en nuestra BD y muestra la confirmación.
    """
    nombre = session.pop("checkout_nombre", "Cliente")
    email = session.pop("checkout_email", None)

    cart = carrito_session()
    if not cart:
        flash("Pedido ya procesado o carrito vacío.")
        return redirect(url_for("index"))

    items = [{"producto_id": int(pid), "cantidad": int(qty)} for pid, qty in cart.items()]
    pedido_id = db.crear_pedido(nombre, email, items)
    if not pedido_id:
        flash("No se pudo registrar el pedido (¿stock insuficiente?).")
        return redirect(url_for("carrito"))

    session["carrito"] = {}
    # API #2: Generar código QR con los datos del pedido
    qr_data = f"Pedido #{pedido_id} - Floreria Brillo Eterno - {nombre}"
    qr_url = generar_url_qr(qr_data)
    return render_template("checkout_ok.html", pedido_id=pedido_id, qr_url=qr_url)


# ─── Admin: logout ────────────────────────────────────────────────────────────
@app.route("/admin/logout")
def admin_logout():
    session["admin"] = False
    flash("Panel de administrador cerrado.")
    return redirect(url_for("index"))


# ─── Admin: productos ─────────────────────────────────────────────────────────
@app.route("/admin/productos")
@requires_admin
def admin_productos():
    productos = db.listar_productos()
    return render_template("admin_productos.html", productos=productos)
    # RUTA PRIVADA DE INVENTARIO (/admin/productos): Protegida por el decorador `@requires_admin`. Muestra el catálogo al Administrador en forma de tabla plana de listado.

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@requires_admin
def admin_producto_nuevo():
    # RUTA PRIVADA CREAR (/admin/producto/nuevo): Renderiza un formulario HTML vacío y espera a que el Administrador presione "Guardar".
    if request.method == "POST":
        # 1. OBTIENE LOS DATOS: Lee cada campo de texto del HTML. `type=float` convierte el texto del precio a números decimales de Python.
        nombre      = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio      = request.form.get("precio", type=float)
        stock       = request.form.get("stock", type=int)
        
        # 2. VALIDACIÓN: Obliga a que nombre, precio y stock existan.
        if not nombre or precio is None or stock is None:
            flash("Completa todos los campos")
            return redirect(url_for("admin_producto_nuevo"))
            
        # 3. MANEJO DE IMÁGENES: Por defecto le asigna 'default.jpg' por si el usuario no mandó foto.
        imagen = "default.jpg"
        imagen_file = request.files.get("imagen")
        
        if imagen_file and imagen_file.filename:
            # Verifica si la extensión es válida (ej: .jpg o .png)
            if allowed_image_file(imagen_file.filename):
                # secure_filename limpia caracteres raros o hackers del nombre del archivo (ejemplo: ../archivo.jpg)
                filename = secure_filename(imagen_file.filename)
                nombre_archivo, extension = os.path.splitext(filename)
                destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # BUCLE ANTICHOQUES: Si ya existe una flor llamada 'rosa.jpg', le suma un número para guardarla como 'rosa_1.jpg' y no sobrescribir la antigua.
                contador = 0
                while os.path.exists(destino):
                    contador += 1
                    filename = f"{nombre_archivo}_{contador}{extension}"
                    destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # Descarga la foto y la guarda permanentemente en la carpeta estática.
                imagen_file.save(destino)
                imagen = filename
            else:
                flash("Formato de imagen no soportado. Se usará imagen por defecto.")
        # 4. GUARDA EN BASE DE DATOS: Le envía todos los datos listos y el nombre de la foto a SQLite3.
        producto_id = db.crear_producto(nombre, descripcion, precio, stock, imagen)
        if producto_id:
            flash("Producto creado")
            return redirect(url_for("admin_productos"))
            
        flash("Error creando producto")
        return redirect(url_for("admin_producto_nuevo"))
        
    return render_template("admin_producto_nuevo.html")

@app.route("/admin/producto/<int:producto_id>/editar", methods=["GET", "POST"])
@requires_admin
def admin_producto_editar(producto_id):
    # RUTA PRIVADA EDITAR (/admin/producto/editar): Es un espejo casi gemelo de "crear", pero aquí ya sabemos el ID del producto a modificar.
    # Busca la flor específica para llenar los campos originalmente.
    p = db.obtener_producto(producto_id)
    if not p:
        flash("Producto no encontrado.")
        return redirect(url_for("admin_productos"))
        
    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio      = request.form.get("precio", type=float)
        stock       = request.form.get("stock", type=int)
        
        if not nombre or precio is None or stock is None:
            flash("Completa todos los campos.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
            
        # Si NO mandan una foto nueva, nueva_imagen se queda en 'None'. Esto le dirá a SQLite3 que ni toque la foto original que ya tenía.
        nueva_imagen = None
        imagen_file = request.files.get("imagen")
        
        # Si el usuario SÍ seleccionó un nuevo JPG/PNG...
        if imagen_file and imagen_file.filename:
            if allowed_image_file(imagen_file.filename):
                filename = secure_filename(imagen_file.filename)
                nombre_archivo, extension = os.path.splitext(filename)
                destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Bucle anticollisions para no borrar una foto de otra flor
                contador = 0
                while os.path.exists(destino):
                    contador += 1
                    filename = f"{nombre_archivo}_{contador}{extension}"
                    destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                imagen_file.save(destino)
                nueva_imagen = filename
            else:
                flash("Formato de imagen no soportado. Se conservará la imagen actual.")
                
        # Función 'actualizar_producto' la cual internamente decide: ¿Hubo foto? Modifica el campo imagen. ¿No hubo foto? Se brinca ese campo de SQL.
        success = db.actualizar_producto(producto_id, nombre, descripcion, precio, stock, nueva_imagen)
        if success:
            flash("Producto actualizado correctamente.")
            return redirect(url_for("admin_productos"))
            
        flash("Error al actualizar el producto.")
        return redirect(url_for("admin_producto_editar", producto_id=producto_id))
        
    return render_template("admin_producto_editar.html", p=p)

@app.route("/admin/producto/<int:producto_id>/borrar", methods=["POST"])
@requires_admin
def admin_producto_borrar(producto_id):
    # RUTA PRIVADA ELIMINAR: Protegida. Permite que el Administrador presione el botón rojo y ejecute la instrucción de borrado (DELETE FROM) en la Base de Datos mediante la función `borrar_producto()`.
    success = db.borrar_producto(producto_id)
    flash("Producto eliminado" if success else "No se pudo eliminar el producto")
    return redirect(url_for("admin_productos"))

@app.route("/admin/producto/<int:producto_id>/stock", methods=["POST"])
@requires_admin
def admin_producto_stock(producto_id):
    # RUTA ADMIN DE STOCK:
    # Recibe el nuevo valor introducido en la tabla dinámica del Administrador.
    nuevo_stock = request.form.get("stock", type=int)
    if nuevo_stock is None or nuevo_stock < 0:
        flash("Stock inválido.")
        # obligamos al navegador a que el redireccionamiento haga un auto-scroll hasta las coordenadas de la fila (tr id="item-5") recién modificada.
        return redirect(url_for("admin_productos") + f"#item-{producto_id}")
        
    # Ejecuta el UPDATE a la base de datos SQL
    success = db.actualizar_stock(producto_id, nuevo_stock)
    flash("Stock actualizado." if success else "Error al actualizar stock.")
    
    # Redireccionamiento con anclaje para experiencia de usuario fluida
    return redirect(url_for("admin_productos") + f"#item-{producto_id}")


# ─── Admin: pedidos ───────────────────────────────────────────────────────────
@app.route("/admin/pedidos")
@requires_admin
def admin_pedidos():
    pedidos = db.listar_pedidos()
    return render_template("admin_pedidos.html", pedidos=pedidos)

@app.route("/admin/pedidos/actualizar", methods=["POST"])
@requires_admin
def admin_pedidos_actualizar():
    """Actualiza los estados de múltiples pedidos via checkboxes."""
    # IDs que el admin marcó como 'entregado'
    ids_entregados = set(request.form.getlist("entregado"))
    todos_los_pedidos = db.listar_pedidos()
    for pedido in todos_los_pedidos:
        nuevo_estado = "entregado" if str(pedido["id"]) in ids_entregados else "pendiente"
        db.actualizar_estado_pedido(pedido["id"], nuevo_estado)
    flash("Pedidos actualizados.")
    return redirect(url_for("admin_pedidos"))


# ─── Admin: avisos ────────────────────────────────────────────────────────────
@app.route("/admin/avisos")
@requires_admin
def admin_avisos():
    # RUTA PRIVADA AVISOS (/admin/avisos): Pantalla central del Administrador donde puede ver todos los mensajitos creados.
    # Solicita a SQLite3 (listar_avisos) que devuelva la tabla completa, incluso aquellos que estén "apagados".
    avisos = db.listar_avisos()
    return render_template("admin_avisos.html", avisos=avisos)

@app.route("/admin/aviso/nuevo", methods=["POST"])
@requires_admin
def admin_aviso_nuevo():
    # RUTA CREAR AVISO: Recibe las palabras del formulario (Título y Mensaje).
    titulo  = request.form.get("titulo", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    
    # 1. Validación de seguridad básica: si dejaron un espacio en blanco, aborta la subida.
    if not titulo or not mensaje:
        flash("Completa título y mensaje.")
        return redirect(url_for("admin_avisos"))
    
    # 2. Si todo está correcto, empuja el texto hacia SQLite3 llamando al comando interno (INSERT INTO).
    db.crear_aviso(titulo, mensaje)
    flash("Aviso publicado.")
    return redirect(url_for("admin_avisos"))

@app.route("/admin/aviso/<int:aviso_id>/toggle", methods=["POST"])
@requires_admin
def admin_aviso_toggle(aviso_id):
    # Si un aviso dice 'activo=True', esta función entra a la Base de Datos y lo cambia a 'False' (para ocultarlo del público).
    # Si dice 'False', lo vuelve 'True'. Es un simple interruptor de encendido/apagado para mostrar u ocultar el aviso sin borrarlo.
    db.togglear_aviso(aviso_id)
    return redirect(url_for("admin_avisos"))

@app.route("/admin/aviso/<int:aviso_id>/borrar", methods=["POST"])
@requires_admin
def admin_aviso_borrar(aviso_id):
    # RUTA DE ELIMINACIÓN PERMANENTE: Ejecuta una instrucción destructiva de borrado (DELETE FROM avisos).
    db.borrar_aviso(aviso_id)
    flash("Aviso eliminado.")
    return redirect(url_for("admin_avisos"))


# ─── Admin: reporte de ventas ─────────────────────────────────────────────────
@app.route("/admin/reporte")
@requires_admin
def admin_reporte():
    """
    ====================EXPLICACIÓN ====================
    Ruta: /admin/reporte
    Propósito: Controlador de la Vista de Reporte Financiero.
    Explicación:
    1. Llama a la Base de Datos para pedir múltiples variables mediante desempaquetado de tuplas (pedidos, total_dia, gastos, producto_estrella).
    2. Realiza operaciones lógico-matemáticas en el Servidor (Cálculo de Ganancia Neta y Ticket Promedio) antes de mandarlo a la vista HTML. Esto evita sobrecargar la Base de Datos con matemáticas que el CPU puede hacer más rápido.
    ====================================================================
    """
    pedidos, total_dia, gastos, producto_estrella = db.reporte_ventas_hoy()
    
    # Cálculos financieros (Business Logic)
    ganancia = total_dia - gastos
    ticket_promedio = total_dia / len(pedidos) if pedidos and len(pedidos) > 0 else 0.0
    
    from datetime import date
    hoy = date.today().strftime("%d/%m/%Y")
    
    # Renderizamos la plantilla inyectando nuestros KPIs
    return render_template("admin_reporte.html", 
                           pedidos=pedidos, 
                           total_dia=total_dia, 
                           gastos=gastos, 
                           ganancia=ganancia, 
                           producto_estrella=producto_estrella,
                           ticket_promedio=ticket_promedio,
                           hoy=hoy)

@app.route("/admin/reporte/gastos", methods=["POST"])
@requires_admin
def admin_reporte_gastos():
    """
    ==================== EXPLICACIÓN ====================
    Ruta: /admin/reporte/gastos (POST)
    Propósito: Procesar la EDICIÓN del formulario de gastos operativos.
    Explicación: Captura lo que el usuario escribió por POST y lo manda a
    la base de datos para sobrescribir (editar) el gasto actual.
    ====================================================================
    """
    monto = request.form.get("gastos", type=float)
    if monto is not None and monto >= 0:
        db.guardar_gastos_hoy(monto)
        flash("Gastos actualizados/modificados exitosamente.")
    else:
        flash("Monto de gastos inválido.")
    return redirect(url_for("admin_reporte"))


if __name__ == "__main__":
    app.run(debug=True)
    # Instrucciones de ejecución:
    # pip install flask
    # py app.py
    # Abrir: http://127.0.0.1:5000/