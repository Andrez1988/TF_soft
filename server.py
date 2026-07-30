#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor local para el Cronograma Gantt TI - Farmacias Peruanas.
Usa solo la biblioteca estandar de Python: http.server + sqlite3 (SQL crudo, sin ORM).

Uso:
    python3 server.py [puerto]

Luego abre en el navegador la URL que se imprime en consola (por defecto
http://localhost:8000). El servidor sirve la pagina y expone una API JSON
que lee y escribe directamente sobre una base de datos SQLite
(cronograma.sqlite, se crea automaticamente junto a este script).
"""
import http.server
import socketserver
import sqlite3
import json
import os
import re
import sys
import threading
import webbrowser
import urllib.parse
import io
import zipfile
import hashlib
import hmac

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cronograma.sqlite")
HTML_PATH = os.path.join(BASE_DIR, "index.html")

DB_LOCK = threading.Lock()

SEED_JSON = '[{"uid": "g1", "titulo": "Planificación IA", "tasks": [{"uid": "g1t1", "n": 1, "id": "1-IA", "corporativo": "", "categoria": "IA", "proceso": "", "actividad": "Creación de Agentes", "integraciones": "", "microservicio": "", "responsable": "", "estado": "No iniciado", "inicio": "2026-07-06", "duracion": 5, "fin": "2026-07-10", "avance": 0}, {"uid": "g1t2", "n": 2, "id": "2-IA", "corporativo": "", "categoria": "IA", "proceso": "", "actividad": "Creación de Modelo de Negocio (Arquitectura/Mod. de Datos/Glosario)", "integraciones": "", "microservicio": "", "responsable": "", "estado": "No iniciado", "inicio": "2026-07-06", "duracion": 5, "fin": "2026-07-10", "avance": 0}, {"uid": "g1t3", "n": 3, "id": "3-IA", "corporativo": "", "categoria": "IA", "proceso": "", "actividad": "Creación de Contratos de APIS", "integraciones": "", "microservicio": "", "responsable": "", "estado": "No iniciado", "inicio": "2026-07-06", "duracion": 5, "fin": "2026-07-10", "avance": 0}]}, {"uid": "g2", "titulo": "DM - Data Management (Materiales)", "tasks": [{"uid": "g2t1", "n": 1, "id": "28-DM", "corporativo": "INT066", "categoria": "DM", "proceso": "Datos Maestros", "actividad": "Creación de Materiales", "integraciones": "MDW -> PMM", "microservicio": "Nuevo", "responsable": "Todo el Equipo", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 4, "fin": "2026-07-16", "avance": 0}, {"uid": "g2t2", "n": 2, "id": "28-DM", "corporativo": "INT066", "categoria": "DM", "proceso": "Datos Maestros", "actividad": "Creación de Materiales", "integraciones": "MDW -> S4", "microservicio": "Nuevo", "responsable": "Todo el Equipo", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 4, "fin": "2026-07-16", "avance": 0}, {"uid": "g2t3", "n": 3, "id": "29-DM", "corporativo": "INT066", "categoria": "DM", "proceso": "Datos Maestros", "actividad": "Modificación de Materiales", "integraciones": "MDW -> PMM", "microservicio": "Nuevo", "responsable": "Todo el Equipo", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 4, "fin": "2026-07-16", "avance": 0}, {"uid": "g2t4", "n": 4, "id": "29-DM", "corporativo": "INT066", "categoria": "DM", "proceso": "Datos Maestros", "actividad": "Modificación de Materiales", "integraciones": "MDW -> S4", "microservicio": "Nuevo", "responsable": "Todo el Equipo", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 4, "fin": "2026-07-16", "avance": 0}]}, {"uid": "g3", "titulo": "CU1 - Ventas / Distribución", "tasks": [{"uid": "g3t1", "n": 5, "id": "2-CU1", "corporativo": "INT087/INT094", "categoria": "CU1", "proceso": "Venta", "actividad": "Venta B2B ORR", "integraciones": "S4 -> MDW", "microservicio": "fps-bus-ms-psys-qs-order-sapqs", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t2", "n": 6, "id": "2-CU1", "corporativo": "INT087/INT094", "categoria": "CU1", "proceso": "Venta", "actividad": "Venta B2B ORR", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-ms-psys-qs-order-pmm", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t3", "n": 7, "id": "3-CU1", "corporativo": "INT088", "categoria": "CU1", "proceso": "Venta", "actividad": "Consulta TRF Number", "integraciones": "S4 -> MDW", "microservicio": "fps-bus-ms-psys-qs-ped-create-reserved-sap", "responsable": "Gaby Marapi", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t4", "n": 8, "id": "3-CU1", "corporativo": "INT088", "categoria": "CU1", "proceso": "Venta", "actividad": "Consulta TRF Number", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-ms-psys-qs-ped-create-reserved-sap", "responsable": "Gaby Marapi", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t5", "n": 9, "id": "4-CU1", "corporativo": "INT099", "categoria": "CU1", "proceso": "Venta", "actividad": "Procesa SLS Venta Cliente", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-legacy-psys-qs-sls-sapqs-ti", "responsable": "Pedro Novoa", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t6", "n": 10, "id": "4-CU1", "corporativo": "INT099", "categoria": "CU1", "proceso": "Venta", "actividad": "Procesa SLS Venta Cliente", "integraciones": "MDW -> SFTP", "microservicio": "fps-bus-legacy-psys-qs-sls-sapqs-ti", "responsable": "Pedro Novoa", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t7", "n": 11, "id": "6-CU1", "corporativo": "", "categoria": "CU1", "proceso": "Venta", "actividad": "Consulta Saldo Cliente", "integraciones": "IRT -> S4", "microservicio": "fps-bus-ms-phub-otm-app-pickup-invoice-settlement", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t8", "n": 12, "id": "7-CU1", "corporativo": "INT093", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devolución Cliente POS", "integraciones": "S4 -> MDW", "microservicio": "fps-bus-ms-psys-qs-er-get-orders-sap", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t9", "n": 13, "id": "7-CU1", "corporativo": "INT093", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devolución Cliente POS", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-ms-psys-qs-er-insert-orders-pmm", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t10", "n": 14, "id": "7-CU1", "corporativo": "INT093", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devolución Cliente POS", "integraciones": "MDW -> PHUB", "microservicio": "Nuevo", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t11", "n": 15, "id": "7-CU1", "corporativo": "INT093", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devolución Cliente POS", "integraciones": "MDW -> Monitor GR2", "microservicio": "Nuevo", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t12", "n": 16, "id": "8-CU1", "corporativo": "INT097", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devol Cliente - SVS Prima CU1", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-ms-psys-qs-er-get-order-svs-pmm (api 1)", "responsable": "Ruben Mendoza", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t13", "n": 17, "id": "8-CU1", "corporativo": "INT097", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devol Cliente - SVS Prima CU1", "integraciones": "MDW -> S4", "microservicio": "fps-bus-ms-psys-qs-er-send-svs-sap", "responsable": "Ruben Mendoza", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t14", "n": 18, "id": "9-CU1", "corporativo": "INT036", "categoria": "CU1", "proceso": "Devolución", "actividad": "NC Confirmación SUNAT SFTP", "integraciones": "S4 -> MDW", "microservicio": "fps-bus-ms-psys-qs-er-get-order-svs-pmm (api 2)", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t15", "n": 19, "id": "10-CU1", "corporativo": "INT095", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devol Cliente - Devol Intercompany IRP", "integraciones": "PHUB -> MDW -> S4", "microservicio": "fps-bus-ms-psys-qs-er-send-nc-sap", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t16", "n": 20, "id": "12-CU1", "corporativo": "INT048", "categoria": "CU1", "proceso": "Devolución", "actividad": "Devol Cliente - Venta Intercompany IRP", "integraciones": "PHUB -> MDW -> S4", "microservicio": "fps-bus-ms-psys-qs-er-send-vta-sap", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g3t17", "n": 21, "id": "13-CU1", "corporativo": "INT108", "categoria": "CU1", "proceso": "Devolución", "actividad": "DQT Recepción SLS Devol Proveedor", "integraciones": "MDW -> S4", "microservicio": "fps-bus-legacy-psys-li-pos-migo", "responsable": "Ruben Mendoza", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g3t18", "n": 22, "id": "14-CU1", "corporativo": "INT101", "categoria": "CU1", "proceso": "Devolución", "actividad": "GR Devol Proveedor DQT", "integraciones": "S4 -> Monitor GR2 (HOMO)", "microservicio": "fps-ws-sls-import", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g3t19", "n": 23, "id": "16-CU1", "corporativo": "", "categoria": "CU1", "proceso": "Devolución", "actividad": "Consulta Ingreso de Mercadería NC", "integraciones": "PHUB -> S4 (HOMO)", "microservicio": "fps-bus-ms-phub-qs-guide-client-in-distribution", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}]}, {"uid": "g4", "titulo": "TITAN - Pedidos y Devoluciones", "tasks": [{"uid": "g4t1", "n": 24, "id": "17-TITAN", "corporativo": "INT015", "categoria": "TITAN", "proceso": "Venta Prio 2", "actividad": "Anulación de Pedido", "integraciones": "PHUB / QUIMIV -> MDW", "microservicio": "Nuevo", "responsable": "Pedro Novoa", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g4t2", "n": 25, "id": "17-TITAN", "corporativo": "INT015", "categoria": "TITAN", "proceso": "Venta Prio 2", "actividad": "Anulación de Pedido", "integraciones": "MDW -> S4", "microservicio": "Nuevo", "responsable": "Pedro Novoa", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g4t3", "n": 26, "id": "18-TITAN", "corporativo": "INT100", "categoria": "TITAN", "proceso": "Venta", "actividad": "Forzado Facturación", "integraciones": "Monitor GRE2 -> S4", "microservicio": "fps-ws-guias-monitor", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g4t4", "n": 27, "id": "19-TITAN", "corporativo": "INT020 / INT091", "categoria": "TITAN", "proceso": "Venta", "actividad": "Consulta Factura", "integraciones": "Monitor GRE2 -> S4", "microservicio": "fps-ws-guias-monitor (*)", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g4t5", "n": 28, "id": "19-TITAN", "corporativo": "INT020 / INT091", "categoria": "TITAN", "proceso": "Venta", "actividad": "Consulta Factura", "integraciones": "PHUB -> S4", "microservicio": "fps-bus-ms-phub-ir-track-sls-wms-gr", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-13", "duracion": 5, "fin": "2026-07-17", "avance": 0}, {"uid": "g4t6", "n": 29, "id": "20-TITAN", "corporativo": "INT103", "categoria": "TITAN", "proceso": "Venta Prio 2", "actividad": "Anula Pedido por Posición", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-legacy-psys-send-cancel-order-sapqs", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g4t7", "n": 30, "id": "20-TITAN", "corporativo": "INT103", "categoria": "TITAN", "proceso": "Venta Prio 2", "actividad": "Anula Pedido por Posición", "integraciones": "MDW -> S4", "microservicio": "fps-bus-legacy-psys-send-cancel-order-sapqs", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g4t8", "n": 31, "id": "21-TITAN", "corporativo": "", "categoria": "TITAN", "proceso": "Devolución", "actividad": "Dev APK Crea Pedido PHUB Aplicativo", "integraciones": "PHUB -> S4 (QAS) ", "microservicio": "No Desplegado", "responsable": "Gaby Marapi", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g4t9", "n": 32, "id": "23-TITAN", "corporativo": "INT107", "categoria": "TITAN", "proceso": "Devolución", "actividad": "Crea Devol Proveedor x Discrepancia", "integraciones": "PHUB -> S4", "microservicio": "fps-bus-ms-phub-ir-track-shipto-discrepancy", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g4t10", "n": 33, "id": "25-TITAN", "corporativo": "", "categoria": "TITAN", "proceso": "Devolución", "actividad": "Dev APK Consulta Creación Pedido Devolución", "integraciones": "PHUB -> S4", "microservicio": "fps-bus-ms-phub-ir-track-request-in-distribution", "responsable": "Pedro Novoa", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}]}, {"uid": "g5", "titulo": "CU0 - Compras", "tasks": [{"uid": "g5t1", "n": 34, "id": "26-CU0", "corporativo": "INT067 / INT062", "categoria": "CU0", "proceso": "Compras", "actividad": "Crea OC F0", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-ms-psys-sp-sap-qs-oc", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g5t2", "n": 35, "id": "26-CU0", "corporativo": "INT067 / INT062", "categoria": "CU0", "proceso": "Compras", "actividad": "Crea OC F0", "integraciones": "MDW -> S4", "microservicio": "fps-bus-ms-psys-sp-sap-qs-oc", "responsable": "Luis Pastor", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g5t3", "n": 36, "id": "27-CU0", "corporativo": "INT079", "categoria": "CU0", "proceso": "Compras", "actividad": "MIGO F0", "integraciones": "MDW -> PMM", "microservicio": "fps-bus-legacy-psys-svs-sap-qs", "responsable": "Gaby Marapi", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g5t4", "n": 37, "id": "27-CU0", "corporativo": "INT079", "categoria": "CU0", "proceso": "Compras", "actividad": "MIGO F0", "integraciones": "MDW -> S4", "microservicio": "fps-bus-legacy-psys-svs-sap-qs", "responsable": "Gaby Marapi", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}]}, {"uid": "g6", "titulo": "WMS - Almacén (Inka3)", "tasks": [{"uid": "g6t1", "n": 38, "id": "30-WMS", "corporativo": "INT083", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Maestro de Producto (ITM)", "integraciones": "SFTP PMM -> MDW", "microservicio": "Nuevo", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t2", "n": 39, "id": "30-WMS", "corporativo": "INT083", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Maestro de Producto (ITM)", "integraciones": "MDW -> WMS", "microservicio": "Nuevo", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t3", "n": 40, "id": "31-WMS", "corporativo": "INT086", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Código de Barras (Item Barcode)", "integraciones": "SFTP PMM -> MDW", "microservicio": "Nuevo", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t4", "n": 41, "id": "31-WMS", "corporativo": "INT086", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Código de Barras (Item Barcode)", "integraciones": "MDW -> WMS", "microservicio": "Nuevo", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t5", "n": 42, "id": "32-WMS", "corporativo": "INT065", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Proveedor (Vendor)", "integraciones": "SFTP PMM -> MDW", "microservicio": "Nuevo", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t6", "n": 43, "id": "32-WMS", "corporativo": "INT065", "categoria": "WMS", "proceso": "Datos Maestros", "actividad": "Proveedor (Vendor)", "integraciones": "MDW -> WMS", "microservicio": "Nuevo", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t7", "n": 44, "id": "33-WMS", "corporativo": "INT037", "categoria": "WMS", "proceso": "QSC", "actividad": "Órdenes ORR", "integraciones": "S4 -> MDW", "microservicio": "Nuevo", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t8", "n": 45, "id": "33-WMS", "corporativo": "INT037", "categoria": "WMS", "proceso": "QSC", "actividad": "Órdenes ORR", "integraciones": "MDW -> WMS", "microservicio": "Nuevo", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t9", "n": 46, "id": "34-WMS", "corporativo": "INT078 / INT081", "categoria": "WMS", "proceso": "QSC", "actividad": "Purchase Order (POS)", "integraciones": "S4 -> MDW", "microservicio": "Nuevo", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t10", "n": 47, "id": "34-WMS", "corporativo": "INT078 / INT081", "categoria": "WMS", "proceso": "QSC", "actividad": "Purchase Order (POS)", "integraciones": "MDW -> WMS", "microservicio": "Nuevo", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t11", "n": 48, "id": "35-WMS", "corporativo": "INT079", "categoria": "WMS", "proceso": "QSC", "actividad": "SLS", "integraciones": "WMS -> MDW", "microservicio": "Nuevo", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t12", "n": 49, "id": "35-WMS", "corporativo": "INT079", "categoria": "WMS", "proceso": "QSC", "actividad": "SLS", "integraciones": "MDW -> SFTP PMM", "microservicio": "Nuevo", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t13", "n": 50, "id": "36-WMS", "corporativo": "INT084", "categoria": "WMS", "proceso": "QSC", "actividad": "IHT", "integraciones": "WMS -> MDW", "microservicio": "Nuevo", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t14", "n": 51, "id": "36-WMS", "corporativo": "INT084", "categoria": "WMS", "proceso": "QSC", "actividad": "IHT", "integraciones": "MDW -> S4", "microservicio": "Nuevo", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t15", "n": 52, "id": "37-WMS", "corporativo": "INT074", "categoria": "WMS", "proceso": "QSC", "actividad": "SVS", "integraciones": "WMS -> MDW", "microservicio": "Nuevo", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}, {"uid": "g6t16", "n": 53, "id": "37-WMS", "corporativo": "INT074", "categoria": "WMS", "proceso": "QSC", "actividad": "SVS", "integraciones": "MDW -> S4", "microservicio": "Nuevo", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-20", "duracion": 5, "fin": "2026-07-24", "avance": 0}]}, {"uid": "g7", "titulo": "DM - Data Homologación", "tasks": [{"uid": "g7t1", "n": 54, "id": "42-DM", "corporativo": "", "categoria": "DM", "proceso": "Datos Maestros", "actividad": "Actualización DM para Homologación", "integraciones": "MDW -> PMM", "microservicio": "Nuevo", "responsable": "", "estado": "No iniciado", "inicio": null, "duracion": null, "fin": null, "avance": 0}]}, {"uid": "g8", "titulo": "B2B - QS Consumo", "tasks": [{"uid": "g8t1", "n": 55, "id": "38-B2B-QSC", "corporativo": "INT073", "categoria": "WMS", "proceso": "B2B", "actividad": "OCO", "integraciones": "MDW -> SFTP PMM (1)", "microservicio": "Prioridad Baja", "responsable": "Ruben Mendoza", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g8t2", "n": 56, "id": "38-B2B-QSC", "corporativo": "INT073", "categoria": "WMS", "proceso": "B2B", "actividad": "OCO", "integraciones": "MDW -> SFTP PMM (2)", "microservicio": "Prioridad Baja", "responsable": "Ruben Mendoza", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}]}, {"uid": "g9", "titulo": "B2B - FP Mayorista", "tasks": [{"uid": "g9t1", "n": 57, "id": "41-B2B-FP", "corporativo": "INT073", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "OCO", "integraciones": "MDW -> SFTP PMM (1)", "microservicio": "Prioridad Baja", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t2", "n": 58, "id": "41-B2B-FP", "corporativo": "INT073", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "OCO", "integraciones": "MDW -> SFTP PMM (2)", "microservicio": "Prioridad Baja", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t3", "n": 59, "id": "41-B2B-FP", "corporativo": "INT073", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "OCO", "integraciones": "PHUB -> SFTP PMM", "microservicio": "Prioridad Baja", "responsable": "Isaac Jurado", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t4", "n": 60, "id": "45-B2B-FP", "corporativo": "", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "Maestro Productos", "integraciones": "PHUB -> PMM", "microservicio": "Prioridad Baja", "responsable": "Jorge Villacorta", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t5", "n": 61, "id": "46-B2B-FP", "corporativo": "", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "Proveedores", "integraciones": "PHUB -> PMM", "microservicio": "Prioridad Baja", "responsable": "Juan Seperak", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t6", "n": 62, "id": "47-B2B-FP", "corporativo": "", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "EAN Principal", "integraciones": "PHUB -> PMM", "microservicio": "Prioridad Baja", "responsable": "Joseph Salazar", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}, {"uid": "g9t7", "n": 63, "id": "48-B2B-FP", "corporativo": "", "categoria": "B2B-FP", "proceso": "B2B", "actividad": "EAN Secundario", "integraciones": "PHUB -> PMM", "microservicio": "Prioridad Baja", "responsable": "Hellen Menacho", "estado": "No iniciado", "inicio": "2026-07-27", "duracion": 5, "fin": "2026-07-31", "avance": 0}]}]'

SCHEMA = """
CREATE TABLE IF NOT EXISTS grupos (
  uid    TEXT PRIMARY KEY,
  titulo TEXT NOT NULL,
  orden  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tareas (
  uid            TEXT PRIMARY KEY,
  grupo_uid      TEXT NOT NULL REFERENCES grupos(uid) ON DELETE CASCADE,
  n              INTEGER,
  ident          TEXT,
  corporativo    TEXT,
  categoria      TEXT,
  proceso        TEXT,
  actividad      TEXT NOT NULL,
  integraciones  TEXT,
  microservicio  TEXT,
  responsable    TEXT,
  estado         TEXT,
  estado_prueba  TEXT DEFAULT 'No iniciado',
  inicio         TEXT,
  duracion       INTEGER,
  fin            TEXT,
  avance         INTEGER DEFAULT 0,
  dependiente    TEXT,
  owner_ku       TEXT,
  orden          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS owners_ku (
  uid    TEXT PRIMARY KEY,
  nombre TEXT NOT NULL UNIQUE,
  orden  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS usuarios (
  usuario       TEXT PRIMARY KEY,
  password_hash TEXT NOT NULL
);
"""

def _hash_password(p):
    """Hash SHA-256 con sal fija; suficiente para las credenciales basicas de este proyecto."""
    return hashlib.sha256(("gantt-ti::" + p).encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def migrate(conn):
    """Agrega columnas nuevas a bases de datos creadas por versiones anteriores."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(tareas)").fetchall()}
    if "dependiente" not in cols:
        conn.execute("ALTER TABLE tareas ADD COLUMN dependiente TEXT")
        conn.commit()
    if "owner_ku" not in cols:
        conn.execute("ALTER TABLE tareas ADD COLUMN owner_ku TEXT")
        conn.commit()
    if "estado_prueba" not in cols:
        conn.execute("ALTER TABLE tareas ADD COLUMN estado_prueba TEXT DEFAULT 'No iniciado'")
        conn.execute("UPDATE tareas SET estado_prueba='No iniciado' WHERE estado_prueba IS NULL")
        conn.commit()

def seed_owners(conn):
    """Puebla el catalogo de OWNER - KU con los responsables reales del dataset."""
    data = json.loads(SEED_JSON)
    nombres = []
    vistos = set()
    for g in data:
        for t in g["tasks"]:
            r = (t.get("responsable") or "").strip()
            if r and r not in vistos:
                vistos.add(r)
                nombres.append(r)
    for i, nombre in enumerate(nombres):
        conn.execute(
            "INSERT OR IGNORE INTO owners_ku (uid, nombre, orden) VALUES (?,?,?)",
            ("own" + str(i + 1), nombre, i),
        )
    conn.commit()

def init_db():
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        migrate(conn)
        row = conn.execute("SELECT COUNT(*) AS c FROM grupos").fetchone()
        if row["c"] == 0:
            seed(conn)
        orow = conn.execute("SELECT COUNT(*) AS c FROM owners_ku").fetchone()
        if orow["c"] == 0:
            seed_owners(conn)
        urow = conn.execute("SELECT COUNT(*) AS c FROM usuarios").fetchone()
        if urow["c"] == 0:
            conn.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                ("admin", _hash_password("1234")),
            )
            conn.commit()
    finally:
        conn.close()

def seed(conn):
    data = json.loads(SEED_JSON)
    g_orden = 0
    for g in data:
        conn.execute(
            "INSERT INTO grupos (uid, titulo, orden) VALUES (?, ?, ?)",
            (g["uid"], g["titulo"], g_orden),
        )
        t_orden = 0
        for t in g["tasks"]:
            conn.execute(
                """INSERT INTO tareas
                   (uid, grupo_uid, n, ident, corporativo, categoria, proceso, actividad,
                    integraciones, microservicio, responsable, estado, estado_prueba, inicio, duracion, fin, avance, dependiente, owner_ku, orden)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    t["uid"], g["uid"], t.get("n"), t.get("id"), t.get("corporativo"),
                    t.get("categoria"), t.get("proceso"), t.get("actividad"),
                    t.get("integraciones"), t.get("microservicio"), t.get("responsable"),
                    t.get("estado"), t.get("estado_prueba") or "No iniciado", t.get("inicio"), t.get("duracion"), t.get("fin"),
                    t.get("avance") or 0, t.get("dependiente"), t.get("owner_ku"), t_orden,
                ),
            )
            t_orden += 1
        g_orden += 1
    conn.commit()

def reset_db():
    conn = get_conn()
    try:
        conn.execute("DELETE FROM tareas")
        conn.execute("DELETE FROM grupos")
        conn.commit()
        seed(conn)
    finally:
        conn.close()

def fetch_all_data():
    conn = get_conn()
    try:
        grupos = conn.execute("SELECT * FROM grupos ORDER BY orden, rowid").fetchall()
        tareas = conn.execute("SELECT * FROM tareas ORDER BY orden, rowid").fetchall()
        owners = conn.execute("SELECT nombre FROM owners_ku ORDER BY orden, nombre").fetchall()
    finally:
        conn.close()
    by_group = {}
    for g in grupos:
        by_group[g["uid"]] = {"uid": g["uid"], "titulo": g["titulo"], "tasks": []}
    for t in tareas:
        if t["grupo_uid"] not in by_group:
            continue
        by_group[t["grupo_uid"]]["tasks"].append({
            "uid": t["uid"], "n": t["n"], "id": t["ident"], "corporativo": t["corporativo"],
            "categoria": t["categoria"], "proceso": t["proceso"], "actividad": t["actividad"],
            "integraciones": t["integraciones"], "microservicio": t["microservicio"],
            "responsable": t["responsable"], "estado": t["estado"], "estado_prueba": t["estado_prueba"], "inicio": t["inicio"],
            "duracion": t["duracion"], "fin": t["fin"], "avance": t["avance"],
            "dependiente": t["dependiente"], "owner_ku": t["owner_ku"],
        })
    return {
        "groups": [by_group[g["uid"]] for g in grupos],
        "owners": [o["nombre"] for o in owners],
    }

def next_task_uid(conn, grupo_uid):
    row = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE grupo_uid=?", (grupo_uid,)).fetchone()
    return "%st%d" % (grupo_uid, row["c"] + 1) if False else grupo_uid + "t" + str(int(__import__("time").time()*1000))[-8:]

def next_group_uid(conn):
    return "g" + str(int(__import__("time").time()*1000))


# ── Exportacion a Excel (.xlsx) usando solo la stdlib (zipfile + XML OOXML) ──
XLSX_COLUMNS = [
    "Sección", "N°", "ID", "Corporativo", "Categoría", "Proceso", "Actividad",
    "Integraciones", "Microservicio", "Responsable", "Estado", "Fecha Inicio",
    "Duración (d)", "Fecha Fin", "% Avance", "Dependiente", "Estado de Prueba", "Owner - KU",
]
# Anchos de columna aproximados (en "caracteres" de Excel).
XLSX_WIDTHS = [26, 5, 10, 16, 14, 16, 34, 22, 40, 18, 14, 12, 12, 12, 9, 18, 16, 18]

def _xlsx_col_letter(n):
    """1 -> A, 2 -> B, 27 -> AA ..."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _xml_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def _xlsx_rows_from_data(data):
    rows = [list(XLSX_COLUMNS)]
    for g in data.get("groups", []):
        for t in g.get("tasks", []):
            rows.append([
                g.get("titulo"), t.get("n"), t.get("id"), t.get("corporativo"),
                t.get("categoria"), t.get("proceso"), t.get("actividad"),
                t.get("integraciones"), t.get("microservicio"), t.get("responsable"),
                t.get("estado"), t.get("inicio"), t.get("duracion"), t.get("fin"),
                t.get("avance"), t.get("dependiente"), t.get("estado_prueba"), t.get("owner_ku"),
            ])
    return rows

def _xlsx_sheet_cell(ref, value, header=False):
    style = ' s="1"' if header else ""
    if value is None or value == "":
        return '<c r="%s"%s/>' % (ref, style)
    if isinstance(value, bool):
        value = str(value)
    if isinstance(value, (int, float)):
        return '<c r="%s"%s><v>%s</v></c>' % (ref, style, value)
    txt = _xml_escape(value)
    return '<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, style, txt)

def build_xlsx(data):
    rows = _xlsx_rows_from_data(data)
    ncols = len(XLSX_COLUMNS)

    cols_xml = "<cols>" + "".join(
        '<col min="%d" max="%d" width="%d" customWidth="1"/>' % (i + 1, i + 1, XLSX_WIDTHS[i])
        for i in range(ncols)
    ) + "</cols>"

    body = []
    for r_idx, row in enumerate(rows, start=1):
        header = (r_idx == 1)
        cells = "".join(
            _xlsx_sheet_cell(_xlsx_col_letter(c_idx) + str(r_idx), row[c_idx - 1], header)
            for c_idx in range(1, ncols + 1)
        )
        body.append('<row r="%d">%s</row>' % (r_idx, cells))
    sheet_data = "<sheetData>" + "".join(body) + "</sheetData>"
    dimension = '<dimension ref="A1:%s%d"/>' % (_xlsx_col_letter(ncols), len(rows))
    freeze = ('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
              'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + dimension + freeze + cols_xml + sheet_data + '</worksheet>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Cronograma" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFB32515"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
        '</styleSheet>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()


# ── Exportacion a Word (.docx) usando solo la stdlib (zipfile + XML WordprocessingML) ──
DOCX_COLUMNS = ["N°", "ID", "Actividad", "Fechas", "Corporativo", "Microservicio", "% Avance", "Estado", "Dependiente", "Estado de Prueba", "Owner - KU"]
# Anchos de columna en twips; suman ~15000 (A4 horizontal con margenes de 720 deja ~15400 utiles).
DOCX_WIDTHS = [450, 900, 2700, 1500, 1000, 2600, 700, 1050, 1350, 1350, 1350]

def _docx_p(text, bold=False, size=None, color=None, space_after=120):
    rpr = ""
    if bold:
        rpr += "<w:b/>"
    if size:
        rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size)
    if color:
        rpr += '<w:color w:val="%s"/>' % color
    return ('<w:p><w:pPr><w:spacing w:after="%d"/></w:pPr>'
            '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            % (space_after, rpr, _xml_escape(text)))

def _docx_tc(text, width, header=False):
    shd = '<w:shd w:val="clear" w:color="auto" w:fill="B32515"/>' if header else ""
    tcpr = ('<w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s<w:vAlign w:val="center"/></w:tcPr>'
            % (width, shd))
    rpr = ('<w:b/><w:color w:val="FFFFFF"/>' if header else "") + '<w:sz w:val="16"/><w:szCs w:val="16"/>'
    txt = "" if text is None else str(text)
    p = ('<w:p><w:pPr><w:spacing w:after="0"/></w:pPr>'
         '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
         % (rpr, _xml_escape(txt)))
    return "<w:tc>%s%s</w:tc>" % (tcpr, p)

def _docx_task_row(t):
    fechas = ""
    if t.get("inicio") or t.get("fin"):
        fechas = "%s → %s" % (t.get("inicio") or "—", t.get("fin") or "—")
        if t.get("duracion"):
            fechas += " (%s d)" % t.get("duracion")
    avance = t.get("avance")
    avance = "%s%%" % avance if avance not in (None, "") else ""
    valores = [t.get("n"), t.get("id"), t.get("actividad"), fechas, t.get("corporativo"),
               t.get("microservicio"), avance, t.get("estado"), t.get("dependiente"), t.get("estado_prueba"), t.get("owner_ku")]
    return "<w:tr>" + "".join(_docx_tc(v, DOCX_WIDTHS[i]) for i, v in enumerate(valores)) + "</w:tr>"

def build_docx(data):
    borders = "".join(
        '<w:%s w:val="single" w:sz="4" w:space="0" w:color="D9D9D9"/>' % b
        for b in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    tblpr = ('<w:tblPr><w:tblW w:w="0" w:type="auto"/>'
             '<w:tblBorders>%s</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>' % borders)
    grid = "<w:tblGrid>" + "".join('<w:gridCol w:w="%d"/>' % w for w in DOCX_WIDTHS) + "</w:tblGrid>"
    header_row = ('<w:tr><w:trPr><w:tblHeader/></w:trPr>'
                  + "".join(_docx_tc(c, DOCX_WIDTHS[i], header=True) for i, c in enumerate(DOCX_COLUMNS))
                  + "</w:tr>")

    cuerpo = [
        _docx_p("Cronograma Gantt — Migración a SAP HANA", bold=True, size=32, color="B32515", space_after=40),
        _docx_p("Farmacias Peruanas · Área TI · Integraciones", size=18, color="7A7B7E", space_after=240),
    ]
    for g in data.get("groups", []):
        tareas = g.get("tasks", [])
        cuerpo.append(_docx_p("%s (%d actividades)" % (g.get("titulo") or "", len(tareas)),
                              bold=True, size=22, color="8B0000", space_after=80))
        filas = "".join(_docx_task_row(t) for t in tareas)
        cuerpo.append("<w:tbl>%s%s%s%s</w:tbl>" % (tblpr, grid, header_row, filas))
        cuerpo.append(_docx_p("", space_after=200))

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>' + "".join(cuerpo) +
        '<w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
        '<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="360" w:footer="360"/>'
        '</w:sectPr></w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", document)
    return buf.getvalue()


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "CronogramaGanttFP/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._send_json({"error": "index.html no encontrado junto a server.py"}, 404)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._send_html(HTML_PATH)
            return
        if path == "/api/data":
            with DB_LOCK:
                self._send_json(fetch_all_data())
            return
        if path == "/api/health":
            self._send_json({"ok": True})
            return
        if path == "/api/export.xlsx":
            with DB_LOCK:
                data = fetch_all_data()
            blob = build_xlsx(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", 'attachment; filename="cronograma-gantt-ti.xlsx"')
            self.send_header("Content-Length", str(len(blob)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(blob)
            return
        if path == "/api/export.docx":
            with DB_LOCK:
                data = fetch_all_data()
            blob = build_docx(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.send_header("Content-Disposition", 'attachment; filename="cronograma-gantt-ti.docx"')
            self.send_header("Content-Length", str(len(blob)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(blob)
            return
        self._send_json({"error": "ruta no encontrada"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        if path == "/api/login":
            usuario = (body.get("usuario") or "").strip()
            password = body.get("password") or ""
            with DB_LOCK:
                conn = get_conn()
                try:
                    row = conn.execute("SELECT password_hash FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
                finally:
                    conn.close()
            ok = row is not None and hmac.compare_digest(row["password_hash"], _hash_password(password))
            if ok:
                self._send_json({"ok": True, "usuario": usuario})
            else:
                self._send_json({"error": "usuario o contraseña incorrectos"}, 401)
            return

        if path == "/api/groups":
            titulo = (body.get("titulo") or "Nueva seccion").strip()
            with DB_LOCK:
                conn = get_conn()
                try:
                    uid = next_group_uid(conn)
                    row = conn.execute("SELECT COALESCE(MAX(orden), -1) AS m FROM grupos").fetchone()
                    conn.execute("INSERT INTO grupos (uid, titulo, orden) VALUES (?,?,?)", (uid, titulo, row["m"] + 1))
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"uid": uid})
            return

        if path == "/api/tasks":
            grupo_uid = body.get("grupo_uid")
            if not grupo_uid:
                self._send_json({"error": "grupo_uid requerido"}, 400)
                return
            with DB_LOCK:
                conn = get_conn()
                try:
                    exists = conn.execute("SELECT 1 FROM grupos WHERE uid=?", (grupo_uid,)).fetchone()
                    if not exists:
                        self._send_json({"error": "seccion no existe"}, 400)
                        conn.close()
                        return
                    uid = next_task_uid(conn, grupo_uid)
                    row = conn.execute("SELECT COALESCE(MAX(orden), -1) AS m FROM tareas WHERE grupo_uid=?", (grupo_uid,)).fetchone()
                    nrow = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE grupo_uid=?", (grupo_uid,)).fetchone()
                    conn.execute(
                        """INSERT INTO tareas
                           (uid, grupo_uid, n, ident, corporativo, categoria, proceso, actividad,
                            integraciones, microservicio, responsable, estado, estado_prueba, inicio, duracion, fin, avance, dependiente, owner_ku, orden)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            uid, grupo_uid, nrow["c"] + 1, body.get("id"), body.get("corporativo"),
                            body.get("categoria"), body.get("proceso"), body.get("actividad", ""),
                            body.get("integraciones"), body.get("microservicio"), body.get("responsable"),
                            body.get("estado", "No iniciado"), body.get("estado_prueba", "No iniciado"), body.get("inicio"), body.get("duracion"),
                            body.get("fin"), body.get("avance") or 0, body.get("dependiente"), body.get("owner_ku"), row["m"] + 1,
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"uid": uid})
            return

        if path == "/api/owners":
            nombre = (body.get("nombre") or "").strip()
            if not nombre:
                self._send_json({"error": "nombre requerido"}, 400)
                return
            with DB_LOCK:
                conn = get_conn()
                try:
                    row = conn.execute("SELECT COALESCE(MAX(orden), -1) AS m FROM owners_ku").fetchone()
                    uid = "own" + str(int(__import__("time").time() * 1000))
                    conn.execute(
                        "INSERT OR IGNORE INTO owners_ku (uid, nombre, orden) VALUES (?,?,?)",
                        (uid, nombre, row["m"] + 1),
                    )
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"nombre": nombre})
            return

        if path == "/api/reset":
            with DB_LOCK:
                reset_db()
            self._send_json({"ok": True})
            return

        self._send_json({"error": "ruta no encontrada"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        m = re.match(r"^/api/groups/([\w-]+)$", path)
        if m:
            uid = m.group(1)
            titulo = body.get("titulo")
            if titulo is None:
                self._send_json({"error": "titulo requerido"}, 400)
                return
            with DB_LOCK:
                conn = get_conn()
                try:
                    conn.execute("UPDATE grupos SET titulo=? WHERE uid=?", (titulo, uid))
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"ok": True})
            return

        m = re.match(r"^/api/tasks/([\w-]+)$", path)
        if m:
            uid = m.group(1)
            fields = ["id","corporativo","categoria","proceso","actividad","integraciones",
                      "microservicio","responsable","estado","estado_prueba","inicio","duracion","fin","avance",
                      "dependiente","owner_ku","grupo_uid"]
            col_map = {"id": "ident"}
            sets = []
            vals = []
            for f in fields:
                if f in body:
                    col = col_map.get(f, f)
                    sets.append(col + "=?")
                    vals.append(body[f])
            if not sets:
                self._send_json({"error": "nada para actualizar"}, 400)
                return
            vals.append(uid)
            with DB_LOCK:
                conn = get_conn()
                try:
                    conn.execute("UPDATE tareas SET " + ", ".join(sets) + " WHERE uid=?", vals)
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"ok": True})
            return

        self._send_json({"error": "ruta no encontrada"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        m = re.match(r"^/api/groups/([\w-]+)$", path)
        if m:
            uid = m.group(1)
            with DB_LOCK:
                conn = get_conn()
                try:
                    conn.execute("DELETE FROM tareas WHERE grupo_uid=?", (uid,))
                    conn.execute("DELETE FROM grupos WHERE uid=?", (uid,))
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"ok": True})
            return

        m = re.match(r"^/api/tasks/([\w-]+)$", path)
        if m:
            uid = m.group(1)
            with DB_LOCK:
                conn = get_conn()
                try:
                    conn.execute("DELETE FROM tareas WHERE uid=?", (uid,))
                    conn.commit()
                finally:
                    conn.close()
            self._send_json({"ok": True})
            return

        self._send_json({"error": "ruta no encontrada"}, 404)


def main():
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    init_db()

    httpd = None
    for candidate in range(port, port + 20):
        try:
            httpd = socketserver.ThreadingTCPServer(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError:
            continue
    if httpd is None:
        print("No se pudo encontrar un puerto libre. Cierra otros programas e intenta de nuevo.")
        sys.exit(1)

    url = "http://localhost:%d" % port
    print("=" * 60)
    print(" Cronograma Gantt TI - Farmacias Peruanas")
    print(" Base de datos SQLite: %s" % DB_PATH)
    print(" Servidor corriendo en: %s" % url)
    print(" Presiona Ctrl+C para detener el servidor.")
    print("=" * 60)
    try:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.shutdown()

if __name__ == "__main__":
    main()
