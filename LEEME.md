# Carpeta de publicación

Esto es **exactamente** lo que va a GitHub Pages, ni un archivo más ni uno menos.
Los seis archivos van en la **raíz** del repositorio, sin carpetas.

| Archivo | Para qué |
|---|---|
| `index.html` | La puerta de entrada: manda a la app. Hace que la URL del QR sea limpia |
| `termostato-1-rele.html` | La app entera: diseño, lógica y Bluetooth en un solo archivo |
| `termostato-1-rele.webmanifest` | Lo que la convierte en app instalable, con nombre e icono |
| `sw.js` | Hace que funcione sin señal una vez abierta |
| `icono-app-oscuro.svg` | Icono para Android (va a sangre, Android le pone su máscara) |
| `icono-app-redondeado.svg` | Icono para escritorio y iOS (ya viene con esquinas redondeadas) |

`actualizar.bat` y este `LEEME.md` **no se suben**: son herramientas de aquí.

---

## Publicar por primera vez

1. Repositorio nuevo en <https://github.com/new>
   - Nombre: `teo` — sale en la dirección, en minúsculas
   - **Public**
   - Marca *Add a README file*
   - **Create repository**

2. **Add file → Upload files**, arrastra los **seis** archivos de esta carpeta,
   y abajo **Commit changes**.

3. **Settings → Pages**
   - Source: *Deploy from a branch*
   - Branch: `main`, carpeta `/ (root)`
   - **Save**

4. Espera 1–2 minutos, recarga la página y arriba sale tu dirección:
   `https://TU-USUARIO.github.io/teo/`

Esa es la dirección del producto. La que va en el QR del equipo.

---

## Volver a publicar después de un cambio

1. Cambia lo que sea en `app/termostato-1-rele.html`.
2. **Sube el número de versión** en `app/sw.js`:
   `const CACHE = "tk-termostato-v4"` → `v5`.
   Si no lo haces, los teléfonos que ya instalaron la app **siguen viendo la
   vieja** aunque subas la nueva.
3. Doble clic en `actualizar.bat` para refrescar esta carpeta.
4. En GitHub: **Add file → Upload files**, arrastra otra vez, Commit.

---

## Comprobación rápida después de publicar

- Abre `https://TU-USUARIO.github.io/teo/` en el PC → debe entrar sola a la app
  en modo demostración.
- Ábrela en el celular con **Chrome** → menú `⋮` → **Instalar aplicación**.
- Con la placa encendida, botón **Conectar** → debe salir **TEO**.

Si en el celular no aparece el equipo al conectar: enciende el **Bluetooth** y
la **ubicación** del teléfono. Android exige la ubicación activada para poder
escanear BLE, aunque la app no la use para nada.
