# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run the app: `python server.py` (or `python server.py <port>`; defaults to 8000 and auto-increments if the port is busy). Opens the browser automatically.
- No install step: `server.py` uses only the Python standard library (`http.server`, `sqlite3`); `index.html` is vanilla HTML/CSS/JS with no bundler or npm dependencies. There is no build, lint, or test command in this project.
- Inspect/query the data directly with any SQLite client, e.g. `sqlite3 cronograma.sqlite`.
- To force a full reseed from the original dataset, stop the server, delete `cronograma.sqlite`, and run `python server.py` again (or use the "Restablecer" button in the UI, which calls `POST /api/reset`).

## Architecture

Two files, no framework on either side:

- **`server.py`** — stdlib-only HTTP server. Serves `index.html` at `/` and a small JSON API under `/api/*` (see README for the endpoint table). All database access is raw parameterized SQL via `sqlite3` — there is no ORM. The `SCHEMA` string near the top defines two tables, `grupos` (Gantt sections) and `tareas` (Gantt rows, `grupo_uid` FK with `ON DELETE CASCADE`). `SEED_JSON` embeds the original Excel-derived dataset (9 groups / 66 tasks) and is only used by `seed()` when `grupos` is empty (first run) or after `/api/reset`. A single `DB_LOCK` serializes writes across request threads since `ThreadingTCPServer` handles requests concurrently.
- **`index.html`** — single-file front-end (inline `<style>`/`<script>`, no build step). `DATA` is an in-memory mirror of the database: it's fully replaced from `GET /api/data` on load, and every user action (create/edit/delete a task, rename/delete a section, move a task between sections, reset) calls the matching endpoint through the `apiGet/apiPost/apiPut/apiDelete` helpers *before* patching `DATA` locally and re-rendering — the server is always the source of truth, the local copy is just a rendering cache.
- **Resilience**: `setServerStatus()` shows a full-screen `#conn-error` overlay and polls every 4s (`setInterval`) whenever `/api/data` fails, so the page degrades gracefully if `server.py` isn't running (e.g. opened via `file://`) instead of rendering a broken/empty Gantt.
- **Rendering**: the Gantt is hand-rolled DOM, not canvas/SVG/a charting library. `computeRange()` derives the visible day span from the min/max task dates in `DATA`; `renderHeader()` and `renderBody()` rebuild the sticky meta-columns + absolutely-positioned day-bars on every change. Category colors/labels (`CATEGORIAS`) and status colors (`ESTADOS`) are plain object constants near the top of the `<script>` — that's the single place to add a new Gantt category or task status.
- **IDs**: group uids look like `g<timestamp>`, task uids like `<grupo_uid>t<timestamp-suffix>`, both minted server-side in `server.py` (`next_group_uid`/`next_task_uid`), never client-side.

## Branding

Colors and typography follow the Farmacias Peruanas brand palette (defined as CSS custom properties at the top of the `<style>` block in `index.html`: `--red`, `--red-dk`, `--amber`, `--ink-ti`, `--g1`/`--g2`/`--g3`, font `Plus Jakarta Sans`). Keep new UI within this palette rather than introducing new colors.
