# 🌹 Florería Brillo Eterno

Aplicación web para una florería de flores eternas artesanales.  
Desarrollada con **Python + Flask + SQLite3 + SCSS + Gulp + Stripe API**.

---

## 📋 Requisitos previos

Antes de empezar, necesitas tener instalado:

- **Python 3.9+** → [Descargar](https://www.python.org/downloads/)
- **Node.js 18+** → [Descargar](https://nodejs.org/) *(solo si quieres compilar SCSS)*
- **Git** → [Descargar](https://git-scm.com/)

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio
```bash
git clone https://github.com/al280268-cell/Brillo-Eterno.git
cd Brillo-Eterno
```

### 2. Cambiar a la rama del proyecto
```bash
git checkout final_Examenparcial2
```

### 3. Instalar dependencias de Python
```bash
pip install -r requirements.txt
```

### 4. Crear el archivo `.env` con las llaves de Stripe
Dentro de la carpeta `mi_tienda/`, crea un archivo llamado `.env` con este contenido:
```
STRIPE_SECRET_KEY=sk_test_TU_LLAVE_SECRETA_AQUI
STRIPE_PUBLIC_KEY=pk_test_TU_LLAVE_PUBLICA_AQUI
```

### 5. Ejecutar la aplicación
```bash
cd mi_tienda
py app.py
```

### 6. Abrir en el navegador
```
http://127.0.0.1:5000/
```

---

## 🔑 Credenciales

| Rol | Usuario | Contraseña |
|---|---|---|
| **Admin** | `admin` | `BrilloEterno123` |
| **Cliente** | Crear cuenta en `/registro` | — |

### Tarjeta de prueba Stripe:
- **Número:** `4242 4242 4242 4242`
- **Fecha:** Cualquier fecha futura (ej. `12/30`)
- **CVC:** Cualquier 3 dígitos (ej. `123`)

---

## 📁 Estructura del proyecto

```
Brillo-Eterno/
├── mi_tienda/
│   ├── app.py              ← Backend Flask + APIs
│   ├── tienda_db.py         ← Base de datos POO + SQLite3
│   ├── .env                 ← Llaves de Stripe (NO se sube a Git)
│   ├── gulpfile.js          ← Compilador SCSS → CSS
│   ├── package.json         ← Dependencias Node.js
│   ├── static/
│   │   ├── css/styles.css   ← Estilos con animaciones
│   │   ├── scss/styles.scss ← Estilos fuente
│   │   ├── js/main.js       ← JavaScript
│   │   └── imagenes/        ← Fotos de productos
│   └── templates/           ← 14 plantillas HTML
├── requirements.txt         ← Dependencias Python
├── .gitignore               ← Excluye .env y archivos sensibles
└── README.md                ← Este archivo
```

---

## 🔌 APIs integradas

| API | Función |
|---|---|
| **Stripe** | Pagos seguros con tarjeta (MXN) |
| **QR Server** | Código QR de seguimiento del pedido |
| **WhatsApp** | Botón flotante de contacto directo |

---

## 🛠️ Compilar SCSS (opcional)

Si quieres modificar los estilos:
```bash
cd mi_tienda
npm install
npx gulp styles    # Compilar una vez
npx gulp watch     # Compilar automáticamente al guardar
```

---

## 👥 Equipo

Examen Parcial II — Administración de Bases de Datos  
Florería Brillo Eterno © 2026
