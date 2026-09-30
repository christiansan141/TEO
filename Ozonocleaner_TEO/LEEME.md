# Ozonocleaner_TEO · propuestas de frontend

Ozonizador de ambientes con la misma tarjeta que Teo: un relé, sensores táctiles y una OLED.
La app elige el **área**, calcula el **tiempo**, permite **programar por calendario** y envía la orden.

| Carpeta / archivo | Qué es |
|---|---|
| `index.html` | Comparador: vistas previas vivas de las tres propuestas, ideas de valor, bocetos, colores y logos |
| `propuesta-1-panel.html` | Panel de una pantalla: plano del área, salida central y programación |
| `propuesta-2-habitacion.html` | Se dibuja la habitación arrastrando la esquina; dial de tiempo; pestañas |
| `propuesta-3-agenda.html` | Calendario primero, próxima sesión y botón «Ozonizar ahora» |
| `bocetos/` | Wireframes de las tres propuestas y borrador de las pantallas OLED |
| `colores/` | `paleta.svg` y `tokens.css` (variables de color, claro y nocturno) |
| `logos/` | Logo claro y oscuro, molécula O₃, iconos de la app |
| `_src/` | Fuentes. `python3 _src/build.py` regenera todo lo anterior |

Cada HTML es un solo archivo, sin dependencias, como Teo. No edite los HTML a mano: cambie `_src/` y regenere.

## Lo que es provisional
- **Fórmula de tiempo:** `minutos = área × altura × factor`. Valores iniciales: altura 2.5 m, factor 0.60 min/m³, tope 120 min. Se editan en la app.
- **Protocolo Bluetooth:** se reutilizan los UUID y códigos de Teo (relé, temporizador, paro, estado y quién manda). Deben confirmarse con el firmware nuevo.
- **Programación:** solo se guarda en el teléfono y dispara con la página abierta. Para que corra sin la app la tarjeta necesita reloj (RTC o NTP) y una orden nueva en el protocolo.
- **OLED y sensores táctiles:** las pantallas de `bocetos/boceto-oled-pantallas.svg` son un borrador; las teclas y los textos se confirman con el hardware.
