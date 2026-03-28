import customtkinter as ctk
import tkinter.ttk as ttk
from core.config import COLORS, fmt_moneda, CTkToolTip
from database import database as db
from database.exportador import exportar_liquidaciones
from CTkMessagebox import CTkMessagebox
from tkcalendar import DateEntry
import tkinter as tk
from tkinter import filedialog
from datetime import datetime


class TabFacturas(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)

        # Barra de filtros
        filtros_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        filtros_frame.pack(fill="x", padx=0, pady=(0, 10))

        ctk.CTkLabel(
            filtros_frame, text="🔍  Filtros Rápidos:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=15, pady=12)
        self.filtro_var = ctk.StringVar(value="todo")

        # Configuración de Radios (SIN TEXTO NI ICONOS, SOLO TOOLTIP)
        opciones = [
            ("", "hoy", "Hoy"),
            ("", "semana", "Esta Semana"),
            ("", "mes", "Este Mes"),
            ("", "todo", "Todo el historial")
        ]

        for icono, valor, desc in opciones:
            rb = ctk.CTkRadioButton(
                filtros_frame, text=icono, variable=self.filtro_var, value=valor,
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                border_color=COLORS["border"], text_color=COLORS["text"],
                font=ctk.CTkFont(size=14), width=28,
                command=self._on_filter_changed
            )
            rb.pack(side="left", padx=2, pady=12)
            CTkToolTip(rb, desc)

        # Filtro por calendario (Condicional)
        self.rb_fecha = ctk.CTkRadioButton(
            filtros_frame, text="📆", variable=self.filtro_var, value="fecha",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"], text_color=COLORS["text"],
            font=ctk.CTkFont(size=14, weight="bold"), width=40,
            command=self._on_filter_changed
        )
        self.rb_fecha.pack(side="left", padx=(10, 5), pady=12)
        CTkToolTip(self.rb_fecha, "Filtrar por Rango de Fechas")

        # Contenedor de calendarios (OCULTO POR DEFECTO)
        self.cal_container = ctk.CTkFrame(filtros_frame, fg_color="transparent")
        
        # --- Estilo para calendario "Desde" ---
        self.lbl_desde = ctk.CTkLabel(self.cal_container, text="Desde:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_muted"])
        self.lbl_desde.pack(side="left", padx=(5, 5))
        
        self.frame_desde = ctk.CTkFrame(self.cal_container, fg_color=COLORS["bg_input"], border_color=COLORS["border"], border_width=2, corner_radius=10, height=36)
        self.frame_desde.pack(side="left", padx=2)
        self.frame_desde.pack_propagate(False)

        self.cal_desde = DateEntry(
            self.frame_desde, width=12, background=COLORS["accent"],
            foreground=COLORS["text"], borderwidth=0, date_pattern='yyyy-mm-dd',
            locale='es_ES', font=("Segoe UI", 10),
            headersbackground=COLORS["accent"], headersforeground='white',
            selectbackground=COLORS["accent"], selectforeground='white',
            normalbackground=COLORS["bg_input"], normalforeground=COLORS["text"],
            weekendbackground=COLORS["bg_card"], weekendforeground=COLORS["text"],
            othermonthbackground=COLORS["table_row_2"], othermonthforeground=COLORS["text_muted"],
            relief="flat"
        )
        self.cal_desde.pack(padx=10, pady=0, fill="y", expand=True)
        
        # --- Estilo para calendario "Hasta" ---
        self.lbl_hasta = ctk.CTkLabel(self.cal_container, text="Hasta:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_muted"])
        self.lbl_hasta.pack(side="left", padx=(10, 5))
        
        self.frame_hasta = ctk.CTkFrame(self.cal_container, fg_color=COLORS["bg_input"], border_color=COLORS["border"], border_width=2, corner_radius=10, height=36)
        self.frame_hasta.pack(side="left", padx=2)
        self.frame_hasta.pack_propagate(False)

        self.cal_hasta = DateEntry(
            self.frame_hasta, width=12, background=COLORS["accent"],
            foreground=COLORS["text"], borderwidth=0, date_pattern='yyyy-mm-dd',
            locale='es_ES', font=("Segoe UI", 10),
            headersbackground=COLORS["accent"], headersforeground='white',
            selectbackground=COLORS["accent"], selectforeground='white',
            normalbackground=COLORS["bg_input"], normalforeground=COLORS["text"],
            weekendbackground=COLORS["bg_card"], weekendforeground=COLORS["text"],
            othermonthbackground=COLORS["table_row_2"], othermonthforeground=COLORS["text_muted"],
            relief="flat"
        )
        self.cal_hasta.pack(padx=10, pady=0, fill="both", expand=True)
        
        self.cal_desde.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())
        self.cal_hasta.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())

        ctk.CTkButton(
            filtros_frame, text="📥 Exportar a Excel", height=34, width=170,
            fg_color=COLORS["success"], hover_color="#27ae60",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._exportar_excel
        ).pack(side="right", padx=15, pady=12)

        # Tabla de liquidaciones
        tabla_liq_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        tabla_liq_frame.pack(fill="both", expand=True)

        self.tree_liquidaciones = ttk.Treeview(
            tabla_liq_frame,
            columns=("id", "mensajero", "fecha", "subtotal", "comision", "aseo", "base", "neto", "empresa", "num_servicios"),
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )
        for col, texto, ancho in [
            ("id", "ID", 40), ("mensajero", "Mensajero", 130),
            ("fecha", "Fecha", 150), ("subtotal", "Subtotal", 100),
            ("comision", "Comisión", 90), ("aseo", "Aseo", 60),
            ("base", "Base", 90), ("neto", "Neto Mens.", 110), 
            ("empresa", "Ganancia Emp.", 120), ("num_servicios", "N° Servicios", 120)
        ]:
            self.tree_liquidaciones.heading(col, text=texto)
            self.tree_liquidaciones.column(col, width=ancho, anchor="center")

        self.tree_liquidaciones.tag_configure("par", background=COLORS["table_row_2"])

        scrollbar_liq = ttk.Scrollbar(tabla_liq_frame, orient="vertical",
                                       command=self.tree_liquidaciones.yview)
        self.tree_liquidaciones.configure(yscrollcommand=scrollbar_liq.set)
        scrollbar_liq.pack(side="right", fill="y")
        self.tree_liquidaciones.pack(fill="both", expand=True, padx=5, pady=5)

        # Evento doble clic para mostrar tarjeta de liquidación
        self.tree_liquidaciones.bind("<Double-1>", self._abrir_tarjeta_liquidacion)

        # Resumen en la parte inferior
        self.resumen_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12, height=55)
        self.resumen_frame.pack(fill="x", pady=(10, 0))
        self.resumen_frame.pack_propagate(False)

        self.lbl_resumen = ctk.CTkLabel(
            self.resumen_frame,
            text="Sin datos para mostrar",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        self.lbl_resumen.pack(expand=True)

        # Cargar liquidaciones al iniciar
        self.reload_data()

    def _abrir_tarjeta_liquidacion(self, event):
        if not self.tree_liquidaciones.winfo_exists():
            return
        seleccion = self.tree_liquidaciones.selection()
        if not seleccion:
            return
        item = self.tree_liquidaciones.item(seleccion[0])
        valores = item["values"]
        # Mapear columnas
        datos = {
            "ID": valores[0],
            "Mensajero": valores[1],
            "Fecha": valores[2],
            "Subtotal": valores[3],
            "Comisión": valores[4],
            "Aseo": valores[5],
            "Base": valores[6],
            "Neto Mens.": valores[7],
            "Ganancia Emp.": valores[8]
        }
        # Obtener servicios asociados a la liquidación
        try:
            id_liq = int(valores[0])
        except Exception:
            id_liq = None
        # Buscar datos de la liquidación en la base para obtener mensajero_id y fecha exacta
        filtro = self.filtro_var.get()
        liquidaciones = db.obtener_liquidaciones(filtro)
        liq = next((l for l in liquidaciones if str(l["id"]) == str(id_liq)), None)
        servicios = []
        if liq:
            servicios = db.obtener_servicios_por_liquidacion(liq["id"])
        # Centrar desde el principio
        self._mostrar_tarjeta_liquidacion(datos, servicios, parent=self)

    def _mostrar_tarjeta_liquidacion(self, datos, servicios, parent=None):
        if parent is None:
            parent = self
        ancho = 420
        alto = 600
        ventana = ctk.CTkToplevel(parent)
        ventana.title(f"Liquidación #{datos['ID']}")
        ventana.configure(fg_color=COLORS["bg_card"])
        ventana.transient(parent)
        # Centrar usando la ventana raíz real
        ventana.update()
        root = parent.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() // 2) - (ancho // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana.lift()
        ventana.grab_set()

        # Header estilo premium con botón cerrar
        header = ctk.CTkFrame(ventana, fg_color=COLORS["accent"], height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text=f"Liquidación #{datos['ID']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=16, side="left", padx=(20,0))

        # Contenedor principal
        main_frame = ctk.CTkFrame(ventana, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        # Info Mensajero y Fecha
        ctk.CTkLabel(
            main_frame, text=f"👤 {datos['Mensajero']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            main_frame, text=f"📅 Fecha: {datos['Fecha']}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 10))

        # Desglose
        card = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_input"], corner_radius=12)
        card.pack(fill="x", pady=10)
        # Número de servicios
        ctk.CTkLabel(card, text="📦 N° Servicios liquidados:", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(card, text=f"{len(servicios)}", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"]).pack(side="right", padx=10, pady=8)

        # Totales
        totales_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        totales_frame.pack(fill="x", pady=(10, 0))
        # Subtotal
        ctk.CTkLabel(totales_frame, text="💰 Subtotal generado:", font=ctk.CTkFont(size=13)).pack(side="left")
        ctk.CTkLabel(totales_frame, text=datos['Subtotal'], font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"]).pack(side="right")
        # Ganancia Mensajero
        mensajero_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        mensajero_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(mensajero_frame, text="🏍️ Pago a Mensajero:", font=ctk.CTkFont(size=13)).pack(side="left")
        # Format Neto Mens directly with negative sign since the dictionary doesn't have it
        _neto_val = datos['Neto Mens.'].replace('$', '- $') if not datos['Neto Mens.'].startswith('-') else datos['Neto Mens.']
        ctk.CTkLabel(mensajero_frame, text=_neto_val, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["danger"]).pack(side="right")

        # Separador interno
        ctk.CTkFrame(main_frame, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # Ganancia Neta (empresa) Main Title
        neto_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        neto_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(neto_frame, text="🏢 GANANCIA EMPRESA:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(neto_frame, text=datos['Comisión'], font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")
        # Aseo
        aseo_g_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        aseo_g_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(aseo_g_frame, text="🧹 ASEO:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(aseo_g_frame, text=datos['Aseo'], font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")
        # Base
        base_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        base_frame.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(base_frame, text="🏦 BASE A DEVOLVER:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(base_frame, text=datos['Base'], font=ctk.CTkFont(size=18, weight="bold"), text_color="#e67e22").pack(side="right")

        # Separador
        ctk.CTkFrame(main_frame, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # Servicios incluidos
        ctk.CTkLabel(main_frame, text="Servicios incluidos:", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=8, pady=(10,2))
        if servicios:
            svc_frame = ctk.CTkScrollableFrame(main_frame, fg_color=COLORS["bg_input"], corner_radius=8, height=520)
            svc_frame.pack(fill="x", padx=8, pady=(5, 10))
            for s in servicios:
                desc = s.get("descripcion", "") or ""
                texto_principal = f"🚴 ID: {s['id']}  |  💰 {fmt_moneda(s['valor'])}  |  🕒 {s['fecha']}"
                fila = ctk.CTkFrame(svc_frame, fg_color="transparent")
                fila.pack(fill="x", padx=4, pady=(4, 0))
                ctk.CTkLabel(fila, text=texto_principal, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"], anchor="w").pack(anchor="w", padx=4)
                if desc:
                    ctk.CTkLabel(fila, text=f"   📝 {desc}", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w").pack(anchor="w", padx=4)
                ctk.CTkFrame(svc_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=4, pady=(4, 0))
        else:
            ctk.CTkLabel(main_frame, text="No se encontraron servicios asociados.", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", padx=8, pady=2)

    def _cargar_liquidaciones(self):
        """Recarga la tabla de liquidaciones según el filtro seleccionado."""
        for item in self.tree_liquidaciones.get_children():
            self.tree_liquidaciones.delete(item)

        filtro = self.filtro_var.get()
        if filtro == "fecha":
            f_inicio = self.cal_desde.get_date().strftime("%Y-%m-%d")
            f_fin = self.cal_hasta.get_date().strftime("%Y-%m-%d")
            filtro = f"{f_inicio}..{f_fin}"
            
        liquidaciones = db.obtener_liquidaciones(filtro)
        # ...

        total_neto = 0
        total_comision = 0

        for i, liq in enumerate(liquidaciones):
            tags = ("par",) if i % 2 == 1 else ()
            ganancia_empresa = liq["comision_empresa"] + liq["descuento_aseo"]
            num_servicios = liq.get("num_servicios", 0)
            self.tree_liquidaciones.insert("", "end", values=(
                liq["id"],
                liq.get("mensajero_nombre", ""),
                liq["fecha"],
                fmt_moneda(liq["subtotal_servicios"]),
                fmt_moneda(liq["comision_empresa"]),
                fmt_moneda(liq["descuento_aseo"]),
                fmt_moneda(liq.get("base_prestada", 0)),
                fmt_moneda(liq["neto_mensajero"]),
                fmt_moneda(ganancia_empresa),
                num_servicios
            ), tags=tags)
            total_neto += liq["neto_mensajero"]
            total_comision += liq["comision_empresa"]

        total_aseo = sum(l["descuento_aseo"] for l in liquidaciones)
        total_empresa = total_comision + total_aseo

        if liquidaciones:
            self.lbl_resumen.configure(
                text=f"📊  {len(liquidaciones)} liquidaciones  |  "
                     f"💰 Total Neto: {fmt_moneda(total_neto)}  |  "
                     f"🏢 Total Comisiones: {fmt_moneda(total_comision)}",
                text_color=COLORS["accent"]
            )
        else:
            self.lbl_resumen.configure(
                text="Sin liquidaciones para el filtro seleccionado.",
                text_color=COLORS["text_muted"]
            )
    def reload_data(self):
        self._cargar_liquidaciones()

    def _on_filter_changed(self):
        self._actualizar_estado_calendarios()
        self._cargar_liquidaciones()

    def _actualizar_estado_calendarios(self):
        es_fecha = self.filtro_var.get() == "fecha"
        if es_fecha:
            self.cal_container.pack(side="left", padx=5)
        else:
            self.cal_container.pack_forget()

    def _exportar_excel(self):
        """Exporta las liquidaciones visibles a un archivo Excel."""
        filtro = self.filtro_var.get()
        if filtro == "fecha":
            f_inicio = self.cal_desde.get_date().strftime("%Y-%m-%d")
            f_fin = self.cal_hasta.get_date().strftime("%Y-%m-%d")
            filtro = f"{f_inicio}..{f_fin}"
        datos = db.obtener_liquidaciones(filtro)

        if not datos:
            CTkMessagebox(title="ℹ️ Sin datos", message="No hay liquidaciones para exportar.",
                          icon="info", option_1="OK")
            return

        # Preguntar ubicación al usuario
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_sugerida = f"Liquidaciones_{timestamp}.xlsx"
        
        ruta_destino = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos de Excel", "*.xlsx")],
            initialfile=ruta_sugerida,
            title="Seleccionar dónde guardar el reporte"
        )
        
        if not ruta_destino:
            return

        try:
            ruta = exportar_liquidaciones(datos, ruta_destino=ruta_destino)
            # Preguntar si desea abrir la ubicación o ver el archivo
            msg = CTkMessagebox(
                title="✅ Exportación Exitosa",
                message=f"Archivo generado correctamente.",
                icon="check", option_1="Abrir archivo", option_2="OK"
            )
            
            if msg.get() == "Abrir archivo":
                try:
                    import subprocess, platform
                    if platform.system() == 'Darwin':       # macOS
                        subprocess.call(('open', ruta))
                    elif platform.system() == 'Windows':    # Windows
                        os.startfile(ruta)
                    else:                                   # linux
                        subprocess.call(('xdg-open', ruta))
                except Exception:
                    pass
        except Exception as e:
            CTkMessagebox(
                title="❌ Error",
                message=f"No se pudo exportar:\n{str(e)}",
                icon="cancel", option_1="OK"
            )
    
    def _on_date_changed(self):
        """Al cambiar fecha en el calendario, activa el radio de fecha y recarga."""
        self.filtro_var.set("fecha")
        self._on_filter_changed()


