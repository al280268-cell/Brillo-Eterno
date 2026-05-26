# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  app.py — Aplicación de Escritorio para Florería Brillo Eterno             ║
# ║  Proyecto Académico · Tkinter + PIL · Python 3                             ║
# ║  Todas las operaciones de BD se delegan a tienda_db.py (BaseDatosTienda)   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ─── Importaciones de la Biblioteca Estándar de Python ────────────────────────
import tkinter as tk                         # Módulo principal de interfaz gráfica
from tkinter import ttk, messagebox          # Widgets temáticos y diálogos
import hashlib                               # Para encriptar contraseñas con SHA-256
from datetime import datetime, timedelta, date  # Manejo de fechas y cálculo de entregas
import os                                    # Para obtener la ruta del archivo actual
import sys                                   # Para información del sistema operativo

# ─── Importación de PIL (Pillow) para cargar imágenes ─────────────────────────
from PIL import Image, ImageTk               # Permite cargar JPG/PNG y mostrar en Tkinter

# ─── Importación de la Capa de Base de Datos ──────────────────────────────────
from tienda_db import BaseDatosTienda        # Clase que encapsula todas las consultas SQL

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES — Extraída del SCSS original del sitio web
# ═══════════════════════════════════════════════════════════════════════════════
ROJO = '#9a1e3f'            # Color primario burdeos (botones, encabezados)
ROJO_HOVER = '#7b1832'      # Burdeos oscuro al pasar el ratón sobre botones
ROJO_DARK = '#4f0f18'       # Burdeos muy oscuro (barra de navegación admin)
BLANCO = '#ffffff'           # Blanco puro para fondos de tarjetas
FONDO = '#fcf9f8'            # Blanco cálido para fondo general de la ventana
TEXTO = '#2b2123'            # Color oscuro para texto principal legible
TEXTO_SUAVE = '#6b5a5d'      # Gris suave para texto secundario
BORDE = '#e8dcdb'            # Color suave para bordes de tarjetas
VERDE = '#2e7d32'            # Verde para stock disponible / pedido entregado
NARANJA = '#e65100'          # Naranja para stock bajo / pedido pendiente
ROJO_STOCK = '#c62828'       # Rojo intenso para producto agotado
AMARILLO_AVISO = '#fff3cd'   # Fondo amarillo claro para banners de avisos
BORDE_AVISO = '#ffc107'      # Borde amarillo dorado para avisos
SOMBRA = '#d4c8c6'           # Color para efecto de sombra en tarjetas

# ═══════════════════════════════════════════════════════════════════════════════
# CREDENCIALES FIJAS DEL ADMINISTRADOR
# ═══════════════════════════════════════════════════════════════════════════════
ADMIN_USER = 'admin'
ADMIN_PASS = 'BrilloEterno123'

# ═══════════════════════════════════════════════════════════════════════════════
# DICCIONARIOS DE NOMBRES EN ESPAÑOL PARA FECHAS
# ═══════════════════════════════════════════════════════════════════════════════
DIAS_SEMANA = ['lunes', 'martes', 'miércoles', 'jueves',
               'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo',
         'junio', 'julio', 'agosto', 'septiembre',
         'octubre', 'noviembre', 'diciembre']

# ═══════════════════════════════════════════════════════════════════════════════
# RUTA GLOBAL DE IMÁGENES
# ═══════════════════════════════════════════════════════════════════════════════
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))  # Directorio de app.py
RUTA_IMAGENES = os.path.join(RUTA_BASE, 'static', 'imagenes')  # Carpeta de imágenes


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════
def hash_password(password):
    """Genera un hash SHA-256 de la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verificar_password(password, password_hash):
    """Compara la contraseña ingresada con el hash almacenado."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == password_hash


def formato_fecha_espanol(fecha):
    """Convierte un datetime a formato legible en español."""
    dia_nombre = DIAS_SEMANA[fecha.weekday()]
    mes_nombre = MESES[fecha.month - 1]
    return f"{dia_nombre}, {fecha.day} de {mes_nombre}"


def calcular_dias_habiles(dias):
    """Calcula una fecha futura saltando fines de semana."""
    fecha = datetime.now()
    agregados = 0
    while agregados < dias:
        fecha += timedelta(days=1)
        if fecha.weekday() < 5:       # Lunes a viernes = días hábiles
            agregados += 1
    return fecha


def formato_precio(valor):
    """Formatea un valor numérico como precio en pesos mexicanos."""
    return f"${valor:,.2f}"


def cargar_imagen(nombre_archivo, ancho, alto):
    """Carga una imagen desde la carpeta static/imagenes y la redimensiona.
    Retorna un ImageTk.PhotoImage o None si no se encuentra el archivo."""
    if not nombre_archivo:
        return None
    # Intentar cargar la imagen con el nombre exacto
    ruta = os.path.join(RUTA_IMAGENES, nombre_archivo)
    if not os.path.exists(ruta):
        # Intentar buscar ignorando mayúsculas/minúsculas
        try:
            archivos = os.listdir(RUTA_IMAGENES)
            nombre_lower = nombre_archivo.lower()
            for f in archivos:
                if f.lower() == nombre_lower:
                    ruta = os.path.join(RUTA_IMAGENES, f)
                    break
            else:
                return None  # No se encontró ninguna coincidencia
        except Exception:
            return None
    try:
        img = Image.open(ruta)                    # Abre la imagen con PIL
        img = img.resize((ancho, alto), Image.LANCZOS)  # Redimensiona con alta calidad
        return ImageTk.PhotoImage(img)            # Convierte a formato Tkinter
    except Exception:
        return None


def crear_boton(parent, text, bg, fg, font_tuple, command, **kwargs):
    """Crea un botón con efecto hover (cambio de color al pasar el mouse)."""
    btn = tk.Button(parent, text=text, bg=bg, fg=fg, font=font_tuple,
                    relief='flat', cursor='hand2', command=command,
                    activebackground=bg, activeforeground=fg,
                    bd=0, **kwargs)
    # Calcular color hover (más oscuro)
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
        hover = f'#{max(r-25,0):02x}{max(g-25,0):02x}{max(b-25,0):02x}'
    except Exception:
        hover = bg
    btn.bind('<Enter>', lambda e: btn.config(bg=hover))    # Mouse entra → oscurece
    btn.bind('<Leave>', lambda e: btn.config(bg=bg))       # Mouse sale → color original
    return btn


def crear_tarjeta_con_sombra(parent, ancho=None, alto=None, **kwargs):
    """Crea un frame con efecto de sombra suave usando frames anidados."""
    # Frame externo (sombra)
    sombra = tk.Frame(parent, bg=SOMBRA, **kwargs)
    # Frame interno (tarjeta blanca) con offset de 3px
    tarjeta = tk.Frame(sombra, bg=BLANCO, bd=0, relief='flat')
    tarjeta.pack(padx=(0, 3), pady=(0, 3), fill='both', expand=True)
    return sombra, tarjeta


def crear_footer(parent):
    """Crea un pie de página elegante en la parte inferior de la ventana.
    Se debe llamar ANTES de crear el contenido principal para que quede abajo."""
    footer = tk.Frame(parent, bg=ROJO_DARK, height=32)
    footer.pack(side=tk.BOTTOM, fill=tk.X)           # Se pega al fondo
    footer.pack_propagate(False)                       # Mantiene su altura fija
    tk.Label(footer,
             text='© 2026 Florería Brillo Eterno  ·  Hecho con 🌹 amor en Python  ·  Parcial 3',
             font=('Helvetica', 8), fg='#d4a0ab', bg=ROJO_DARK
             ).pack(expand=True)                       # Texto centrado


# ═══════════════════════════════════════════════════════════════════════════════
# ESTILOS GLOBALES TTK
# ═══════════════════════════════════════════════════════════════════════════════
def configurar_estilos():
    """Configura los estilos globales de ttk para toda la aplicación."""
    estilo = ttk.Style()
    estilo.theme_use('clam')  # Tema base más moderno

    # Treeview general
    estilo.configure('Custom.Treeview',
                     font=('Helvetica', 10),
                     rowheight=32,
                     background=BLANCO,
                     fieldbackground=BLANCO,
                     foreground=TEXTO)
    estilo.configure('Custom.Treeview.Heading',
                     font=('Helvetica', 10, 'bold'),
                     background=ROJO,
                     foreground=BLANCO,
                     relief='flat')
    estilo.map('Custom.Treeview.Heading',
               background=[('active', ROJO_HOVER)])
    estilo.map('Custom.Treeview',
               background=[('selected', '#f8e0e6')],
               foreground=[('selected', TEXTO)])

    # Scrollbar
    estilo.configure('Custom.Vertical.TScrollbar',
                     background=BORDE,
                     troughcolor=FONDO,
                     arrowcolor=ROJO)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL — CONTROLADOR DE LA APLICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
class AplicacionTienda:
    """Controlador central. Gestiona navegación, estado y conexión a BD."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Florería Brillo Eterno')
        self.root.geometry('960x700')
        self.root.minsize(850, 620)
        self.root.configure(bg=FONDO)

        # Configurar estilos ttk globales
        configurar_estilos()

        # Conexión a la Base de Datos
        self.db = BaseDatosTienda(ruta=RUTA_BASE, bd='tienda.sqlite3')
        self.db.semilla_productos()       # Datos iniciales si la BD está vacía

        # Estado Global
        self.usuario_actual = None        # Dict del usuario logueado o None
        self.es_admin = False             # True si es administrador
        self.carrito = {}                 # {producto_id: cantidad}
        self.frame_actual = None          # Frame visible actualmente

        # Pantalla inicial
        self.mostrar(VentanaLogin)

    def mostrar(self, FrameClass, **kwargs):
        """Destruye el frame actual y muestra uno nuevo."""
        if self.frame_actual is not None:
            self.frame_actual.destroy()
        self.frame_actual = FrameClass(self.root, self, **kwargs)
        self.frame_actual.pack(fill=tk.BOTH, expand=True)

    def cerrar_sesion(self):
        """Cierra la sesión actual y regresa al Login."""
        self.usuario_actual = None
        self.es_admin = False
        self.carrito = {}
        self.mostrar(VentanaLogin)

    def contar_carrito(self):
        """Retorna la cantidad total de artículos en el carrito."""
        return sum(self.carrito.values())

    def ejecutar(self):
        """Inicia el bucle principal de Tkinter."""
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 1 — VENTANA DE LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaLogin(tk.Frame):
    """Pantalla de bienvenida con acceso Cliente o Administrador."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self._imgs = []   # Lista para evitar garbage collection de imágenes
        crear_footer(self)  # Pie de página (se empaqueta abajo primero)

        # ─── Tarjeta con sombra centrada ──────────────────────────────────
        sombra, tarjeta = crear_tarjeta_con_sombra(self)
        sombra.place(relx=0.5, rely=0.5, anchor='center', width=460, height=580)

        # ─── Logo de la tienda ────────────────────────────────────────────
        logo = cargar_imagen('minifoto.png', 80, 80)
        if logo:
            self._imgs.append(logo)
            tk.Label(tarjeta, image=logo, bg=BLANCO).pack(pady=(20, 5))
        else:
            tk.Label(tarjeta, text='🌹', font=('Helvetica', 40),
                     bg=BLANCO).pack(pady=(20, 5))

        # ─── Título ──────────────────────────────────────────────────────
        tk.Label(tarjeta, text='Florería Brillo Eterno',
                 font=('Georgia', 18, 'bold'), fg=ROJO, bg=BLANCO
                 ).pack(pady=(0, 2))
        tk.Label(tarjeta, text='Bienvenido de vuelta',
                 font=('Helvetica', 11), fg=TEXTO_SUAVE, bg=BLANCO
                 ).pack(pady=(0, 5))

        # ─── Línea decorativa ─────────────────────────────────────────────
        tk.Frame(tarjeta, bg=ROJO, height=2, width=60).pack(pady=(0, 12))

        # ─── Selector Cliente / Admin (botones estilizados) ───────────────
        self.tipo_var = tk.StringVar(value='cliente')
        frame_tabs = tk.Frame(tarjeta, bg=BORDE)
        frame_tabs.pack(padx=40, fill=tk.X)

        self.btn_tab_cliente = tk.Button(frame_tabs, text='👤  Cliente',
            font=('Helvetica', 10, 'bold'), relief='flat', cursor='hand2',
            bg=ROJO, fg=BLANCO, bd=0,
            command=lambda: self._seleccionar_tab('cliente'))
        self.btn_tab_cliente.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6)

        self.btn_tab_admin = tk.Button(frame_tabs, text='🔧  Administrador',
            font=('Helvetica', 10, 'bold'), relief='flat', cursor='hand2',
            bg=FONDO, fg=TEXTO, bd=0,
            command=lambda: self._seleccionar_tab('admin'))
        self.btn_tab_admin.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6)

        # ─── Frame dinámico del formulario ────────────────────────────────
        self.form_frame = tk.Frame(tarjeta, bg=BLANCO)
        self.form_frame.pack(fill=tk.X, padx=40, pady=(15, 5))

        # ─── Label de errores ─────────────────────────────────────────────
        self.lbl_error = tk.Label(tarjeta, text='', fg=ROJO_STOCK,
                                   bg=BLANCO, font=('Helvetica', 9), wraplength=380)
        self.lbl_error.pack(pady=(5, 3))

        # ─── Enlace para registrarse ──────────────────────────────────────
        enlace = tk.Label(tarjeta, text='¿No tienes cuenta? Regístrate aquí',
                          fg=ROJO, bg=BLANCO, font=('Helvetica', 9, 'underline'),
                          cursor='hand2')
        enlace.pack(pady=(3, 15))
        enlace.bind('<Button-1>', lambda e: self.app.mostrar(VentanaRegistro))

        # ─── Construir formulario inicial ─────────────────────────────────
        self._construir_form_cliente()

    def _seleccionar_tab(self, tipo):
        """Cambia entre las pestañas de Cliente y Admin."""
        self.tipo_var.set(tipo)
        self.lbl_error.config(text='')
        if tipo == 'cliente':
            self.btn_tab_cliente.config(bg=ROJO, fg=BLANCO)
            self.btn_tab_admin.config(bg=FONDO, fg=TEXTO)
            for w in self.form_frame.winfo_children(): w.destroy()
            self._construir_form_cliente()
        else:
            self.btn_tab_admin.config(bg=ROJO_DARK, fg=BLANCO)
            self.btn_tab_cliente.config(bg=FONDO, fg=TEXTO)
            for w in self.form_frame.winfo_children(): w.destroy()
            self._construir_form_admin()

    def _crear_entry(self, parent, placeholder, show=None):
        """Crea un Entry con focus highlight y placeholder visual."""
        entry = tk.Entry(parent, font=('Helvetica', 12), relief='solid', bd=1,
                         fg=TEXTO, bg=BLANCO, insertbackground=ROJO)
        if show:
            entry.config(show=show)
        entry.pack(fill=tk.X, ipady=7, pady=(0, 4))
        # Efecto de focus: borde rojo al enfocar
        entry.bind('<FocusIn>', lambda e: entry.config(highlightcolor=ROJO,
                   highlightbackground=ROJO, highlightthickness=1))
        entry.bind('<FocusOut>', lambda e: entry.config(highlightthickness=0))
        return entry

    def _construir_form_cliente(self):
        """Campos para iniciar sesión como cliente."""
        tk.Label(self.form_frame, text='USUARIO', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(8, 2))
        self.entry_user = self._crear_entry(self.form_frame, 'Tu usuario')

        tk.Label(self.form_frame, text='CONTRASEÑA', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(6, 2))
        self.entry_pass = self._crear_entry(self.form_frame, '', show='•')

        # Checkbox mostrar contraseña
        self.show_pass = tk.BooleanVar()
        tk.Checkbutton(self.form_frame, text='Mostrar contraseña',
                       variable=self.show_pass, bg=BLANCO, fg=TEXTO_SUAVE,
                       font=('Helvetica', 8), selectcolor=BLANCO, bd=0,
                       command=lambda: self.entry_pass.config(
                           show='' if self.show_pass.get() else '•')
                       ).pack(anchor='w', pady=(2, 8))

        btn = crear_boton(self.form_frame, 'Entrar como Cliente',
                          ROJO, BLANCO, ('Helvetica', 11, 'bold'),
                          self._login_cliente)
        btn.pack(fill=tk.X, ipady=8)
        self.entry_pass.bind('<Return>', lambda e: self._login_cliente())

    def _construir_form_admin(self):
        """Campos para iniciar sesión como administrador."""
        tk.Label(self.form_frame, text='USUARIO', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(8, 2))
        self.entry_admin_user = tk.Entry(self.form_frame, font=('Helvetica', 12),
                                          relief='solid', bd=1)
        self.entry_admin_user.insert(0, 'admin')
        self.entry_admin_user.config(state='readonly')
        self.entry_admin_user.pack(fill=tk.X, ipady=7, pady=(0, 4))

        tk.Label(self.form_frame, text='CONTRASEÑA', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(6, 2))
        self.entry_admin_pass = self._crear_entry(self.form_frame, '', show='•')

        # Checkbox mostrar contraseña
        self.show_pass_admin = tk.BooleanVar()
        tk.Checkbutton(self.form_frame, text='Mostrar contraseña',
                       variable=self.show_pass_admin, bg=BLANCO, fg=TEXTO_SUAVE,
                       font=('Helvetica', 8), selectcolor=BLANCO, bd=0,
                       command=lambda: self.entry_admin_pass.config(
                           show='' if self.show_pass_admin.get() else '•')
                       ).pack(anchor='w', pady=(2, 8))

        btn = crear_boton(self.form_frame, 'Entrar al Panel Admin',
                          ROJO_DARK, BLANCO, ('Helvetica', 11, 'bold'),
                          self._login_admin)
        btn.pack(fill=tk.X, ipady=8)
        self.entry_admin_pass.bind('<Return>', lambda e: self._login_admin())

    def _login_cliente(self):
        """Verifica credenciales del cliente contra la BD."""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username or not password:
            self.lbl_error.config(text='Por favor completa todos los campos.')
            return
        try:
            usuario = self.app.db.verificar_usuario(username, password)
            if not usuario:
                self.lbl_error.config(text='Usuario o contraseña inválidos.')
                return
            self.app.usuario_actual = {'id': usuario['id'], 'username': usuario['username']}
            self.app.es_admin = False
            self.app.mostrar(VentanaCatalogo)
        except Exception as e:
            self.lbl_error.config(text=f'Error: {e}')

    def _login_admin(self):
        """Verifica credenciales del administrador contra constantes fijas."""
        password = self.entry_admin_pass.get().strip()
        if not password:
            self.lbl_error.config(text='Ingresa la contraseña de administrador.')
            return
        if password == ADMIN_PASS:
            self.app.es_admin = True
            self.app.usuario_actual = {'id': 0, 'username': 'admin'}
            self.app.mostrar(VentanaAdminProductos)
        else:
            self.lbl_error.config(text='Contraseña de administrador incorrecta.')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 2 — VENTANA DE REGISTRO
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaRegistro(tk.Frame):
    """Formulario para crear una nueva cuenta de cliente."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self._imgs = []
        crear_footer(self)  # Pie de página

        sombra, tarjeta = crear_tarjeta_con_sombra(self)
        sombra.place(relx=0.5, rely=0.5, anchor='center', width=440, height=480)

        # Logo
        logo = cargar_imagen('minifoto.png', 60, 60)
        if logo:
            self._imgs.append(logo)
            tk.Label(tarjeta, image=logo, bg=BLANCO).pack(pady=(20, 5))
        else:
            tk.Label(tarjeta, text='🌸', font=('Helvetica', 30), bg=BLANCO).pack(pady=(20, 5))

        tk.Label(tarjeta, text='Crear cuenta', font=('Georgia', 18, 'bold'),
                 fg=ROJO, bg=BLANCO).pack(pady=(0, 2))
        tk.Label(tarjeta, text='Únete a Florería Brillo Eterno',
                 font=('Helvetica', 10), fg=TEXTO_SUAVE, bg=BLANCO).pack(pady=(0, 5))
        tk.Frame(tarjeta, bg=ROJO, height=2, width=50).pack(pady=(0, 10))

        form = tk.Frame(tarjeta, bg=BLANCO)
        form.pack(fill=tk.X, padx=40)

        tk.Label(form, text='USUARIO', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(8, 2))
        self.entry_user = tk.Entry(form, font=('Helvetica', 12), relief='solid', bd=1)
        self.entry_user.pack(fill=tk.X, ipady=7)

        tk.Label(form, text='CONTRASEÑA', font=('Helvetica', 9, 'bold'),
                 bg=BLANCO, fg=TEXTO_SUAVE).pack(anchor='w', pady=(10, 2))
        self.entry_pass = tk.Entry(form, font=('Helvetica', 12), relief='solid',
                                    bd=1, show='•')
        self.entry_pass.pack(fill=tk.X, ipady=7)

        btn = crear_boton(form, 'Registrar', ROJO, BLANCO,
                          ('Helvetica', 11, 'bold'), self._registrar)
        btn.pack(fill=tk.X, ipady=8, pady=(15, 5))
        self.entry_pass.bind('<Return>', lambda e: self._registrar())

        self.lbl_error = tk.Label(tarjeta, text='', fg=ROJO_STOCK,
                                   bg=BLANCO, font=('Helvetica', 9), wraplength=360)
        self.lbl_error.pack(pady=(5, 3))

        enlace = tk.Label(tarjeta, text='¿Ya tienes cuenta? Inicia sesión',
                          fg=ROJO, bg=BLANCO, font=('Helvetica', 9, 'underline'),
                          cursor='hand2')
        enlace.pack(pady=(3, 15))
        enlace.bind('<Button-1>', lambda e: self.app.mostrar(VentanaLogin))

    def _registrar(self):
        """Crea un nuevo usuario en la BD."""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username or not password:
            self.lbl_error.config(text='Completa todos los campos.')
            return
        if len(password) < 4:
            self.lbl_error.config(text='La contraseña debe tener al menos 4 caracteres.')
            return
        try:
            user_id = self.app.db.crear_usuario(username, password)
            if not user_id:
                self.lbl_error.config(text='Ese nombre de usuario ya está en uso.')
                return
            self.app.usuario_actual = {'id': user_id, 'username': username}
            self.app.es_admin = False
            messagebox.showinfo('¡Bienvenido!', f'Cuenta creada exitosamente.\n¡Hola {username}!')
            self.app.mostrar(VentanaCatalogo)
        except Exception as e:
            self.lbl_error.config(text=f'Error al registrar: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 3 — CATÁLOGO DE PRODUCTOS (CON IMÁGENES)
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaCatalogo(tk.Frame):
    """Catálogo principal con tarjetas de productos con imágenes."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self._imgs = []       # Referencias a imágenes para evitar GC
        crear_footer(self)  # Pie de página
        self._construir_barra_superior()
        self._mostrar_avisos()
        self._construir_catalogo()

    def _construir_barra_superior(self):
        """Barra superior elegante con logo, usuario y carrito."""
        barra = tk.Frame(self, bg=ROJO, height=55)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)

        # Logo y nombre
        frame_logo = tk.Frame(barra, bg=ROJO)
        frame_logo.pack(side=tk.LEFT, padx=15)
        logo = cargar_imagen('minifoto.png', 35, 35)
        if logo:
            self._imgs.append(logo)
            tk.Label(frame_logo, image=logo, bg=ROJO).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(frame_logo, text='Florería Brillo Eterno',
                 font=('Georgia', 14, 'bold'), fg=BLANCO, bg=ROJO
                 ).pack(side=tk.LEFT)

        # Cerrar sesión
        crear_boton(barra, 'Cerrar sesión', ROJO_DARK, BLANCO,
                    ('Helvetica', 9), self.app.cerrar_sesion
                    ).pack(side=tk.RIGHT, padx=5, pady=12)

        # Carrito con badge
        n = self.app.contar_carrito()
        texto_carrito = f'🛒 Carrito ({n})' if n > 0 else '🛒 Carrito'
        btn_carrito = crear_boton(barra, texto_carrito, BLANCO, ROJO,
                                  ('Helvetica', 10, 'bold'),
                                  lambda: self.app.mostrar(VentanaCarrito))
        btn_carrito.pack(side=tk.RIGHT, padx=5, pady=12)

        # Nombre del usuario
        if self.app.usuario_actual:
            tk.Label(barra, text=f'Hola, {self.app.usuario_actual["username"]}',
                     font=('Helvetica', 10), fg='#f5d0d8', bg=ROJO
                     ).pack(side=tk.RIGHT, padx=10)

        # Botón admin
        if self.app.es_admin:
            crear_boton(barra, '⚙ Panel Admin', ROJO_DARK, BLANCO,
                        ('Helvetica', 9, 'bold'),
                        lambda: self.app.mostrar(VentanaAdminProductos)
                        ).pack(side=tk.RIGHT, padx=5, pady=12)

    def _mostrar_avisos(self):
        """Muestra banners amarillos para cada aviso activo."""
        try:
            avisos = self.app.db.listar_avisos(solo_activos=True)
            for aviso in avisos:
                frame_aviso = tk.Frame(self, bg=AMARILLO_AVISO, bd=0,
                                        highlightbackground=BORDE_AVISO,
                                        highlightthickness=1)
                frame_aviso.pack(fill=tk.X, padx=12, pady=(6, 0))
                tk.Label(frame_aviso, text=f"📢  {aviso['titulo']}  —  {aviso['mensaje']}",
                         font=('Helvetica', 9), bg=AMARILLO_AVISO, fg='#664d03',
                         wraplength=880, justify='left'
                         ).pack(padx=12, pady=6, anchor='w')
        except Exception:
            pass

    def _construir_catalogo(self):
        """Construye la cuadrícula scrollable de tarjetas de productos con imágenes."""
        # Título
        tk.Label(self, text='— Catálogo —', font=('Georgia', 20, 'bold'),
                 fg=TEXTO, bg=FONDO).pack(pady=(15, 5))
        tk.Label(self, text='Elige el arreglo perfecto para cada ocasión',
                 font=('Helvetica', 10), fg=TEXTO_SUAVE, bg=FONDO).pack(pady=(0, 12))

        # Canvas + Scrollbar
        contenedor = tk.Frame(self, bg=FONDO)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=8)

        canvas = tk.Canvas(contenedor, bg=FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient='vertical', command=canvas.yview,
                                   style='Custom.Vertical.TScrollbar')
        self.frame_grid = tk.Frame(canvas, bg=FONDO)
        self.frame_grid.bind('<Configure>',
                              lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame_grid, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel)

        # Cargar productos
        try:
            productos = self.app.db.listar_productos()
        except Exception:
            productos = []

        if not productos:
            tk.Label(self.frame_grid, text='No hay productos disponibles.',
                     font=('Helvetica', 14), fg=TEXTO_SUAVE, bg=FONDO
                     ).grid(row=0, column=0, padx=20, pady=60, columnspan=3)
            return

        # Crear tarjetas en grid de 3 columnas
        for idx, prod in enumerate(productos):
            fila = idx // 3
            col = idx % 3
            self._crear_tarjeta_producto(prod, fila, col)

    def _crear_tarjeta_producto(self, prod, fila, col):
        """Crea una tarjeta de producto con imagen, nombre, precio y botón."""
        # Frame sombra
        sombra = tk.Frame(self.frame_grid, bg=SOMBRA)
        sombra.grid(row=fila, column=col, padx=10, pady=10, sticky='nsew')
        self.frame_grid.columnconfigure(col, weight=1, minsize=280)

        # Tarjeta interior
        tarjeta = tk.Frame(sombra, bg=BLANCO, bd=0)
        tarjeta.pack(padx=(0, 3), pady=(0, 3), fill='both', expand=True)

        # Hover effect en la tarjeta
        def on_enter(e):
            sombra.config(bg=ROJO_HOVER)
        def on_leave(e):
            sombra.config(bg=SOMBRA)
        tarjeta.bind('<Enter>', on_enter)
        tarjeta.bind('<Leave>', on_leave)

        # ─── IMAGEN del producto ──────────────────────────────────────────
        imagen_nombre = prod['imagen'] if prod['imagen'] else 'default.jpg'
        img = cargar_imagen(imagen_nombre, 180, 180)
        if img:
            self._imgs.append(img)   # Evitar garbage collection
            lbl_img = tk.Label(tarjeta, image=img, bg=BLANCO, cursor='hand2')
            lbl_img.pack(padx=15, pady=(15, 5))
            pid = prod['id']
            lbl_img.bind('<Button-1>',
                         lambda e, p=pid: self.app.mostrar(VentanaProducto, producto_id=p))
        else:
            tk.Label(tarjeta, text='🌸', font=('Helvetica', 50),
                     bg=BLANCO).pack(padx=15, pady=(15, 5))

        # Nombre (clickeable)
        lbl_nombre = tk.Label(tarjeta, text=prod['nombre'],
                               font=('Georgia', 12, 'bold'), fg=TEXTO,
                               bg=BLANCO, cursor='hand2', wraplength=240)
        lbl_nombre.pack(padx=10, pady=(5, 2))
        pid = prod['id']
        lbl_nombre.bind('<Button-1>',
                         lambda e, p=pid: self.app.mostrar(VentanaProducto, producto_id=p))

        # Precio
        tk.Label(tarjeta, text=formato_precio(prod['precio']),
                 font=('Georgia', 16, 'bold'), fg=ROJO, bg=BLANCO
                 ).pack(pady=(2, 4))

        # Stock badge + controles
        stock = prod['stock']
        if stock == 0:
            tk.Label(tarjeta, text='🚫  Agotado', font=('Helvetica', 10, 'bold'),
                     fg=BLANCO, bg=ROJO_STOCK, padx=10, pady=2).pack(pady=(0, 12))
        else:
            color_stock = VERDE if stock > 3 else NARANJA
            txt_stock = f'✔ En stock: {stock}' if stock > 3 else f'⚠ Quedan {stock}'
            tk.Label(tarjeta, text=txt_stock, font=('Helvetica', 9),
                     fg=color_stock, bg=BLANCO).pack(pady=(0, 4))

            # Controles de cantidad
            frame_ctrl = tk.Frame(tarjeta, bg=BLANCO)
            frame_ctrl.pack(pady=(0, 12))
            spin = tk.Spinbox(frame_ctrl, from_=1, to=stock, width=4,
                               font=('Helvetica', 11), justify='center',
                               relief='solid', bd=1)
            spin.pack(side=tk.LEFT, padx=(0, 6))

            def agregar(p=prod, s=spin):
                try:
                    cantidad = int(s.get())
                    actual = self.app.carrito.get(p['id'], 0)
                    if actual + cantidad > p['stock']:
                        messagebox.showwarning('Stock insuficiente',
                            f'Solo quedan {p["stock"]} disponibles.')
                        return
                    self.app.carrito[p['id']] = actual + cantidad
                    messagebox.showinfo('✅ Agregado',
                        f'{p["nombre"]} x{cantidad} agregado al carrito.')
                    self.app.mostrar(VentanaCatalogo)
                except ValueError:
                    messagebox.showerror('Error', 'Cantidad inválida.')

            crear_boton(frame_ctrl, '🛒 Agregar', ROJO, BLANCO,
                        ('Helvetica', 9, 'bold'), agregar).pack(side=tk.LEFT)


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 4 — DETALLE DE PRODUCTO (CON IMAGEN GRANDE)
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaProducto(tk.Frame):
    """Vista detallada de un producto con imagen grande."""

    def __init__(self, parent, app, producto_id=None):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self._imgs = []
        crear_footer(self)  # Pie de página

        # Botón volver
        crear_boton(self, '← Volver al catálogo', ROJO, BLANCO,
                    ('Helvetica', 10), lambda: self.app.mostrar(VentanaCatalogo)
                    ).pack(anchor='w', padx=20, pady=15)

        # Obtener producto
        prod = None
        try:
            if producto_id is not None:
                prod = self.app.db.obtener_producto(producto_id)
        except Exception:
            pass

        if not prod:
            tk.Label(self, text='Producto no encontrado.',
                     font=('Helvetica', 16), fg=ROJO_STOCK, bg=FONDO).pack(pady=50)
            return

        # ─── Layout de dos columnas ───────────────────────────────────────
        sombra, tarjeta = crear_tarjeta_con_sombra(self)
        sombra.pack(padx=40, pady=10, fill=tk.X)

        contenido = tk.Frame(tarjeta, bg=BLANCO)
        contenido.pack(fill=tk.BOTH, padx=20, pady=20)

        # Columna izquierda: imagen
        frame_izq = tk.Frame(contenido, bg=BLANCO)
        frame_izq.pack(side=tk.LEFT, padx=(0, 25))

        imagen_nombre = prod['imagen'] if prod['imagen'] else 'default.jpg'
        img = cargar_imagen(imagen_nombre, 300, 300)
        if img:
            self._imgs.append(img)
            tk.Label(frame_izq, image=img, bg=BLANCO).pack()
        else:
            tk.Label(frame_izq, text='🌹', font=('Helvetica', 80),
                     bg=BLANCO).pack(padx=40, pady=40)

        # Columna derecha: información
        frame_der = tk.Frame(contenido, bg=BLANCO)
        frame_der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(frame_der, text=prod['nombre'], font=('Georgia', 22, 'bold'),
                 fg=TEXTO, bg=BLANCO, wraplength=400, anchor='w', justify='left'
                 ).pack(anchor='w', pady=(0, 8))

        tk.Frame(frame_der, bg=BORDE, height=1).pack(fill=tk.X, pady=(0, 10))

        desc = prod['descripcion'] if prod['descripcion'] else 'Sin descripción disponible.'
        tk.Label(frame_der, text=desc, font=('Helvetica', 11),
                 fg=TEXTO_SUAVE, bg=BLANCO, wraplength=400, justify='left'
                 ).pack(anchor='w', pady=(0, 12))

        tk.Label(frame_der, text=formato_precio(prod['precio']),
                 font=('Georgia', 28, 'bold'), fg=ROJO, bg=BLANCO
                 ).pack(anchor='w', pady=(0, 10))

        stock = prod['stock']
        if stock == 0:
            tk.Label(frame_der, text='🚫  Producto Agotado',
                     font=('Helvetica', 13, 'bold'), fg=BLANCO, bg=ROJO_STOCK,
                     padx=15, pady=5).pack(anchor='w', pady=(5, 10))
        else:
            color_stock = VERDE if stock > 3 else NARANJA
            tk.Label(frame_der, text=f'Disponibles: {stock} unidades',
                     font=('Helvetica', 11), fg=color_stock, bg=BLANCO
                     ).pack(anchor='w', pady=(0, 8))

            frame_ctrl = tk.Frame(frame_der, bg=BLANCO)
            frame_ctrl.pack(anchor='w', pady=(5, 0))
            tk.Label(frame_ctrl, text='Cantidad:', font=('Helvetica', 11),
                     bg=BLANCO, fg=TEXTO).pack(side=tk.LEFT, padx=(0, 8))
            spin = tk.Spinbox(frame_ctrl, from_=1, to=stock, width=5,
                               font=('Helvetica', 12), justify='center',
                               relief='solid', bd=1)
            spin.pack(side=tk.LEFT, padx=(0, 12))

            def agregar_carrito():
                try:
                    cantidad = int(spin.get())
                    actual = self.app.carrito.get(prod['id'], 0)
                    if actual + cantidad > stock:
                        messagebox.showwarning('Stock insuficiente',
                            f'Solo quedan {stock} disponibles (ya tienes {actual}).')
                        return
                    self.app.carrito[prod['id']] = actual + cantidad
                    messagebox.showinfo('✅ Agregado',
                        f'{prod["nombre"]} x{cantidad} agregado al carrito.')
                except ValueError:
                    messagebox.showerror('Error', 'Cantidad inválida.')

            crear_boton(frame_ctrl, '🛒 Agregar al carrito', ROJO, BLANCO,
                        ('Helvetica', 11, 'bold'), agregar_carrito
                        ).pack(side=tk.LEFT, ipady=4)


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 5 — CARRITO DE COMPRAS + CHECKOUT
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaCarrito(tk.Frame):
    """Carrito de compras con tabla, formulario de checkout y opciones de envío."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self._imgs = []
        crear_footer(self)  # Pie de página

        # Barra superior
        barra = tk.Frame(self, bg=ROJO, height=55)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)
        tk.Label(barra, text='🛒  Tu Carrito', font=('Georgia', 14, 'bold'),
                 fg=BLANCO, bg=ROJO).pack(side=tk.LEFT, padx=15)
        crear_boton(barra, '← Volver al catálogo', ROJO_DARK, BLANCO,
                    ('Helvetica', 9), lambda: self.app.mostrar(VentanaCatalogo)
                    ).pack(side=tk.RIGHT, padx=10, pady=12)

        # Canvas scrollable
        contenedor = tk.Frame(self, bg=FONDO)
        contenedor.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(contenedor, bg=FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient='vertical', command=canvas.yview)
        self.frame_contenido = tk.Frame(canvas, bg=FONDO)
        self.frame_contenido.bind('<Configure>',
                                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame_contenido, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all('<MouseWheel>',
                         lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        if not self.app.carrito:
            tk.Label(self.frame_contenido, text='Tu carrito está vacío  🛒',
                     font=('Georgia', 16), fg=TEXTO_SUAVE, bg=FONDO).pack(pady=60)
            crear_boton(self.frame_contenido, 'Ir al catálogo', ROJO, BLANCO,
                        ('Helvetica', 12, 'bold'),
                        lambda: self.app.mostrar(VentanaCatalogo)).pack(ipady=6)
            return

        self._construir_tabla()
        self._construir_formulario_checkout()

    def _construir_tabla(self):
        """Tabla con los artículos del carrito."""
        frame_tabla = tk.Frame(self.frame_contenido, bg=FONDO)
        frame_tabla.pack(fill=tk.X, padx=20, pady=(15, 5))

        tk.Label(frame_tabla, text='Artículos en tu carrito',
                 font=('Georgia', 15, 'bold'), fg=TEXTO, bg=FONDO).pack(anchor='w', pady=(0, 8))

        columnas = ('producto', 'cantidad', 'precio_unit', 'subtotal')
        self.tree = ttk.Treeview(frame_tabla, columns=columnas,
                                  show='headings', style='Custom.Treeview', height=6)
        self.tree.heading('producto', text='Producto')
        self.tree.heading('cantidad', text='Cantidad')
        self.tree.heading('precio_unit', text='Precio Unit.')
        self.tree.heading('subtotal', text='Subtotal')
        self.tree.column('producto', width=320)
        self.tree.column('cantidad', width=100, anchor='center')
        self.tree.column('precio_unit', width=120, anchor='e')
        self.tree.column('subtotal', width=120, anchor='e')
        self.tree.pack(fill=tk.X)

        # Filas alternadas
        self.tree.tag_configure('par', background='#faf5f4')
        self.tree.tag_configure('impar', background=BLANCO)

        self.total = 0.0
        self.items_data = {}
        for i, (pid, qty) in enumerate(self.app.carrito.items()):
            try:
                prod = self.app.db.obtener_producto(pid)
                if not prod: continue
                subtotal = prod['precio'] * qty
                self.total += subtotal
                tag = 'par' if i % 2 == 0 else 'impar'
                iid = self.tree.insert('', 'end', values=(
                    prod['nombre'], qty,
                    formato_precio(prod['precio']),
                    formato_precio(subtotal)
                ), tags=(tag,))
                self.items_data[iid] = pid
            except Exception:
                continue

        frame_acciones = tk.Frame(frame_tabla, bg=FONDO)
        frame_acciones.pack(fill=tk.X, pady=8)
        crear_boton(frame_acciones, '🗑️ Quitar seleccionado', ROJO_STOCK, BLANCO,
                    ('Helvetica', 9, 'bold'), self._quitar_seleccionado
                    ).pack(side=tk.LEFT)
        tk.Label(frame_acciones, text=f'TOTAL: {formato_precio(self.total)}',
                 font=('Georgia', 18, 'bold'), fg=ROJO, bg=FONDO
                 ).pack(side=tk.RIGHT, padx=10)

    def _quitar_seleccionado(self):
        """Elimina el producto seleccionado del carrito."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selecciona', 'Selecciona un producto para quitar.')
            return
        pid = self.items_data.get(sel[0])
        if pid and pid in self.app.carrito:
            del self.app.carrito[pid]
        self.app.mostrar(VentanaCarrito)

    def _construir_formulario_checkout(self):
        """Formulario con datos de envío, método de entrega y botón de compra."""
        sombra, frame_form = crear_tarjeta_con_sombra(self.frame_contenido)
        sombra.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(frame_form, text='Datos de envío', font=('Georgia', 15, 'bold'),
                 fg=TEXTO, bg=BLANCO).pack(padx=20, pady=(15, 10), anchor='w')

        # Método de entrega
        self.metodo_var = tk.StringVar(value='click_collect')
        frame_metodo = tk.Frame(frame_form, bg=BLANCO)
        frame_metodo.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(frame_metodo, text='Método de entrega:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w')
        tk.Radiobutton(frame_metodo, text='🏪 Click & Collect (3 días hábiles)',
                        variable=self.metodo_var, value='click_collect',
                        bg=BLANCO, fg=TEXTO, font=('Helvetica', 10),
                        selectcolor=BLANCO, command=self._actualizar_fecha
                        ).pack(anchor='w', padx=10)
        tk.Radiobutton(frame_metodo, text='📍 Punto Medio (2 días naturales)',
                        variable=self.metodo_var, value='punto_medio',
                        bg=BLANCO, fg=TEXTO, font=('Helvetica', 10),
                        selectcolor=BLANCO, command=self._actualizar_fecha
                        ).pack(anchor='w', padx=10)

        self.lbl_fecha = tk.Label(frame_form, text='', font=('Helvetica', 10, 'bold'),
                                   fg=VERDE, bg=BLANCO)
        self.lbl_fecha.pack(padx=20, pady=5, anchor='w')

        # Opciones Punto Medio
        self.frame_punto_medio = tk.Frame(frame_form, bg=BLANCO)
        self.frame_punto_medio.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(self.frame_punto_medio, text='Ubicación:', font=('Helvetica', 10),
                 bg=BLANCO, fg=TEXTO).grid(row=0, column=0, sticky='w', pady=3)
        self.combo_ubicacion = ttk.Combobox(self.frame_punto_medio,
            values=['El Centro', 'Villa Teresa', 'Plaza Universidad'],
            state='readonly', font=('Helvetica', 10), width=25)
        self.combo_ubicacion.set('El Centro')
        self.combo_ubicacion.grid(row=0, column=1, padx=10, pady=3)
        tk.Label(self.frame_punto_medio, text='Horario:', font=('Helvetica', 10),
                 bg=BLANCO, fg=TEXTO).grid(row=1, column=0, sticky='w', pady=3)
        self.combo_horario = ttk.Combobox(self.frame_punto_medio,
            values=['4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM', '6:00 PM'],
            state='readonly', font=('Helvetica', 10), width=25)
        self.combo_horario.set('4:00 PM')
        self.combo_horario.grid(row=1, column=1, padx=10, pady=3)

        # Separador
        tk.Frame(frame_form, bg=BORDE, height=1).pack(fill=tk.X, padx=20, pady=10)

        # Datos personales
        frame_datos = tk.Frame(frame_form, bg=BLANCO)
        frame_datos.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(frame_datos, text='Nombre del titular *:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', pady=(5, 2))
        self.entry_nombre = tk.Entry(frame_datos, font=('Helvetica', 12),
                                      relief='solid', bd=1)
        self.entry_nombre.pack(fill=tk.X, ipady=5)
        tk.Label(frame_datos, text='Email (opcional):', font=('Helvetica', 10),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', pady=(8, 2))
        self.entry_email = tk.Entry(frame_datos, font=('Helvetica', 12),
                                     relief='solid', bd=1)
        self.entry_email.pack(fill=tk.X, ipady=5)

        # Botón finalizar
        crear_boton(frame_form, '✅  Finalizar Compra', VERDE, BLANCO,
                    ('Helvetica', 13, 'bold'), self._finalizar_compra
                    ).pack(padx=20, pady=(15, 20), fill=tk.X, ipady=8)

        self._actualizar_fecha()

    def _actualizar_fecha(self):
        """Actualiza la fecha estimada de entrega."""
        if self.metodo_var.get() == 'click_collect':
            fecha = calcular_dias_habiles(3)
            self.lbl_fecha.config(text=f'📅 Listo para recoger: {formato_fecha_espanol(fecha)}')
            self.frame_punto_medio.pack_forget()
        else:
            fecha = datetime.now() + timedelta(days=2)
            self.lbl_fecha.config(text=f'📅 Fecha de encuentro: {formato_fecha_espanol(fecha)}')
            self.frame_punto_medio.pack(fill=tk.X, padx=20, pady=5)

    def _finalizar_compra(self):
        """Procesa la compra: valida datos, crea pedido y limpia carrito."""
        nombre = self.entry_nombre.get().strip()
        email = self.entry_email.get().strip() or None
        if not nombre:
            messagebox.showerror('Campo requerido', 'Por favor ingresa el nombre del titular.')
            return
        if not self.app.carrito:
            messagebox.showwarning('Carrito vacío', 'No hay productos en el carrito.')
            return
        items = [{'producto_id': pid, 'cantidad': qty}
                 for pid, qty in self.app.carrito.items()]
        try:
            pedido_id = self.app.db.crear_pedido(nombre, email, items)
            if pedido_id:
                self.app.carrito = {}
                self.app.mostrar(VentanaConfirmacion, pedido_id=pedido_id)
            else:
                messagebox.showerror('Error', 'No se pudo procesar. ¿Stock insuficiente?')
        except Exception as e:
            messagebox.showerror('Error', f'Error al procesar: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 6 — CONFIRMACIÓN DE PEDIDO
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaConfirmacion(tk.Frame):
    """Pantalla de éxito después de completar una compra."""

    def __init__(self, parent, app, pedido_id=None):
        super().__init__(parent, bg=FONDO)
        self.app = app
        crear_footer(self)  # Pie de página

        sombra, tarjeta = crear_tarjeta_con_sombra(self)
        sombra.place(relx=0.5, rely=0.5, anchor='center', width=480, height=420)

        # Decoración
        tk.Label(tarjeta, text='🌸✨🌹✨🌸', font=('Helvetica', 24),
                 bg=BLANCO).pack(pady=(30, 10))

        tk.Label(tarjeta, text='¡Pedido Confirmado!', font=('Georgia', 22, 'bold'),
                 fg=VERDE, bg=BLANCO).pack(pady=(0, 5))

        tk.Label(tarjeta, text='Gracias por tu compra en\nFlorería Brillo Eterno',
                 font=('Helvetica', 11), fg=TEXTO, bg=BLANCO).pack(pady=(0, 12))

        # Número de pedido
        id_texto = f'#{pedido_id}' if pedido_id else '#—'
        frame_id = tk.Frame(tarjeta, bg=FONDO, bd=1, relief='solid',
                             highlightbackground=BORDE, highlightthickness=1)
        frame_id.pack(padx=60, pady=5)
        tk.Label(frame_id, text=f'Tu número de pedido es: {id_texto}',
                 font=('Georgia', 14, 'bold'), fg=ROJO, bg=FONDO,
                 padx=15, pady=8).pack()

        tk.Label(tarjeta, text='🌸 Estamos preparando tu arreglo\nfloral con amor... 🌸',
                 font=('Helvetica', 10), fg=TEXTO_SUAVE, bg=BLANCO).pack(pady=(10, 15))

        crear_boton(tarjeta, 'Volver al catálogo', ROJO, BLANCO,
                    ('Helvetica', 11, 'bold'),
                    lambda: self.app.mostrar(VentanaCatalogo)
                    ).pack(fill=tk.X, padx=50, ipady=7)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — BARRA DE NAVEGACIÓN DEL ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
def construir_barra_admin(frame, app, titulo_extra=''):
    """Crea una barra de navegación consistente para vistas admin."""
    barra = tk.Frame(frame, bg=ROJO_DARK, height=55)
    barra.pack(fill=tk.X)
    barra.pack_propagate(False)

    texto = f'🌹 Brillo Eterno — Admin {titulo_extra}'
    tk.Label(barra, text=texto, font=('Georgia', 12, 'bold'),
             fg=BLANCO, bg=ROJO_DARK).pack(side=tk.LEFT, padx=15)

    crear_boton(barra, 'Cerrar sesión', ROJO_STOCK, BLANCO,
                ('Helvetica', 9), app.cerrar_sesion
                ).pack(side=tk.RIGHT, padx=5, pady=12)

    botones = [
        ('📊 Reporte', VentanaAdminReporte),
        ('📢 Avisos', VentanaAdminAvisos),
        ('📦 Pedidos', VentanaAdminPedidos),
        ('🏪 Productos', VentanaAdminProductos),
    ]
    for texto_btn, clase in botones:
        crear_boton(barra, texto_btn, ROJO, BLANCO, ('Helvetica', 9),
                    lambda c=clase: app.mostrar(c)
                    ).pack(side=tk.RIGHT, padx=3, pady=12)


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 7 — ADMIN: GESTIÓN DE PRODUCTOS
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaAdminProductos(tk.Frame):
    """Panel de administración para ver, crear, editar y borrar productos."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        crear_footer(self)  # Pie de página
        construir_barra_admin(self, app, '| Productos')

        frame_acciones = tk.Frame(self, bg=FONDO)
        frame_acciones.pack(fill=tk.X, padx=15, pady=10)
        crear_boton(frame_acciones, '+ Agregar producto', VERDE, BLANCO,
                    ('Helvetica', 10, 'bold'),
                    lambda: self.app.mostrar(VentanaAdminProductoForm, modo='nuevo')
                    ).pack(side=tk.LEFT, ipady=4)

        # Treeview
        columnas = ('id', 'nombre', 'precio', 'stock')
        self.tree = ttk.Treeview(self, columns=columnas, show='headings',
                                  style='Custom.Treeview', height=14)
        self.tree.heading('id', text='ID')
        self.tree.heading('nombre', text='Nombre')
        self.tree.heading('precio', text='Precio')
        self.tree.heading('stock', text='Stock')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('nombre', width=380)
        self.tree.column('precio', width=120, anchor='e')
        self.tree.column('stock', width=80, anchor='center')
        self.tree.pack(fill=tk.X, padx=15, pady=(0, 5))

        self.tree.tag_configure('agotado', background='#fce4ec')
        self.tree.tag_configure('bajo', background='#fff8e1')
        self.tree.tag_configure('normal', background=BLANCO)
        self.tree.tag_configure('normal_alt', background='#faf5f4')

        self._cargar_productos()

        # Panel inferior de acciones
        frame_inferior = tk.Frame(self, bg=FONDO)
        frame_inferior.pack(fill=tk.X, padx=15, pady=5)

        frame_stock = tk.LabelFrame(frame_inferior, text='Actualizar Stock Rápido',
                                     font=('Helvetica', 10, 'bold'), bg=FONDO,
                                     fg=TEXTO, padx=10, pady=5)
        frame_stock.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(frame_stock, text='Nuevo stock:', font=('Helvetica', 10),
                 bg=FONDO, fg=TEXTO).pack(side=tk.LEFT, padx=3)
        self.entry_stock = tk.Entry(frame_stock, width=8, font=('Helvetica', 10),
                                     relief='solid', bd=1)
        self.entry_stock.pack(side=tk.LEFT, padx=3)
        crear_boton(frame_stock, 'Guardar', NARANJA, BLANCO,
                    ('Helvetica', 9, 'bold'), self._actualizar_stock
                    ).pack(side=tk.LEFT, padx=5)

        frame_botones = tk.Frame(frame_inferior, bg=FONDO)
        frame_botones.pack(side=tk.RIGHT)
        crear_boton(frame_botones, '✏️ Editar', ROJO, BLANCO,
                    ('Helvetica', 10, 'bold'), self._editar_producto
                    ).pack(side=tk.LEFT, padx=5, ipady=2)
        crear_boton(frame_botones, '🗑️ Borrar', ROJO_STOCK, BLANCO,
                    ('Helvetica', 10, 'bold'), self._borrar_producto
                    ).pack(side=tk.LEFT, padx=5, ipady=2)

    def _cargar_productos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            productos = self.app.db.listar_productos()
            for i, prod in enumerate(productos):
                stock = prod['stock']
                if stock == 0:
                    tag = 'agotado'
                elif stock <= 3:
                    tag = 'bajo'
                else:
                    tag = 'normal' if i % 2 == 0 else 'normal_alt'
                self.tree.insert('', 'end', values=(
                    prod['id'], prod['nombre'],
                    formato_precio(prod['precio']), stock
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror('Error', f'No se pudieron cargar productos: {e}')

    def _obtener_id_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selecciona', 'Selecciona un producto de la tabla.')
            return None
        return int(self.tree.item(sel[0], 'values')[0])

    def _actualizar_stock(self):
        pid = self._obtener_id_seleccionado()
        if pid is None: return
        try:
            nuevo_stock = int(self.entry_stock.get())
            if nuevo_stock < 0:
                messagebox.showerror('Error', 'El stock no puede ser negativo.')
                return
            if self.app.db.actualizar_stock(pid, nuevo_stock):
                messagebox.showinfo('Éxito', 'Stock actualizado.')
                self._cargar_productos()
            else:
                messagebox.showerror('Error', 'No se pudo actualizar.')
        except ValueError:
            messagebox.showerror('Error', 'Ingresa un número válido.')

    def _editar_producto(self):
        pid = self._obtener_id_seleccionado()
        if pid is not None:
            self.app.mostrar(VentanaAdminProductoForm, modo='editar', producto_id=pid)

    def _borrar_producto(self):
        pid = self._obtener_id_seleccionado()
        if pid is None: return
        if messagebox.askyesno('Confirmar', '¿Eliminar este producto?\nEsta acción no se puede deshacer.'):
            try:
                if self.app.db.borrar_producto(pid):
                    messagebox.showinfo('Eliminado', 'Producto eliminado.')
                    self._cargar_productos()
                else:
                    messagebox.showerror('Error', 'No se pudo eliminar. ¿Tiene pedidos?')
            except Exception as e:
                messagebox.showerror('Error', f'Error: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 8 — ADMIN: FORMULARIO CREAR / EDITAR PRODUCTO
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaAdminProductoForm(tk.Frame):
    """Formulario para crear o editar un producto."""

    def __init__(self, parent, app, modo='nuevo', producto_id=None):
        super().__init__(parent, bg=FONDO)
        self.app = app
        self.modo = modo
        self.producto_id = producto_id
        crear_footer(self)  # Pie de página

        crear_boton(self, '← Volver', ROJO, BLANCO, ('Helvetica', 10),
                    lambda: self.app.mostrar(VentanaAdminProductos)
                    ).pack(anchor='w', padx=20, pady=15)

        titulo = 'Nuevo Producto' if modo == 'nuevo' else 'Editar Producto'
        tk.Label(self, text=titulo, font=('Georgia', 18, 'bold'),
                 fg=TEXTO, bg=FONDO).pack(pady=(0, 10))

        sombra, tarjeta = crear_tarjeta_con_sombra(self)
        sombra.pack(fill=tk.X, padx=60, pady=5)

        tk.Label(tarjeta, text='Nombre del producto *:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', padx=20, pady=(15, 2))
        self.entry_nombre = tk.Entry(tarjeta, font=('Helvetica', 12), relief='solid', bd=1)
        self.entry_nombre.pack(fill=tk.X, padx=20, ipady=5)

        tk.Label(tarjeta, text='Descripción:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', padx=20, pady=(10, 2))
        self.text_desc = tk.Text(tarjeta, font=('Helvetica', 11), height=4,
                                  relief='solid', bd=1, wrap='word')
        self.text_desc.pack(fill=tk.X, padx=20)

        frame_numeros = tk.Frame(tarjeta, bg=BLANCO)
        frame_numeros.pack(fill=tk.X, padx=20, pady=(10, 0))
        tk.Label(frame_numeros, text='Precio ($) *:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).grid(row=0, column=0, sticky='w', pady=2)
        self.entry_precio = tk.Entry(frame_numeros, font=('Helvetica', 12),
                                      relief='solid', bd=1, width=15)
        self.entry_precio.grid(row=0, column=1, padx=10, pady=2)
        tk.Label(frame_numeros, text='Stock *:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).grid(row=0, column=2, sticky='w', padx=(20, 0), pady=2)
        self.entry_stock = tk.Entry(frame_numeros, font=('Helvetica', 12),
                                     relief='solid', bd=1, width=10)
        self.entry_stock.grid(row=0, column=3, padx=10, pady=2)

        if modo == 'editar' and producto_id:
            try:
                prod = self.app.db.obtener_producto(producto_id)
                if prod:
                    self.entry_nombre.insert(0, prod['nombre'])
                    self.text_desc.insert('1.0', prod['descripcion'] or '')
                    self.entry_precio.insert(0, str(prod['precio']))
                    self.entry_stock.insert(0, str(prod['stock']))
            except Exception:
                pass

        texto_btn = 'Crear producto' if modo == 'nuevo' else 'Guardar cambios'
        crear_boton(tarjeta, texto_btn, VERDE, BLANCO,
                    ('Helvetica', 12, 'bold'), self._guardar
                    ).pack(fill=tk.X, padx=20, pady=15, ipady=7)

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_desc.get('1.0', 'end-1c').strip()
        precio_str = self.entry_precio.get().strip()
        stock_str = self.entry_stock.get().strip()
        if not nombre:
            messagebox.showerror('Error', 'El nombre es obligatorio.')
            return
        try:
            precio = float(precio_str)
            if precio < 0: raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Precio inválido.')
            return
        try:
            stock = int(stock_str)
            if stock < 0: raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Stock inválido.')
            return
        try:
            if self.modo == 'nuevo':
                if self.app.db.crear_producto(nombre, descripcion, precio, stock):
                    messagebox.showinfo('Éxito', 'Producto creado.')
                    self.app.mostrar(VentanaAdminProductos)
                else:
                    messagebox.showerror('Error', 'No se pudo crear.')
            else:
                if self.app.db.actualizar_producto(self.producto_id, nombre, descripcion, precio, stock):
                    messagebox.showinfo('Éxito', 'Producto actualizado.')
                    self.app.mostrar(VentanaAdminProductos)
                else:
                    messagebox.showerror('Error', 'No se pudo actualizar.')
        except Exception as e:
            messagebox.showerror('Error', f'Error: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 9 — ADMIN: GESTIÓN DE PEDIDOS
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaAdminPedidos(tk.Frame):
    """Panel para ver y gestionar pedidos de clientes."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        crear_footer(self)  # Pie de página
        construir_barra_admin(self, app, '| Pedidos')

        tk.Label(self, text='Gestión de Pedidos', font=('Georgia', 16, 'bold'),
                 fg=TEXTO, bg=FONDO).pack(pady=(15, 10))

        columnas = ('id', 'cliente', 'email', 'productos', 'total', 'estado', 'fecha')
        self.tree = ttk.Treeview(self, columns=columnas, show='headings',
                                  style='Custom.Treeview', height=14)
        self.tree.heading('id', text='ID')
        self.tree.heading('cliente', text='Cliente')
        self.tree.heading('email', text='Email')
        self.tree.heading('productos', text='Productos')
        self.tree.heading('total', text='Total')
        self.tree.heading('estado', text='Estado')
        self.tree.heading('fecha', text='Fecha')
        self.tree.column('id', width=40, anchor='center')
        self.tree.column('cliente', width=120)
        self.tree.column('email', width=130)
        self.tree.column('productos', width=220)
        self.tree.column('total', width=80, anchor='e')
        self.tree.column('estado', width=80, anchor='center')
        self.tree.column('fecha', width=130)
        self.tree.pack(fill=tk.X, padx=15, pady=(0, 5))

        self.tree.tag_configure('pendiente', foreground=NARANJA)
        self.tree.tag_configure('entregado', foreground=VERDE)

        self._cargar_pedidos()

        frame_acciones = tk.Frame(self, bg=FONDO)
        frame_acciones.pack(fill=tk.X, padx=15, pady=10)
        crear_boton(frame_acciones, '✅ Marcar Entregado', VERDE, BLANCO,
                    ('Helvetica', 10, 'bold'),
                    lambda: self._cambiar_estado('entregado')
                    ).pack(side=tk.LEFT, padx=5, ipady=3)
        crear_boton(frame_acciones, '⏳ Marcar Pendiente', NARANJA, BLANCO,
                    ('Helvetica', 10, 'bold'),
                    lambda: self._cambiar_estado('pendiente')
                    ).pack(side=tk.LEFT, padx=5, ipady=3)

    def _cargar_pedidos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            pedidos = self.app.db.listar_pedidos()
            for ped in pedidos:
                estado = ped['estado'] if ped['estado'] else 'pendiente'
                tag = 'entregado' if estado == 'entregado' else 'pendiente'
                self.tree.insert('', 'end', values=(
                    ped['id'], ped['cliente_nombre'],
                    ped['cliente_email'] or '—',
                    ped['productos_nombres'] or 'N/A',
                    formato_precio(ped['total']),
                    estado, ped['creado_en']
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror('Error', f'Error al cargar pedidos: {e}')

    def _cambiar_estado(self, nuevo_estado):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selecciona', 'Selecciona un pedido.')
            return
        pedido_id = int(self.tree.item(sel[0], 'values')[0])
        try:
            if self.app.db.actualizar_estado_pedido(pedido_id, nuevo_estado):
                messagebox.showinfo('Éxito', f'Pedido #{pedido_id} → "{nuevo_estado}".')
                self._cargar_pedidos()
            else:
                messagebox.showerror('Error', 'No se pudo actualizar.')
        except Exception as e:
            messagebox.showerror('Error', f'Error: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 10 — ADMIN: REPORTE DE VENTAS DEL DÍA
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaAdminReporte(tk.Frame):
    """Dashboard con KPIs financieros del día actual."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        crear_footer(self)  # Pie de página
        construir_barra_admin(self, app, '| Reporte')

        # Canvas scrollable
        contenedor = tk.Frame(self, bg=FONDO)
        contenedor.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(contenedor, bg=FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient='vertical', command=canvas.yview)
        self.frame_contenido = tk.Frame(canvas, bg=FONDO)
        self.frame_contenido.bind('<Configure>',
                                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame_contenido, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all('<MouseWheel>',
                         lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        # Datos del reporte
        try:
            pedidos, total_dia, gastos, producto_estrella = self.app.db.reporte_ventas_hoy()
        except Exception:
            pedidos, total_dia, gastos, producto_estrella = [], 0.0, 0.0, 'N/A'

        ganancia = total_dia - gastos
        num_pedidos = len(pedidos) if pedidos else 0
        ticket_promedio = total_dia / num_pedidos if num_pedidos > 0 else 0.0

        hoy = date.today()
        fecha_str = f"{hoy.day}/{hoy.month}/{hoy.year}"

        tk.Label(self.frame_contenido,
                 text=f'📊  Resumen operativo del día: {fecha_str}',
                 font=('Georgia', 16, 'bold'), fg=TEXTO, bg=FONDO
                 ).pack(pady=(15, 15))

        # KPI Cards
        frame_kpis = tk.Frame(self.frame_contenido, bg=FONDO)
        frame_kpis.pack(fill=tk.X, padx=15, pady=(0, 15))

        self._crear_kpi(frame_kpis, 0, 0, '📦', 'Pedidos hoy', str(num_pedidos), ROJO)
        self._crear_kpi(frame_kpis, 0, 1, '💵', 'Ventas (Ingresos)', formato_precio(total_dia), VERDE)
        self._crear_kpi(frame_kpis, 0, 2, '📉', 'Gastos Operativos', formato_precio(gastos), NARANJA)
        color_gan = VERDE if ganancia >= 0 else ROJO_STOCK
        self._crear_kpi(frame_kpis, 1, 0, '⚖️', 'Ganancia Neta', formato_precio(ganancia), color_gan)
        self._crear_kpi(frame_kpis, 1, 1, '🏷️', 'Ticket Promedio', formato_precio(ticket_promedio), ROJO)
        self._crear_kpi(frame_kpis, 1, 2, '🌟', 'Producto Estrella', producto_estrella, ROJO)

        # Formulario gastos
        frame_gastos = tk.LabelFrame(self.frame_contenido, text='Modificar Gastos del Día',
                                      font=('Helvetica', 11, 'bold'), bg=BLANCO,
                                      fg=TEXTO, padx=15, pady=10)
        frame_gastos.pack(fill=tk.X, padx=15, pady=(0, 10))
        tk.Label(frame_gastos, text='💸 Monto ($):', font=('Helvetica', 10),
                 bg=BLANCO, fg=TEXTO).pack(side=tk.LEFT, padx=5)
        self.entry_gastos = tk.Entry(frame_gastos, width=15, font=('Helvetica', 11),
                                      relief='solid', bd=1)
        self.entry_gastos.insert(0, str(gastos))
        self.entry_gastos.pack(side=tk.LEFT, padx=5)
        crear_boton(frame_gastos, 'Actualizar Gastos', NARANJA, BLANCO,
                    ('Helvetica', 10, 'bold'), self._guardar_gastos
                    ).pack(side=tk.LEFT, padx=10)

        # Tabla de pedidos del día
        if pedidos:
            tk.Label(self.frame_contenido, text='Pedidos del día',
                     font=('Georgia', 14, 'bold'), fg=TEXTO, bg=FONDO
                     ).pack(padx=15, pady=(10, 5), anchor='w')

            columnas = ('id', 'cliente', 'detalle', 'total', 'estado')
            tree = ttk.Treeview(self.frame_contenido, columns=columnas,
                                show='headings', style='Custom.Treeview',
                                height=min(len(pedidos), 8))
            tree.heading('id', text='ID')
            tree.heading('cliente', text='Cliente')
            tree.heading('detalle', text='Detalle')
            tree.heading('total', text='Total')
            tree.heading('estado', text='Estado')
            tree.column('id', width=40, anchor='center')
            tree.column('cliente', width=150)
            tree.column('detalle', width=350)
            tree.column('total', width=100, anchor='e')
            tree.column('estado', width=80, anchor='center')
            tree.pack(fill=tk.X, padx=15, pady=(0, 15))

            for ped in pedidos:
                detalle = ped['detalle'] if ped['detalle'] else 'N/A'
                tree.insert('', 'end', values=(
                    ped['id'], ped['cliente_nombre'],
                    detalle, formato_precio(ped['total']),
                    ped['estado'] or 'pendiente'
                ))

    def _crear_kpi(self, parent, fila, col, icono, titulo, valor, color):
        """Crea una tarjeta KPI con borde lateral de color."""
        sombra = tk.Frame(parent, bg=SOMBRA)
        sombra.grid(row=fila, column=col, padx=6, pady=6, sticky='nsew')
        parent.columnconfigure(col, weight=1, minsize=200)

        interior = tk.Frame(sombra, bg=BLANCO)
        interior.pack(padx=(0, 3), pady=(0, 3), fill='both', expand=True)

        # Borde de color a la izquierda
        tk.Frame(interior, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)

        contenido = tk.Frame(interior, bg=BLANCO)
        contenido.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(contenido, text=f'{icono}  {titulo}', font=('Helvetica', 9),
                 fg=TEXTO_SUAVE, bg=BLANCO).pack(anchor='w')
        tk.Label(contenido, text=valor, font=('Georgia', 15, 'bold'),
                 fg=color, bg=BLANCO, wraplength=180).pack(anchor='w', pady=(2, 0))

    def _guardar_gastos(self):
        try:
            monto = float(self.entry_gastos.get().strip())
            if monto < 0:
                messagebox.showerror('Error', 'El monto no puede ser negativo.')
                return
            if self.app.db.guardar_gastos_hoy(monto):
                messagebox.showinfo('Éxito', 'Gastos actualizados.')
                self.app.mostrar(VentanaAdminReporte)
            else:
                messagebox.showerror('Error', 'No se pudieron guardar.')
        except ValueError:
            messagebox.showerror('Error', 'Ingresa un monto válido.')


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME 11 — ADMIN: GESTIÓN DE AVISOS
# ═══════════════════════════════════════════════════════════════════════════════
class VentanaAdminAvisos(tk.Frame):
    """Panel para crear, mostrar/ocultar y borrar avisos."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=FONDO)
        self.app = app
        crear_footer(self)  # Pie de página
        construir_barra_admin(self, app, '| Avisos')

        # Canvas scrollable
        contenedor = tk.Frame(self, bg=FONDO)
        contenedor.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(contenedor, bg=FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient='vertical', command=canvas.yview)
        self.frame_contenido = tk.Frame(canvas, bg=FONDO)
        self.frame_contenido.bind('<Configure>',
                                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame_contenido, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all('<MouseWheel>',
                         lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        # Formulario para crear aviso
        sombra, frame_crear = crear_tarjeta_con_sombra(self.frame_contenido)
        sombra.pack(fill=tk.X, padx=15, pady=(15, 10))

        tk.Label(frame_crear, text='📢  Publicar nuevo aviso',
                 font=('Georgia', 13, 'bold'), fg=TEXTO, bg=BLANCO
                 ).pack(anchor='w', padx=15, pady=(12, 8))

        tk.Label(frame_crear, text='Título:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', padx=15, pady=(0, 2))
        self.entry_titulo = tk.Entry(frame_crear, font=('Helvetica', 12),
                                      relief='solid', bd=1)
        self.entry_titulo.pack(fill=tk.X, padx=15, ipady=5)

        tk.Label(frame_crear, text='Mensaje:', font=('Helvetica', 10, 'bold'),
                 bg=BLANCO, fg=TEXTO).pack(anchor='w', padx=15, pady=(8, 2))
        self.text_mensaje = tk.Text(frame_crear, font=('Helvetica', 11), height=3,
                                     relief='solid', bd=1, wrap='word')
        self.text_mensaje.pack(fill=tk.X, padx=15)

        crear_boton(frame_crear, '📢 Publicar aviso', VERDE, BLANCO,
                    ('Helvetica', 10, 'bold'), self._crear_aviso
                    ).pack(fill=tk.X, padx=15, pady=(10, 12), ipady=5)

        # Tabla de avisos
        tk.Label(self.frame_contenido, text='Avisos existentes',
                 font=('Georgia', 14, 'bold'), fg=TEXTO, bg=FONDO
                 ).pack(padx=15, pady=(10, 5), anchor='w')

        columnas = ('id', 'titulo', 'mensaje', 'estado', 'fecha')
        self.tree = ttk.Treeview(self.frame_contenido, columns=columnas,
                                  show='headings', style='Custom.Treeview', height=8)
        self.tree.heading('id', text='ID')
        self.tree.heading('titulo', text='Título')
        self.tree.heading('mensaje', text='Mensaje')
        self.tree.heading('estado', text='Estado')
        self.tree.heading('fecha', text='Fecha')
        self.tree.column('id', width=40, anchor='center')
        self.tree.column('titulo', width=160)
        self.tree.column('mensaje', width=340)
        self.tree.column('estado', width=80, anchor='center')
        self.tree.column('fecha', width=130)
        self.tree.pack(fill=tk.X, padx=15, pady=(0, 5))

        self.tree.tag_configure('visible', foreground=VERDE)
        self.tree.tag_configure('oculto', foreground=TEXTO_SUAVE)

        self._cargar_avisos()

        frame_acciones = tk.Frame(self.frame_contenido, bg=FONDO)
        frame_acciones.pack(fill=tk.X, padx=15, pady=10)
        crear_boton(frame_acciones, '👁️ Mostrar / Ocultar', NARANJA, BLANCO,
                    ('Helvetica', 10, 'bold'), self._toggle_aviso
                    ).pack(side=tk.LEFT, padx=5, ipady=3)
        crear_boton(frame_acciones, '🗑️ Borrar aviso', ROJO_STOCK, BLANCO,
                    ('Helvetica', 10, 'bold'), self._borrar_aviso
                    ).pack(side=tk.LEFT, padx=5, ipady=3)

    def _cargar_avisos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            avisos = self.app.db.listar_avisos(solo_activos=False)
            for aviso in avisos:
                estado = 'Visible' if aviso['activo'] else 'Oculto'
                tag = 'visible' if aviso['activo'] else 'oculto'
                self.tree.insert('', 'end', values=(
                    aviso['id'], aviso['titulo'],
                    aviso['mensaje'][:80] + ('...' if len(aviso['mensaje']) > 80 else ''),
                    estado, aviso['creado_en']
                ), tags=(tag,))
        except Exception as e:
            messagebox.showerror('Error', f'Error al cargar avisos: {e}')

    def _crear_aviso(self):
        titulo = self.entry_titulo.get().strip()
        mensaje = self.text_mensaje.get('1.0', 'end-1c').strip()
        if not titulo or not mensaje:
            messagebox.showerror('Error', 'Completa el título y el mensaje.')
            return
        try:
            if self.app.db.crear_aviso(titulo, mensaje):
                messagebox.showinfo('Publicado', 'Aviso publicado exitosamente.')
                self.entry_titulo.delete(0, 'end')
                self.text_mensaje.delete('1.0', 'end')
                self._cargar_avisos()
            else:
                messagebox.showerror('Error', 'No se pudo publicar.')
        except Exception as e:
            messagebox.showerror('Error', f'Error: {e}')

    def _toggle_aviso(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selecciona', 'Selecciona un aviso.')
            return
        aviso_id = int(self.tree.item(sel[0], 'values')[0])
        try:
            self.app.db.togglear_aviso(aviso_id)
            self._cargar_avisos()
        except Exception as e:
            messagebox.showerror('Error', f'Error: {e}')

    def _borrar_aviso(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Selecciona', 'Selecciona un aviso.')
            return
        aviso_id = int(self.tree.item(sel[0], 'values')[0])
        if messagebox.askyesno('Confirmar', '¿Borrar este aviso?'):
            try:
                self.app.db.borrar_aviso(aviso_id)
                self._cargar_avisos()
                messagebox.showinfo('Eliminado', 'Aviso eliminado.')
            except Exception as e:
                messagebox.showerror('Error', f'Error: {e}')


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    aplicacion = AplicacionTienda()   # Crea la instancia del controlador
    aplicacion.ejecutar()              # Inicia el bucle de eventos
    # INSTRUCCIONES:
    # 1. Asegúrate de que tienda_db.py esté en el mismo directorio
    # 2. Ejecuta: python app.py
    # 3. Credenciales admin: usuario='admin', contraseña='BrilloEterno123'