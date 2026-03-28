import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime
from core.config import COLORS, fmt_moneda, CTkToolTip
from database import database as db
from CTkMessagebox import CTkMessagebox
from tkcalendar import DateEntry
import tkinter as tk


class TabFinanzas(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()
        self.reload_data()

    def _build_ui(self):
        # --- Filtros ---
        filtros_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        filtros_frame.pack(fill="x", padx=0, pady=(0, 15))

        ctk.CTkLabel(
            filtros_frame, text="🕒 Período:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=15, pady=12)

        self.filtro_var = ctk.StringVar(value="todo")

        # Configuración de Radios (SIN TEXTO NI ICONOS, SOLO TOOLTIP)
        opciones = [
            ("Hoy", "hoy", "Hoy"),
            ("Semana", "semana", "Esta Semana"),
            ("Mes", "mes", "Este Mes"),
            ("Todo", "todo", "Todo el historial")
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
        # No se empaqueta inicialmente

        self.lbl_desde = ctk.CTkLabel(self.cal_container, text="Desde:", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
        self.lbl_desde.pack(side="left", padx=2)
        self.cal_desde = DateEntry(self.cal_container, width=10, background=COLORS["accent"],
                                     foreground='white', borderwidth=1, date_pattern='yyyy-mm-dd',
                                     locale='es_ES')
        self.cal_desde.pack(side="left", padx=2)
        
        self.lbl_hasta = ctk.CTkLabel(self.cal_container, text="Hasta:", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
        self.lbl_hasta.pack(side="left", padx=2)
        self.cal_hasta = DateEntry(self.cal_container, width=10, background=COLORS["accent"],
                                     foreground='white', borderwidth=1, date_pattern='yyyy-mm-dd',
                                     locale='es_ES')
        self.cal_hasta.pack(side="left", padx=2)
        
        self.cal_desde.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())
        self.cal_hasta.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())

        # Inicializar estado de calendarios
        self._actualizar_estado_calendarios()

        # --- Dashboard ---
        dash_frame = ctk.CTkFrame(self, fg_color="transparent")
        dash_frame.pack(fill="x", pady=(0, 15))
        
        self.card_ingresos = self._crear_card(dash_frame, "Total Ingresos", "$0", COLORS["success"])
        self.card_ingresos.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.card_gastos = self._crear_card(dash_frame, "Total Gastos", "$0", COLORS["danger"])
        self.card_gastos.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_balance = self._crear_card(dash_frame, "Balance Neto", "$0", COLORS["accent"])
        self.card_balance.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # --- Tablas ---
        tablas_contenedor = ctk.CTkFrame(self, fg_color="transparent")
        tablas_contenedor.pack(fill="both", expand=True)
        tablas_contenedor.grid_columnconfigure(0, weight=1)
        tablas_contenedor.grid_columnconfigure(1, weight=1)
        tablas_contenedor.grid_rowconfigure(0, weight=1)

        # Columna Ingresos (Liquidaciones)
        f_ingresos = ctk.CTkFrame(tablas_contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        f_ingresos.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Configurar grid para f_ingresos
        f_ingresos.grid_rowconfigure(1, weight=1)
        f_ingresos.grid_columnconfigure(0, weight=1)
        
        # Header Ingresos
        header_ingresos = ctk.CTkFrame(f_ingresos, fg_color="transparent", height=40)
        header_ingresos.grid(row=0, column=0, sticky="ew", padx=15, pady=5)
        header_ingresos.pack_propagate(False)

        ctk.CTkLabel(header_ingresos, text="📈 Detalle de Ingresos (Comisiones + Aseo)", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent"]).pack(side="left", pady=5)
        
        # Rediseño de la lógica de tablas para usar grid
        self.tree_ingresos_frame = ctk.CTkFrame(f_ingresos, fg_color="transparent")
        self.tree_ingresos_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tree_ingresos = self._setup_treeview(self.tree_ingresos_frame, ("id", "fecha", "comision", "aseo", "total"))
        
        self.tree_ingresos.heading("id", text="ID")
        self.tree_ingresos.heading("fecha", text="Fecha")
        self.tree_ingresos.heading("comision", text="Comisión")
        self.tree_ingresos.heading("aseo", text="Aseo")
        self.tree_ingresos.heading("total", text="Total")
        
        for col, width in zip(("id", "fecha", "comision", "aseo", "total"), (40, 140, 90, 80, 100)):
            self.tree_ingresos.column(col, width=width, anchor="center")

        # Footer Ingresos
        self.f_footer_ing = ctk.CTkFrame(f_ingresos, fg_color=COLORS["bg_input"], height=40, corner_radius=8)
        self.f_footer_ing.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.lbl_total_ing_footer = ctk.CTkLabel(self.f_footer_ing, text="Total: $0", 
                                                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["success"])
        self.lbl_total_ing_footer.pack(side="right", padx=20, pady=5)

        # Columna Gastos
        f_gastos = ctk.CTkFrame(tablas_contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        f_gastos.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Configurar grid para f_gastos
        f_gastos.grid_rowconfigure(2, weight=1)
        f_gastos.grid_columnconfigure(0, weight=1)

        header_gastos = ctk.CTkFrame(f_gastos, fg_color="transparent", height=40)
        header_gastos.grid(row=0, column=0, sticky="ew", padx=15, pady=5)
        header_gastos.pack_propagate(False)
        
        ctk.CTkLabel(header_gastos, text="📉 Detalle de Gastos", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["danger"]).pack(side="left", pady=5)
        
        # Invertir orden: Agregar Gasto a la derecha
        ctk.CTkButton(header_gastos, text="➕ Agregar Gasto", width=120, height=28,
                     fg_color=COLORS["danger"], hover_color="#c0392b",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     command=self._abrir_modal_gasto).pack(side="right", padx=(5, 0))

        ctk.CTkButton(header_gastos, text="🗑️ Eliminar", width=80, height=28,
                     fg_color="transparent", border_width=1, border_color=COLORS["danger"],
                     text_color=COLORS["danger"], font=ctk.CTkFont(size=11, weight="bold"),
                     command=self._confirmar_eliminar_gasto).pack(side="right")

        self.tree_gastos_frame = ctk.CTkFrame(f_gastos, fg_color="transparent")
        self.tree_gastos_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.tree_gastos = self._setup_treeview(self.tree_gastos_frame, ("id", "fecha", "descripcion", "monto"))

        self.tree_gastos.heading("id", text="ID")
        self.tree_gastos.heading("fecha", text="Fecha")
        self.tree_gastos.heading("descripcion", text="Descripción")
        self.tree_gastos.heading("monto", text="Monto")
        
        for col, width in zip(("id", "fecha", "descripcion", "monto"), (40, 140, 180, 100)):
            self.tree_gastos.column(col, width=width, anchor="center")
            
        # Footer Gastos
        self.f_footer_gst = ctk.CTkFrame(f_gastos, fg_color=COLORS["bg_input"], height=40, corner_radius=8)
        self.f_footer_gst.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.lbl_total_gst_footer = ctk.CTkLabel(self.f_footer_gst, text="Total: $0", 
                                                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["danger"])
        self.lbl_total_gst_footer.pack(side="right", padx=20, pady=5)

    def _crear_card(self, parent, titulo, valor, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12, height=100)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(pady=(15, 0))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
        lbl_valor.pack(pady=(5, 15))
        card.lbl_valor = lbl_valor
        return card

    def _setup_treeview(self, parent_frame, columnas):
        """Configura un Treeview con scrollbar dentro de un frame."""
        tree = ttk.Treeview(parent_frame, columns=columnas, show="headings", style="Dark.Treeview")
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("par", background=COLORS["table_row_2"])
        return tree

    def _crear_tabla(self, parent, columnas):
        """Deprecated: Use _setup_treeview instead."""
        tabla_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tabla_frame.pack(fill="both", expand=True, padx=10, pady=5)
        return self._setup_treeview(tabla_frame, columnas)

    def reload_data(self):
        filtro = self.filtro_var.get()
        if filtro == "fecha":
            f_inicio = self.cal_desde.get_date().strftime("%Y-%m-%d")
            f_fin = self.cal_hasta.get_date().strftime("%Y-%m-%d")
            filtro = f"{f_inicio}..{f_fin}"
            
        # Cargar Ingresos (Liquidaciones)
        for item in self.tree_ingresos.get_children():
            self.tree_ingresos.delete(item)
        
        liquidaciones = db.obtener_liquidaciones(filtro)
        total_ingresos = 0
        for i, liq in enumerate(liquidaciones):
            comision = liq["comision_empresa"]
            aseo = liq["descuento_aseo"]
            total_fila = comision + aseo
            total_ingresos += total_fila
            tags = ("par",) if i % 2 == 1 else ()
            self.tree_ingresos.insert("", "end", values=(
                liq["id"], liq["fecha"], fmt_moneda(comision), fmt_moneda(aseo), fmt_moneda(total_fila)
            ), tags=tags)
        
        # Cargar Gastos
        for item in self.tree_gastos.get_children():
            self.tree_gastos.delete(item)
            
        gastos = db.obtener_gastos(filtro)
        total_gastos = 0
        for i, g in enumerate(gastos):
            total_gastos += g["monto"]
            tags = ("par",) if i % 2 == 1 else ()
            self.tree_gastos.insert("", "end", values=(
                g["id"], g["fecha"], g["descripcion"], fmt_moneda(g["monto"])
            ), tags=tags)
            
        # Actualizar Dashboard y Footers
        self.card_ingresos.lbl_valor.configure(text=fmt_moneda(total_ingresos))
        self.card_gastos.lbl_valor.configure(text=fmt_moneda(total_gastos))
        self.card_balance.lbl_valor.configure(text=fmt_moneda(total_ingresos - total_gastos))

        self.lbl_total_ing_footer.configure(text=f"Total: {fmt_moneda(total_ingresos)}")
        self.lbl_total_gst_footer.configure(text=f"Total: {fmt_moneda(total_gastos)}")

    def _on_filter_changed(self):
        self._actualizar_estado_calendarios()
        self.reload_data()

    def _actualizar_estado_calendarios(self):
        es_fecha = self.filtro_var.get() == "fecha"
        if es_fecha:
            self.cal_container.pack(side="left", padx=5)
        else:
            self.cal_container.pack_forget()

    def _on_date_changed(self):
        """Al cambiar fecha en el calendario, activa el radio de fecha y recarga."""
        self.filtro_var.set("fecha")
        self.reload_data()

    def _abrir_modal_gasto(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Registrar Nuevo Gasto")
        modal.geometry("350x250")
        modal.configure(fg_color=COLORS["bg_card"])
        modal.transient(self.winfo_toplevel())

        # Centrar y mostrar
        modal.update()
        root = self.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() // 2) - (350 // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (250 // 2)
        modal.geometry(f"+{x}+{y}")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Descripción del Gasto:", font=ctk.CTkFont(size=13)).pack(pady=(20, 5))
        entry_desc = ctk.CTkEntry(modal, width=250, placeholder_text="Ej: Combustible, Papelería...")
        entry_desc.pack(pady=5)
        
        ctk.CTkLabel(modal, text="Monto ($):", font=ctk.CTkFont(size=13)).pack(pady=(10, 5))
        entry_monto = ctk.CTkEntry(modal, width=250, placeholder_text="0")
        entry_monto.pack(pady=5)

        def guardar():
            desc = entry_desc.get().strip()
            try:
                monto_str = entry_monto.get().replace(".", "").replace(",", "").strip()
                if not monto_str or not desc:
                    raise ValueError("Campos vacíos")
                monto = float(monto_str)
            except ValueError:
                CTkMessagebox(title="Error", message="Ingresa una descripción y un monto válido.", icon="cancel")
                return
            
            db.crear_gasto(desc, monto)
            modal.destroy()
            self.reload_data()

        ctk.CTkButton(modal, text="💾 Guardar Gasto", fg_color=COLORS["success"], command=guardar).pack(pady=20)

    def _confirmar_eliminar_gasto(self):
        seleccion = self.tree_gastos.selection()
        if not seleccion:
            CTkMessagebox(title="Aviso", message="Selecciona un gasto de la lista.", icon="warning")
            return
        
        item = self.tree_gastos.item(seleccion[0])
        id_gasto = item["values"][0]

        # Solicitar contraseña antes de proceder
        self._solicitar_password(
            titulo="Seguridad",
            mensaje=f"Ingresa la contraseña para eliminar el gasto #{id_gasto}:",
            callback=lambda: self._eliminar_gasto_confirmado(id_gasto)
        )

    def _solicitar_password(self, titulo, mensaje, callback):
        modal = ctk.CTkToplevel(self)
        modal.title(titulo)
        modal.geometry("320x180")
        modal.configure(fg_color=COLORS["bg_card"])
        modal.transient(self.winfo_toplevel())

        # Centrar
        modal.update()
        root = self.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() // 2) - (320 // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (180 // 2)
        modal.geometry(f"+{x}+{y}")
        modal.grab_set()

        ctk.CTkLabel(modal, text=mensaje, font=ctk.CTkFont(size=12)).pack(pady=(20, 10), padx=20)
        entry_pass = ctk.CTkEntry(modal, width=200, show="*")
        entry_pass.pack(pady=5)
        entry_pass.focus_set()

        def verificar(event=None):
            if entry_pass.get() == "ya le llego":
                modal.destroy()
                callback()
            else:
                CTkMessagebox(title="Error", message="Contraseña incorrecta", icon="cancel")
                entry_pass.delete(0, 'end')

        entry_pass.bind("<Return>", verificar)
        ctk.CTkButton(modal, text="Verificar", fg_color=COLORS["accent"], command=verificar).pack(pady=15)

    def _eliminar_gasto_confirmado(self, id_gasto):
        db.eliminar_gasto(id_gasto)
        self.reload_data()
        CTkMessagebox(title="Éxito", message="Gasto eliminado correctamente.", icon="check")
