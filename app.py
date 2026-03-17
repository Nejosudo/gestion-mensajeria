import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime
from database import database as db
from database.exportador import exportar_liquidaciones

# ── Configuración global ──
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colores
COLORS = {
    "bg_dark":      "#f4f7f6",
    "bg_card":      "#ffffff",
    "bg_input":     "#fdfdfd",
    "accent":       "#3a86ff",
    "accent_hover": "#2a6fdf",
    "success":      "#27ae60",
    "danger":       "#e74c3c",
    "warning":      "#f39c12",
    "text":         "#2d3436",
    "text_muted":   "#636e72",
    "border":       "#dfe6e9",
    "table_header": "#f1f2f6",
    "table_row_1":  "#ffffff",
    "table_row_2":  "#f9f9f9",
    "highlight":    "#eef2ff",
}

class VentanaResumen(ctk.CTkToplevel):
    """Ventana modal premium para el resumen de liquidación."""
    def __init__(self, parent, datos, on_confirm):
        super().__init__(parent)
        self.title("Confirmar Liquidación")
        self.geometry("400x580")
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        # Centrar
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 290
        self.geometry(f"+{x}+{y}")

        self.on_confirm = on_confirm

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=25, pady=20)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=42,
            fg_color="transparent", border_width=2, border_color=COLORS["border"],
            text_color=COLORS["text"], hover_color=COLORS["bg_input"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="Confirmar y Liquidar", height=42,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._confirmar
        ).pack(side="right", fill="x", expand=True)

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["accent"], height=70, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Resumen de Liquidación",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=20)

        # Contenedor principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        # ── Info Mensajero ──
        ctk.CTkLabel(
            main_frame, text=f"👤 {datos['nombre']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            main_frame, text=f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 10))

        # ── Desglose ──
        card = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_input"], corner_radius=12)
        card.pack(fill="x", pady=10)

        self._item_resumen(card, "📦 Servicios realizados", f"{datos['num_servicios']}", False)
        self._item_resumen(card, "💰 Subtotal", fmt_moneda(datos['subtotal']), False)
        self._item_resumen(card, "🏢 Comisión Empresa (20%)", f"- {fmt_moneda(datos['comision'])}", True)
        self._item_resumen(card, "🧹 Descuento Aseo", f"- {fmt_moneda(600)}", True)

        # Separador
        ctk.CTkFrame(main_frame, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # ── Totales Importantes ──
        # Ganancia Neta
        f_ganancia = ctk.CTkFrame(main_frame, fg_color="transparent")
        f_ganancia.pack(fill="x")
        ctk.CTkLabel(f_ganancia, text="💵 GANANCIA NETA:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(f_ganancia, text=fmt_moneda(datos['neto']), font=ctk.CTkFont(size=18, weight="bold"), text_color="#27ae60").pack(side="right")

        # Base
        f_base = ctk.CTkFrame(main_frame, fg_color="transparent")
        f_base.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(f_base, text="🏦 BASE A DEVOLVER:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(f_base, text=fmt_moneda(datos['base']), font=ctk.CTkFont(size=18, weight="bold"), text_color="#e67e22").pack(side="right")

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=25, pady=25)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=40,
            fg_color="transparent", border_width=2, border_color=COLORS["border"],
            text_color=COLORS["text"], hover_color=COLORS["bg_input"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="Confirmar y Liquidar", height=40,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._confirmar
        ).pack(side="right", fill="x", expand=True)

    def _item_resumen(self, parent, label, value, is_negative):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=8)
        
        color_val = COLORS["danger"] if is_negative else COLORS["text"]
        
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12, weight="bold"), text_color=color_val).pack(side="right")

    def _confirmar(self):
        self.on_confirm()
        self.destroy()


class FormularioMensajero(ctk.CTkToplevel):
    """Ventana modal para Crear y Editar mensajeros."""

    def __init__(self, parent, callback, mensajero=None):
        super().__init__(parent)
        self.callback = callback
        self.mensajero = mensajero

        self.title("👤 Datos del Mensajero")
        self.geometry("400x350")
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        # Centrar ventana
        self.after(10, self._centrar)

        # UI
        ctk.CTkLabel(
            self, text="GESTIÓN DE MENSAJERO",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=20)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=40)

        ctk.CTkLabel(form, text="Nombre:", text_color=COLORS["text_muted"]).pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(form, height=35, fg_color=COLORS["bg_input"])
        self.entry_nombre.pack(fill="x", pady=(2, 10))

        vcmd = (self.register(self._validar_telefono), '%P')
        self.entry_telefono = ctk.CTkEntry(
            form, height=35, fg_color=COLORS["bg_input"],
            validate="key", validatecommand=vcmd
        )
        self.entry_telefono.pack(fill="x", pady=(2, 20))

        if mensajero:
            self.entry_nombre.insert(0, mensajero["nombre"])
            self.entry_telefono.insert(0, mensajero["telefono"])

        self.btn_guardar = ctk.CTkButton(
            self, text="💾 Guardar Cambios" if mensajero else "➕ Registrar Mensajero",
            fg_color=COLORS["success"], hover_color="#219150", height=40,
            font=ctk.CTkFont(weight="bold"),
            command=self._guardar
        )
        self.btn_guardar.pack(fill="x", padx=40, pady=10)

    def _centrar(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (400 // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")

    def _validar_telefono(self, P):
        """Valida que el teléfono solo contenga números y máximo 11 dígitos."""
        if P == "": return True
        return P.isdigit() and len(P) <= 11

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        if not nombre or not telefono:
            CTkMessagebox(title="Error", message="Completa todos los campos.", icon="warning")
            return
        
        self.callback(nombre, telefono, self.mensajero["id"] if self.mensajero else None)
        self.destroy()


def fmt_moneda(valor: float) -> str:
    """Formatea un número a moneda COP: $5.000"""
    return f"${valor:,.0f}".replace(",", ".")


class App(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()

        # ── Ventana ──
        self.title("📦 Sistema de Mensajería — Gestión y Liquidación")
        self.geometry("1180x750")
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        # Inicializar base de datos
        db.init_db()

        self.mensajero_seleccionado: dict | None = None # Variable para el mensajero seleccionado
        self._edit_widget = None # Variable para edición inline

        self._build_ui()
        self._cargar_mensajeros()

    def _build_ui(self):
        """Crea el layout principal con CTkTabview."""

        # ── Header ──
        header = ctk.CTkFrame(self, height=60, fg_color=COLORS["bg_card"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="📦  SISTEMA DE MENSAJERÍA",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=20)

        self.lbl_fecha = ctk.CTkLabel(
            header,
            text=datetime.now().strftime("📅  %d / %B / %Y"),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        self.lbl_fecha.pack(side="right", padx=20)

        # ── Tabview ──
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["border"],
            corner_radius=12
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        tab1 = self.tabview.add("🏍️  Gestión de Mensajeros")
        tab2 = self.tabview.add("📊  Facturas e Informes")

        self._build_tab_gestion(tab1)
        self._build_tab_facturas(tab2)


    def _build_tab_gestion(self, parent):
        """Construye la pestaña de gestión de mensajeros."""

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_columnconfigure(0, weight=1, minsize=340)
        contenedor.grid_columnconfigure(1, weight=3)
        contenedor.grid_rowconfigure(0, weight=1)

        # ── Panel Izquierdo: CRUD Mensajeros ──
        panel_izq = ctk.CTkFrame(contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        # Header Mensajeros
        header_mz = ctk.CTkFrame(panel_izq, fg_color="transparent")
        header_mz.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header_mz, text="👤 Mensajeros",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkButton(
            header_mz, text="➕ Nuevo", width=80, height=28,
            fg_color=COLORS["success"], text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._abrir_form_nuevo
        ).pack(side="right")

        # Buscador
        search_frame = ctk.CTkFrame(panel_izq, fg_color=COLORS["bg_input"], corner_radius=8, height=35)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=8)
        
        self.entry_buscar = ctk.CTkEntry(
            search_frame, placeholder_text="Buscar por nombre o tel...",
            fg_color="transparent", border_width=0, text_color=COLORS["text"]
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._cargar_mensajeros())

        # Lista de mensajeros
        self.lista_mensajeros = ctk.CTkScrollableFrame(
            panel_izq, fg_color="transparent"
        )
        self.lista_mensajeros.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # Panel Derecho: Botones
        self.btn_edit_mz = ctk.CTkButton(
            panel_izq, text="✏️ Editar Seleccionado", height=32,
            fg_color=COLORS["warning"], text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._abrir_form_editar
        )
        self.btn_edit_mz.pack(fill="x", padx=15, pady=(0, 5))

        self.btn_del_mz = ctk.CTkButton(
            panel_izq, text="🗑️ Eliminar Seleccionado", height=32,
            fg_color=COLORS["danger"], text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._eliminar_mensajero
        )
        self.btn_del_mz.pack(fill="x", padx=15, pady=(0, 15))

        # ── Panel Derecho: Servicios y Liquidación ──
        panel_der = ctk.CTkFrame(contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        # Barra superior del panel derecho
        barra_sup = ctk.CTkFrame(panel_der, fg_color="transparent")
        barra_sup.pack(fill="x", padx=15, pady=(12, 5))

        self.lbl_mensajero_sel = ctk.CTkLabel(
            barra_sup, text="Selecciona un mensajero ←",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        )
        self.lbl_mensajero_sel.pack(side="left")

        # ── Barra de Acciones (Servicio + Base) ──
        barra_acciones = ctk.CTkFrame(panel_der, fg_color=COLORS["bg_input"], corner_radius=10, height=52)
        barra_acciones.pack(fill="x", padx=15, pady=(0, 8))
        barra_acciones.pack_propagate(False) 

        # Sección Servicio
        section_svc = ctk.CTkFrame(barra_acciones, fg_color="transparent")
        section_svc.pack(side="left", fill="y", padx=(10, 0))

        ctk.CTkLabel(
            section_svc, text="💰 Servicio:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=5)

        self.entry_valor = ctk.CTkEntry(
            section_svc, width=80, placeholder_text="5000",
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text"], corner_radius=6, height=28,
            justify="center"
        )
        self.entry_valor.pack(side="left", padx=2)
        self.entry_valor.insert(0, "5000")

        # Separador visual
        ctk.CTkFrame(barra_acciones, width=1, fg_color=COLORS["border"]).pack(side="left", fill="y", padx=15, pady=10)

        # Sección Base
        section_base = ctk.CTkFrame(barra_acciones, fg_color="transparent")
        section_base.pack(side="left", fill="y")

        ctk.CTkLabel(
            section_base, text="🏦 Base:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e67e22"
        ).pack(side="left", padx=5)

        self.entry_base = ctk.CTkEntry(
            section_base, width=80, placeholder_text="0",
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text"], corner_radius=6, height=28,
            justify="center"
        )
        self.entry_base.pack(side="left", padx=2)
        self.entry_base.insert(0, "0")

        ctk.CTkButton(
            barra_acciones, text="➕ Agregar servicio", width=32, height=28,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            command=self._asignar_servicio
        ).pack(side="right", padx=5)

        # Tabla de servicios del día
        tabla_header = ctk.CTkFrame(panel_der, fg_color="transparent")
        tabla_header.pack(fill="x", padx=15, pady=(5, 0))

        ctk.CTkLabel(
            tabla_header, text="📋  Servicios del Día",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left")

        ctk.CTkLabel(
            tabla_header, text="(Doble clic para editar valor)",
            font=ctk.CTkFont(size=10, slant="italic"),
            text_color=COLORS["text_muted"]
        ).pack(side="left", padx=10)

        # Barra inferior con botón de liquidación y eliminar servicio
        barra_inf = ctk.CTkFrame(panel_der, fg_color="transparent")
        barra_inf.pack(side="bottom", fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            barra_inf, text="🗑️ Eliminar Servicio", height=38,
            fg_color=COLORS["danger"], hover_color="#c0392b",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._eliminar_servicio
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            barra_inf, text="⚡ Ejecutar Liquidación", height=40, width=220,
            fg_color="#6c3ce0", hover_color="#7c4dff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._ejecutar_liquidacion
        ).pack(side="right")

        # Contenedor de la tabla con Treeview
        self.tabla_frame = ctk.CTkFrame(panel_der, fg_color=COLORS["bg_input"], corner_radius=10)
        self.tabla_frame.pack(fill="both", expand=True, padx=15, pady=(5, 8))

        import tkinter.ttk as ttk

        # Estilo para Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=COLORS["table_row_1"],
                         foreground=COLORS["text"],
                         fieldbackground=COLORS["table_row_1"],
                         borderwidth=0,
                         rowheight=32,
                         font=("Segoe UI", 11))
        style.configure("Dark.Treeview.Heading",
                         background=COLORS["table_header"],
                         foreground=COLORS["accent"],
                         borderwidth=0,
                         font=("Segoe UI", 11, "bold"),
                         relief="flat")
        style.map("Dark.Treeview",
                   background=[("selected", COLORS["highlight"])],
                   foreground=[("selected", COLORS["text"])])

        # Definición de la tabla
        self.tree_servicios = ttk.Treeview(
            self.tabla_frame,
            columns=("id", "valor", "fecha", "estado"),
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )
        self.tree_servicios.heading("id", text="ID")
        self.tree_servicios.heading("valor", text="Valor")
        self.tree_servicios.heading("fecha", text="Fecha / Hora")
        self.tree_servicios.heading("estado", text="Estado")

        self.tree_servicios.column("id", width=50, anchor="center")
        self.tree_servicios.column("valor", width=120, anchor="center")
        self.tree_servicios.column("fecha", width=180, anchor="center")
        self.tree_servicios.column("estado", width=100, anchor="center")

        # Color de las filas para Light Mode
        self.tree_servicios.tag_configure("par", background=COLORS["table_row_2"])
        self.tree_servicios.tag_configure("pendiente", foreground="#2980b9")
        self.tree_servicios.tag_configure("liquidado", foreground="#27ae60")

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree_servicios.pack(fill="both", expand=True, padx=2, pady=2)

        # Doble clic para edición inline
        self.tree_servicios.bind("<Double-1>", self._on_doble_clic_servicio)

    def _build_tab_facturas(self, parent):
        """Construye la pestaña de facturas."""

        # Barra de filtros
        filtros_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        filtros_frame.pack(fill="x", padx=0, pady=(0, 10))

        ctk.CTkLabel(
            filtros_frame, text="🔍  Filtros Rápidos:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=15, pady=12)

        self.filtro_var = ctk.StringVar(value="todo")

        for texto, valor in [("Hoy", "hoy"), ("Esta Semana", "semana"),
                             ("Este Mes", "mes"), ("Todo", "todo")]:
            ctk.CTkRadioButton(
                filtros_frame, text=texto, variable=self.filtro_var, value=valor,
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                border_color=COLORS["border"], text_color=COLORS["text"],
                font=ctk.CTkFont(size=12),
                command=self._cargar_liquidaciones
            ).pack(side="left", padx=10, pady=12)

        ctk.CTkButton(
            filtros_frame, text="📥 Exportar a Excel", height=34, width=170,
            fg_color=COLORS["success"], hover_color="#27ae60",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._exportar_excel
        ).pack(side="right", padx=15, pady=12)

        # Tabla de liquidaciones
        tabla_liq_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        tabla_liq_frame.pack(fill="both", expand=True)

        import tkinter.ttk as ttk

        self.tree_liquidaciones = ttk.Treeview(
            tabla_liq_frame,
            columns=("id", "mensajero", "fecha", "subtotal", "comision", "aseo", "base", "neto", "empresa"),
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )
        for col, texto, ancho in [
            ("id", "ID", 40), ("mensajero", "Mensajero", 130),
            ("fecha", "Fecha", 150), ("subtotal", "Subtotal", 100),
            ("comision", "Comisión", 90), ("aseo", "Aseo", 60),
            ("base", "Base", 90), ("neto", "Neto Mens.", 110), 
            ("empresa", "Ganancia Emp.", 120)
        ]:
            self.tree_liquidaciones.heading(col, text=texto)
            self.tree_liquidaciones.column(col, width=ancho, anchor="center")

        self.tree_liquidaciones.tag_configure("par", background=COLORS["table_row_2"])

        scrollbar_liq = ttk.Scrollbar(tabla_liq_frame, orient="vertical",
                                       command=self.tree_liquidaciones.yview)
        self.tree_liquidaciones.configure(yscrollcommand=scrollbar_liq.set)
        scrollbar_liq.pack(side="right", fill="y")
        self.tree_liquidaciones.pack(fill="both", expand=True, padx=5, pady=5)

        # Resumen en la parte inferior
        self.resumen_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12, height=55)
        self.resumen_frame.pack(fill="x", pady=(10, 0))
        self.resumen_frame.pack_propagate(False)

        self.lbl_resumen = ctk.CTkLabel(
            self.resumen_frame,
            text="Sin datos para mostrar",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        self.lbl_resumen.pack(expand=True)

        # Cargar datos iniciales
        self._cargar_liquidaciones()


    def _cargar_mensajeros(self):
        """Recarga la lista de mensajeros filtrando según el buscador."""
        for widget in self.lista_mensajeros.winfo_children():
            widget.destroy()

        busqueda = self.entry_buscar.get().strip()
        mensajeros = db.obtener_mensajeros(busqueda)

        if not mensajeros:
            ctk.CTkLabel(
                self.lista_mensajeros, text="No se encontraron coincidencias",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return

        for m in mensajeros:
            is_sel = self.mensajero_seleccionado and self.mensajero_seleccionado["id"] == m["id"]
            
            btn = ctk.CTkButton(
                self.lista_mensajeros,
                text=f"  👤  {m['nombre']}\n       📞 {m['telefono']}",
                anchor="w", height=50,
                fg_color=COLORS["highlight"] if is_sel else "transparent",
                hover_color=COLORS["highlight"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=12, weight="bold" if is_sel else "normal"),
                corner_radius=8,
                command=lambda mid=m["id"], mn=m["nombre"], mt=m["telefono"]: self._seleccionar_mensajero(mid, mn, mt)
            )
            btn.pack(fill="x", pady=1)

    def _seleccionar_mensajero(self, id_: int, nombre: str, telefono: str):
        """Selecciona un mensajero y carga sus servicios."""
        self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
        self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        self._cargar_mensajeros() # Recargar para resaltar selección
        self._cargar_servicios_dia()

    def _abrir_form_nuevo(self):
        FormularioMensajero(self, self._procesar_form_mensajero)

    def _abrir_form_editar(self):
        if not self.mensajero_seleccionado:
            CTkMessagebox(title="Aviso", message="Selecciona un mensajero de la lista.", icon="warning")
            return
        FormularioMensajero(self, self._procesar_form_mensajero, self.mensajero_seleccionado)

    def _procesar_form_mensajero(self, nombre, telefono, id_=None):
        if id_:
            db.actualizar_mensajero(id_, nombre, telefono)
            self.mensajero_seleccionado["nombre"] = nombre
            self.mensajero_seleccionado["telefono"] = telefono
            self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        else:
            db.crear_mensajero(nombre, telefono)
        
        self._cargar_mensajeros()

    def _eliminar_mensajero(self):
        if not self.mensajero_seleccionado:
            CTkMessagebox(title="⚠️ Sin selección", message="Selecciona un mensajero para eliminar.",
                          icon="warning", option_1="OK")
            return
        msg = CTkMessagebox(
            title="🗑️ Confirmar eliminación",
            message=f"¿Eliminar al mensajero '{self.mensajero_seleccionado['nombre']}'?\n"
                    f"Se borrarán también sus servicios y liquidaciones.",
            icon="question", option_1="Cancelar", option_2="Eliminar"
        )
        if msg.get() == "Eliminar":
            db.eliminar_mensajero(self.mensajero_seleccionado["id"])
            self.mensajero_seleccionado = None
            self.lbl_mensajero_sel.configure(text="Selecciona un mensajero ←")
            self._cargar_mensajeros()
            self._limpiar_tabla_servicios()

    def _asignar_servicio(self):
        if not self.mensajero_seleccionado:
            CTkMessagebox(title="⚠️ Sin mensajero", message="Selecciona un mensajero primero.",
                          icon="warning", option_1="OK")
            return
        try:
            valor = float(self.entry_valor.get().strip().replace(".", "").replace(",", ""))
        except ValueError:
            CTkMessagebox(title="⚠️ Valor inválido", message="Ingresa un valor numérico válido.",
                          icon="warning", option_1="OK")
            return
        if valor <= 0:
            CTkMessagebox(title="⚠️ Valor inválido", message="El valor debe ser mayor a 0.",
                          icon="warning", option_1="OK")
            return

        db.crear_servicio(self.mensajero_seleccionado["id"], valor)
        # Resetear el valor a 5000 por defecto después de agregar
        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, "5000")
        self._cargar_servicios_dia()

    def _cargar_servicios_dia(self):
        """Carga los servicios del día del mensajero seleccionado en la tabla."""
        self._limpiar_tabla_servicios()
        if not self.mensajero_seleccionado:
            return

        servicios = db.obtener_servicios_del_dia(self.mensajero_seleccionado["id"])
        for i, s in enumerate(servicios):
            tags = []
            if i % 2 == 1:
                tags.append("par")
            tags.append("pendiente" if s["estado"] == "Pendiente" else "liquidado")

            self.tree_servicios.insert("", "end", iid=str(s["id"]), values=(
                s["id"],
                fmt_moneda(s["valor"]),
                s["fecha"],
                s["estado"]
            ), tags=tags)

    def _limpiar_tabla_servicios(self):
        for item in self.tree_servicios.get_children():
            self.tree_servicios.delete(item)

    def _eliminar_servicio(self):
        """Elimina el servicio seleccionado de la tabla."""
        seleccion = self.tree_servicios.selection()
        if not seleccion:
            CTkMessagebox(title="⚠️ Sin selección", message="Selecciona un servicio de la tabla.",
                          icon="warning", option_1="OK")
            return
        id_servicio = int(seleccion[0])
        valores = self.tree_servicios.item(seleccion[0], "values")
        estado = valores[3]
        if estado == "Liquidado":
            CTkMessagebox(title="⚠️ No permitido",
                          message="No se puede eliminar un servicio ya liquidado.",
                          icon="warning", option_1="OK")
            return
        msg = CTkMessagebox(
            title="🗑️ Eliminar servicio",
            message=f"¿Eliminar el servicio #{id_servicio} con valor {valores[1]}?",
            icon="question", option_1="Cancelar", option_2="Eliminar"
        )
        if msg.get() == "Eliminar":
            db.eliminar_servicio(id_servicio)
            self._cargar_servicios_dia()

    # ── Edición Inline ──

    def _on_doble_clic_servicio(self, event):
        """Permite editar el valor de un servicio mediante doble clic."""
        self._cerrar_edicion_inline()

        region = self.tree_servicios.identify("region", event.x, event.y)
        if region != "cell":
            return

        columna = self.tree_servicios.identify_column(event.x)
        item = self.tree_servicios.identify_row(event.y)
        if not item:
            return

        # Solo permitir edición en la columna "valor" (#2)
        if columna != "#2":
            return

        # No editar servicios liquidados
        valores = self.tree_servicios.item(item, "values")
        if valores[3] == "Liquidado":
            CTkMessagebox(title="⚠️ No editable",
                          message="No se puede editar un servicio ya liquidado.",
                          icon="warning", option_1="OK")
            return

        # Obtener posición de la celda
        bbox = self.tree_servicios.bbox(item, columna)
        if not bbox:
            return

        # Crear Entry sobre la celda
        valor_actual = valores[1].replace("$", "").replace(".", "")
        entry = ctk.CTkEntry(
            self.tabla_frame,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text"],
            border_color=COLORS["accent"],
            corner_radius=4,
            justify="center",
            width=bbox[2] - 4,
            height=bbox[3] - 4
        )
        entry.place(x=bbox[0] + 2, y=bbox[1] + 2)
        entry.insert(0, valor_actual)
        entry.select_range(0, "end")
        entry.focus()

        self._edit_widget = entry
        self._edit_item = item
        self._edit_id = int(valores[0])

        entry.bind("<Return>", self._confirmar_edicion_inline)
        entry.bind("<Escape>", lambda e: self._cerrar_edicion_inline())
        entry.bind("<FocusOut>", lambda e: self._cerrar_edicion_inline())

    def _confirmar_edicion_inline(self, event=None):
        """Guarda el nuevo valor editado inline."""
        if not self._edit_widget:
            return

        try:
            nuevo_valor = float(self._edit_widget.get().strip().replace(".", "").replace(",", ""))
        except ValueError:
            CTkMessagebox(title="⚠️ Error", message="Valor numérico inválido.",
                          icon="warning", option_1="OK")
            self._cerrar_edicion_inline()
            return

        if nuevo_valor <= 0:
            CTkMessagebox(title="⚠️ Error", message="El valor debe ser mayor a 0.",
                          icon="warning", option_1="OK")
            self._cerrar_edicion_inline()
            return

        db.actualizar_valor_servicio(self._edit_id, nuevo_valor)
        self._cerrar_edicion_inline()
        self._cargar_servicios_dia()

    def _cerrar_edicion_inline(self):
        """Destruye el widget de edición inline si existe."""
        if self._edit_widget:
            self._edit_widget.destroy()
            self._edit_widget = None

    def _ejecutar_liquidacion(self):
        """Ejecuta la liquidación del mensajero seleccionado."""
        if not self.mensajero_seleccionado:
            CTkMessagebox(title="⚠️ Sin mensajero", message="Selecciona un mensajero primero.",
                          icon="warning", option_1="OK")
            return

        pendientes = db.obtener_servicios_pendientes(self.mensajero_seleccionado["id"])
        if not pendientes:
            CTkMessagebox(
                title="ℹ️ Sin servicios pendientes",
                message=f"El mensajero '{self.mensajero_seleccionado['nombre']}'\n"
                        f"no tiene servicios pendientes para liquidar.",
                icon="info", option_1="Entendido"
            )
            return

        # Calcular resumen previo
        try:
            val_base = float(self.entry_base.get().strip().replace(".", "").replace(",", "")) if self.entry_base.get() else 0
        except ValueError:
            val_base = 0 # Default to 0 if input is invalid

        subtotal = sum(s["valor"] for s in pendientes)
        comision = subtotal * 0.20
        # Ganancia real del trabajo
        ganancia_neta = (subtotal * 0.80) - 600

        datos_liquidacion = {
            "nombre": self.mensajero_seleccionado['nombre'],
            "num_servicios": len(pendientes),
            "subtotal": subtotal,
            "comision": comision,
            "neto": ganancia_neta,
            "base": val_base
        }

        def confirmar_final():
            # Ejecutar en DB
            db.ejecutar_liquidacion(self.mensajero_seleccionado["id"], val_base, pendientes)
            
            # Limpiar UI
            self.entry_base.delete(0, "end")
            self.entry_base.insert(0, "0")
            self._cargar_servicios_dia()
            self._cargar_liquidaciones()
            
            CTkMessagebox(
                title="✅ Éxito",
                message="La liquidación se ha procesado correctamente.",
                icon="check", option_1="Excelente"
            )

        # Mostrar ventana premium
        VentanaResumen(self, datos_liquidacion, confirmar_final)

    def _cargar_liquidaciones(self):
        """Recarga la tabla de liquidaciones según el filtro seleccionado."""
        for item in self.tree_liquidaciones.get_children():
            self.tree_liquidaciones.delete(item)

        filtro = self.filtro_var.get()
        liquidaciones = db.obtener_liquidaciones(filtro)

        total_neto = 0
        total_comision = 0

        for i, liq in enumerate(liquidaciones):
            tags = ("par",) if i % 2 == 1 else ()
            ganancia_empresa = liq["comision_empresa"] + liq["descuento_aseo"]
            
            self.tree_liquidaciones.insert("", "end", values=(
                liq["id"],
                liq.get("mensajero_nombre", ""),
                liq["fecha"],
                fmt_moneda(liq["subtotal_servicios"]),
                fmt_moneda(liq["comision_empresa"]),
                fmt_moneda(liq["descuento_aseo"]),
                fmt_moneda(liq.get("base_prestada", 0)),
                fmt_moneda(liq["neto_mensajero"]),
                fmt_moneda(ganancia_empresa)
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

    def _exportar_excel(self):
        """Exporta las liquidaciones visibles a un archivo Excel."""
        filtro = self.filtro_var.get()
        datos = db.obtener_liquidaciones(filtro)

        if not datos:
            CTkMessagebox(title="ℹ️ Sin datos", message="No hay liquidaciones para exportar.",
                          icon="info", option_1="OK")
            return

        try:
            ruta = exportar_liquidaciones(datos)
            CTkMessagebox(
                title="✅ Exportación Exitosa",
                message=f"Archivo generado en:\n{ruta}",
                icon="check", option_1="Abrir carpeta", option_2="OK"
            )
        except Exception as e:
            CTkMessagebox(
                title="❌ Error",
                message=f"No se pudo exportar:\n{str(e)}",
                icon="cancel", option_1="OK"
            )

if __name__ == "__main__":
    app = App()
    app.mainloop()
