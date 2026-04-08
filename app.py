# app.py
import os
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

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")
db.semilla_productos()


# ─── Helpers de sesión ────────────────────────────────────────────────────────
def is_admin():
    return session.get("admin", False)

def requires_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash("Acceso solo para administrador.")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

def current_user():
    return session.get("user")

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


# ─── Catálogo (público) ───────────────────────────────────────────────────────
@app.route("/")
def index():
    productos = db.listar_productos()
    avisos = db.listar_avisos(solo_activos=True)
    return render_template("index.html", productos=productos,
                           carrito=carrito_session(), avisos=avisos)

@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    p = db.obtener_producto(producto_id)
    if not p:
        return "Producto no encontrado", 404
    return render_template("producto.html", p=p, carrito=carrito_session())


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
    return render_template("carrito.html", items=items, total=total)

@app.route("/carrito/agregar", methods=["POST"])
@login_required
def carrito_agregar():
    pid = request.form.get("producto_id", type=int)
    qty = request.form.get("cantidad", type=int, default=1)
    p = db.obtener_producto(pid)
    if not p:
        flash("Producto no existe.")
        return redirect(url_for("index"))
    cart = carrito_session()
    cart[str(pid)] = int(cart.get(str(pid), 0)) + max(qty, 1)
    session["carrito"] = cart
    flash("Agregado al carrito.")
    return redirect(request.referrer or url_for("index"))

@app.route("/carrito/quitar", methods=["POST"])
@login_required
def carrito_quitar():
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Proporciona usuario y contraseña.")
            return redirect(url_for("login"))
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
    session.pop("user", None)
    flash("Sesión cerrada.")
    return redirect(url_for("index"))


# ─── Checkout ─────────────────────────────────────────────────────────────────
@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    nombre = request.form.get("nombre", "").strip()
    email  = request.form.get("email", "").strip() or None
    if not nombre:
        flash("Escribe tu nombre para continuar.")
        return redirect(url_for("carrito"))
    cart = carrito_session()
    if not cart:
        flash("Tu carrito está vacío.")
        return redirect(url_for("index"))
    items = [{"producto_id": int(pid), "cantidad": int(qty)} for pid, qty in cart.items()]
    pedido_id = db.crear_pedido(nombre, email, items)
    if not pedido_id:
        flash("No se pudo procesar el pedido (¿stock insuficiente?).")
        return redirect(url_for("carrito"))
    session["carrito"] = {}
    return render_template("checkout_ok.html", pedido_id=pedido_id)


# ─── Admin: auth ──────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "admin" and password == "BrilloEterno123":
            session["admin"] = True
            flash("Bienvenido admin")
            return redirect(url_for("admin_productos"))
        flash("Usuario o contraseña inválidos")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session["admin"] = False
    flash("Sesión cerrada")
    return redirect(url_for("index"))


# ─── Admin: productos ─────────────────────────────────────────────────────────
@app.route("/admin/productos")
@requires_admin
def admin_productos():
    productos = db.listar_productos()
    return render_template("admin_productos.html", productos=productos)

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@requires_admin
def admin_producto_nuevo():
    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio      = request.form.get("precio", type=float)
        stock       = request.form.get("stock", type=int)
        if not nombre or precio is None or stock is None:
            flash("Completa todos los campos")
            return redirect(url_for("admin_producto_nuevo"))
        imagen = "default.jpg"
        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename:
            if allowed_image_file(imagen_file.filename):
                filename = secure_filename(imagen_file.filename)
                nombre_archivo, extension = os.path.splitext(filename)
                destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                contador = 0
                while os.path.exists(destino):
                    contador += 1
                    filename = f"{nombre_archivo}_{contador}{extension}"
                    destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen_file.save(destino)
                imagen = filename
            else:
                flash("Formato de imagen no soportado. Se usará imagen por defecto.")
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
        nueva_imagen = None
        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename:
            if allowed_image_file(imagen_file.filename):
                filename = secure_filename(imagen_file.filename)
                nombre_archivo, extension = os.path.splitext(filename)
                destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                contador = 0
                while os.path.exists(destino):
                    contador += 1
                    filename = f"{nombre_archivo}_{contador}{extension}"
                    destino = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen_file.save(destino)
                nueva_imagen = filename
            else:
                flash("Formato de imagen no soportado. Se conservará la imagen actual.")
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
    success = db.borrar_producto(producto_id)
    flash("Producto eliminado" if success else "No se pudo eliminar el producto")
    return redirect(url_for("admin_productos"))

@app.route("/admin/producto/<int:producto_id>/stock", methods=["POST"])
@requires_admin
def admin_producto_stock(producto_id):
    """Actualizar stock de un producto directamente desde el panel."""
    nuevo_stock = request.form.get("stock", type=int)
    if nuevo_stock is None or nuevo_stock < 0:
        flash("Stock inválido.")
        return redirect(url_for("admin_productos"))
    success = db.actualizar_stock(producto_id, nuevo_stock)
    flash("Stock actualizado." if success else "Error actualizando stock.")
    return redirect(url_for("admin_productos"))


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
    avisos = db.listar_avisos()
    return render_template("admin_avisos.html", avisos=avisos)

@app.route("/admin/aviso/nuevo", methods=["POST"])
@requires_admin
def admin_aviso_nuevo():
    titulo  = request.form.get("titulo", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    if not titulo or not mensaje:
        flash("Completa título y mensaje.")
        return redirect(url_for("admin_avisos"))
    db.crear_aviso(titulo, mensaje)
    flash("Aviso publicado.")
    return redirect(url_for("admin_avisos"))

@app.route("/admin/aviso/<int:aviso_id>/toggle", methods=["POST"])
@requires_admin
def admin_aviso_toggle(aviso_id):
    db.togglear_aviso(aviso_id)
    return redirect(url_for("admin_avisos"))

@app.route("/admin/aviso/<int:aviso_id>/borrar", methods=["POST"])
@requires_admin
def admin_aviso_borrar(aviso_id):
    db.borrar_aviso(aviso_id)
    flash("Aviso eliminado.")
    return redirect(url_for("admin_avisos"))


# ─── Admin: reporte de ventas ─────────────────────────────────────────────────
@app.route("/admin/reporte")
@requires_admin
def admin_reporte():
    pedidos, total_dia = db.reporte_ventas_hoy()
    from datetime import date
    hoy = date.today().strftime("%d/%m/%Y")
    return render_template("admin_reporte.html", pedidos=pedidos,
                           total_dia=total_dia, hoy=hoy)


if __name__ == "__main__":
    app.run(debug=True)
    '''
    Instrucciones de ejecución:
        pip install flask
        py app.py
        Abrir: http://127.0.0.1:5000/
    '''