# Cronograma Gantt TI — Farmacias Peruanas

Web interna para visualizar y editar el cronograma de integraciones de la
migración a SAP HANA (Área TI). Es un proyecto sin frameworks ni
dependencias externas: un servidor Python (solo librería estándar) que
sirve una página HTML/CSS/JS y persiste todo en una base de datos SQLite,
con SQL escrito a mano (sin ORM).

## Requisitos

- Python 3.8 o superior. No requiere `pip install` de nada.

## Cómo ejecutarlo

**Opción más simple (Windows):** haz doble clic en `iniciar.bat`. Detecta
Python automáticamente y abre el navegador solo. Si no tienes Python
instalado, el mismo archivo te avisa y te da el link de descarga.

**Opción manual (cualquier sistema operativo):**

```bash
python server.py
```

Esto:
1. Crea `cronograma.sqlite` junto a `server.py` si no existe, y la llena
   con las 9 secciones / 66 actividades originales del Excel del proyecto.
2. Levanta un servidor en `http://localhost:8000` (o el primer puerto
   libre a partir de ahí).
3. Abre el navegador automáticamente en esa URL.

Para usar otro puerto: `python server.py 9000`.
Para detener el servidor: `Ctrl+C` en la terminal.

## Arquitectura

- **`server.py`**: servidor HTTP (`http.server`/`socketserver`, sin
  frameworks) que expone una API JSON en `/api/*` y sirve `index.html` en
  `/`. Todas las consultas a `cronograma.sqlite` son SQL crudo vía el
  módulo `sqlite3` de la librería estándar (sin SQLAlchemy ni ningún ORM).
- **`index.html`**: front-end de una sola página (HTML + CSS + JS
  vanilla, sin build step ni dependencias de npm). Dibuja el diagrama de
  Gantt, los KPIs, filtros y el modal de edición, y llama a la API del
  servidor (`fetch`) para leer y guardar cada cambio.
- **`cronograma.sqlite`**: base de datos generada en el primer arranque
  (no se versiona, ver `.gitignore`).

## API

| Método | Ruta                | Descripción                                   |
|--------|---------------------|------------------------------------------------|
| GET    | `/api/data`         | Devuelve todas las secciones y actividades      |
| POST   | `/api/groups`       | Crea una sección (`{titulo}`)                   |
| PUT    | `/api/groups/:uid`  | Renombra una sección (`{titulo}`)               |
| DELETE | `/api/groups/:uid`  | Elimina una sección y sus actividades           |
| POST   | `/api/tasks`        | Crea una actividad (requiere `grupo_uid`)       |
| PUT    | `/api/tasks/:uid`   | Actualiza campos de una actividad               |
| DELETE | `/api/tasks/:uid`   | Elimina una actividad                           |
| POST   | `/api/reset`        | Borra todo y vuelve a sembrar los datos originales |

## Respaldo / uso en equipo

Toda la información vive en `cronograma.sqlite`. Para compartir el estado
actual con alguien más, copia esa carpeta completa (o al menos ese
archivo); esa persona ejecuta `python server.py` en su propia máquina y
verá los mismos datos. El archivo también se puede abrir con cualquier
visor de SQLite (por ejemplo, DB Browser for SQLite) para consultas
manuales.
