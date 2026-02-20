# 📁 Configuración de Google Drive API & Autenticación

Este documento detalla el flujo para configurar una **Service Account**, generar credenciales y asegurar el acceso a carpetas en **Shared Drives** (Unidades Compartidas) desde un entorno Django.

---

## 🚀 1. Creación del Proyecto y Service Account

1. Ve a [Google Cloud Console](https://console.cloud.google.com).
2. Crea un nuevo proyecto o selecciona uno existente.
3. En el menú lateral, ve a **APIs y Servicios > Biblioteca**.
4. Busca **"Google Drive API"** y haz clic en **Habilitar**.
5. Ve a **APIs y Servicios > Credenciales**.
6. Haz clic en **Crear credenciales > Cuenta de servicio**.
7. Asigna un nombre (ej. `django-drive-manager`) y finaliza la creación.

## 🔑 2. Generación del Archivo de Claves (JSON)

> [!CAUTION]
> **IMPORTANTE:** Nunca subas este archivo a GitHub. Google inhabilitará la clave automáticamente si se detecta en un repositorio público.

1. Dentro de la sección **Cuentas de servicio**, haz clic en el email de la cuenta creada.
2. Ve a la pestaña **Claves (Keys)**.
3. Haz clic en **Agregar clave > Crear clave nueva**.
4. Selecciona el formato **JSON** y descárgalo.
5. Renombra el archivo (ej. `drive-credentials.json`) y guárdalo en la raíz de tu proyecto.
6. **Añade el archivo a tu `.gitignore`**:
   ```text
   drive-credentials.json
