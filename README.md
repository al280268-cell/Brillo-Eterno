# Florería Brillo Eterno

Tienda en línea de flores eternas hechas a mano con listón. Desarrollada con Flask y SQLite.

## Características

- **Catálogo de productos** con imágenes y precios
- **Carrito de compras** con checkout simulado
- **Registro e inicio de sesión** de usuarios
- **Panel de administración** para agregar, editar y eliminar productos
- **Diseño responsivo** para móvil y escritorio
- **Página "Nosotros"** con información de la florería

## Requisitos

- Python 3.8 o superior

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/al280268-cell/Brillo-Eterno.git
cd Brillo-Eterno

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

Abrir en el navegador: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Acceso al panel de administración

- URL: `/admin/login`
- Usuario: `admin`
- Contraseña: `BrilloEterno123`

## Estructura del proyecto

```
Brillo-Eterno/
├── app.py              # Aplicación principal Flask
├── tienda_db.py        # Capa de base de datos SQLite
├── requirements.txt    # Dependencias de Python
├── static/
│   ├── styles.css      # Estilos CSS
│   ├── normalize.css   # Reset CSS
│   └── imagenes/       # Imágenes de productos
└── templates/          # Plantillas HTML (Jinja2)
    ├── base.html       # Plantilla base
    ├── index.html      # Catálogo
    ├── producto.html   # Detalle de producto
    ├── carrito.html    # Carrito de compras
    ├── checkout_ok.html # Confirmación de pedido
    ├── login.html      # Inicio de sesión
    ├── registro.html   # Registro de usuario
    ├── nosotros.html   # Página "Nosotros"
    ├── admin_login.html           # Login admin
    ├── admin_productos.html       # Lista de productos (admin)
    ├── admin_producto_nuevo.html  # Crear producto (admin)
    └── admin_producto_editar.html # Editar producto (admin)
```
