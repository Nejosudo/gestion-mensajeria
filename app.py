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
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)

        # Centrar desde el principio
        ancho = 400
        alto = 580
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (ancho // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (alto // 2)
        if self.winfo_exists():
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
            
        self.wait_visibility()
        self.grab_set()

        self.on_confirm = on_confirm

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
        self._item_resumen(card, "💰 Subtotal generado", fmt_moneda(datos['subtotal']), False)
        self._item_resumen(card, "🏍️ Pago a Mensajero", f"- {fmt_moneda(datos['neto'])}", True)

        # Separador
        ctk.CTkFrame(main_frame, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # ── Totales Importantes (Empresa) ──
        # Ganancia Empresa
        f_empresa = ctk.CTkFrame(main_frame, fg_color="transparent")
        f_empresa.pack(fill="x")
        ctk.CTkLabel(f_empresa, text="🏢 GANANCIA EMPRESA:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(f_empresa, text=fmt_moneda(datos['comision']), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")

        # Aseo
        f_aseo = ctk.CTkFrame(main_frame, fg_color="transparent")
        f_aseo.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(f_aseo, text="🧹 ASEO:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(f_aseo, text=fmt_moneda(1000), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")

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
        if self.winfo_exists():
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
        
        # Centrar ventana
        self.update_idletasks()
        if self.master and self.master.winfo_exists():
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (400 // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (350 // 2)
            self.geometry(f"+{x}+{y}")
            
        self.wait_visibility()
        self.grab_set()

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

    def _validar_telefono(self, P):
        """Valida que el teléfono solo contenga números y máximo 11 dígitos."""
        if P == "": return True
        return P.isdigit() and len(P) <= 11

    def _guardar(self):
        if not self.winfo_exists():
            return
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
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        # Mostrar ventana de contraseña antes de continuar
        self.withdraw()  # Oculta la ventana principal
        self._ventana_login()

    # Eliminado: método de login por contraseña
    def _ventana_login(self):
        login = ctk.CTkToplevel(self)
        login.title("Acceso restringido")
        login.geometry("340x180")
        login.resizable(False, False)
        login.transient(self)
        # Centrar en el centro de la pantalla SIEMPRE
        self.update_idletasks()
        screen_w = login.winfo_screenwidth()
        screen_h = login.winfo_screenheight()
        x = (screen_w // 2) - (340 // 2)
        y = (screen_h // 2) - (180 // 2)
        login.geometry(f"340x180+{x}+{y}")
        login.wait_visibility()
        login.grab_set()

        ctk.CTkLabel(login, text="Ingrese la contraseña", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(20, 10))
        entry_pass = ctk.CTkEntry(login, show="*", width=200)
        entry_pass.pack(pady=5)

        def check_pass():
            if entry_pass.get() == "ya le llego":
                login.destroy()
                self._iniciar_app()
            else:
                CTkMessagebox(title="Error", message="Contraseña incorrecta", icon="cancel")
                entry_pass.delete(0, "end")
                entry_pass.focus()

        ctk.CTkButton(login, text="Entrar", command=check_pass).pack(pady=15)
        entry_pass.bind("<Return>", lambda e: check_pass())
        entry_pass.focus()

    def _iniciar_app(self):
        # Centrar y maximizar ANTES de mostrar la ventana principal
        ancho = 1180
        alto = 750
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.state("zoomed")
        self.deiconify()  # Muestra la ventana principal
        # Inicializar base de datos
        db.init_db()
        self.mensajero_seleccionado: dict | None = None # Variable para el mensajero seleccionado
        self.bases_mensajeros: dict = {} # Guarda la base individual para cada mensajero
        for m in db.obtener_mensajeros():
            base_bd = m.get("base_actual", 0)
            if base_bd is None: base_bd = 0
            self.bases_mensajeros[m["id"]] = str(int(base_bd) if base_bd == int(base_bd) else base_bd) if base_bd else "0"
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

        # Forzar color negro en el texto de las pestañas
        try:
            for btn in self.tabview._segmented_button._buttons_dict.values():
                btn.configure(text_color=("#000000", "#000000"))
        except Exception:
            pass


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
        # --- Protección por contraseña para Editar y Eliminar ---
        def pedir_contrasena(callback):
            dialog = ctk.CTkToplevel(self)
            dialog.title("Contraseña requerida")
            dialog.geometry("320x150")
            dialog.resizable(False, False)
            dialog.transient(self)
            # Centrar
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - (320 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (150 // 2)
            dialog.geometry(f"320x150+{x}+{y}")
            dialog.wait_visibility()
            dialog.grab_set()

            ctk.CTkLabel(dialog, text="Ingrese la contraseña", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(18, 8))
            entry = ctk.CTkEntry(dialog, show="*", width=180)
            entry.pack(pady=5)

            def check():
                if entry.get() == "ya le llego":
                    dialog.destroy()
                    callback()
                else:
                    CTkMessagebox(title="Error", message="Contraseña incorrecta", icon="cancel")
                    entry.delete(0, "end")
                    entry.focus()

            ctk.CTkButton(dialog, text="Aceptar", command=check).pack(pady=12)
            entry.bind("<Return>", lambda e: check())
            entry.focus()

        self.btn_edit_mz = ctk.CTkButton(
            panel_izq, text="✏️ Editar Seleccionado", height=32,
            fg_color=COLORS["warning"], text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: pedir_contrasena(self._abrir_form_editar)
        )
        self.btn_edit_mz.pack(fill="x", padx=15, pady=(0, 5))

        self.btn_del_mz = ctk.CTkButton(
            panel_izq, text="🗑️ Eliminar Seleccionado", height=32,
            fg_color=COLORS["danger"], text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: pedir_contrasena(self._eliminar_mensajero)
        )
        self.btn_del_mz.pack(fill="x", padx=15, pady=(0, 15))

    # Eliminado: protección de botones por contraseña

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
        self.entry_base.insert(0, "$0")
        self.entry_base.bind("<KeyRelease>", self._on_base_key_release)
        self.entry_base.bind("<Return>", self._guardar_base_actual)
        self.entry_base.bind("<FocusIn>", self._on_base_focus_in)
        self.entry_base.bind("<FocusOut>", self._on_base_focus_out)

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
            command=lambda: pedir_contrasena(self._eliminar_servicio)
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
            columns=("id", "valor", "descripcion", "fecha"),
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )
        self.tree_servicios.heading("id", text="ID")
        self.tree_servicios.heading("valor", text="Valor")
        self.tree_servicios.heading("descripcion", text="Descripción domicilio")
        self.tree_servicios.heading("fecha", text="Fecha / Hora")

        self.tree_servicios.column("id", width=50, anchor="center")
        self.tree_servicios.column("valor", width=120, anchor="center")
        self.tree_servicios.column("descripcion", width=220, anchor="w")
        self.tree_servicios.column("fecha", width=180, anchor="center")

        # Color de las filas para Light Mode
        self.tree_servicios.tag_configure("par", background=COLORS["table_row_2"])

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree_servicios.pack(fill="both", expand=True, padx=2, pady=2)

        # Doble clic para edición inline (valor o descripción)
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

        # Cargar liquidaciones al iniciar
        self._cargar_liquidaciones()

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
            servicios = db.obtener_servicios_por_liquidacion(liq["mensajero_id"], liq["id"])
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
        # Centrar desde el principio
        ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (ancho // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana.wait_visibility()
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
                ctk.CTkLabel(svc_frame, text=f"ID: {s['id']} | Valor: {fmt_moneda(s['valor'])} | Fecha: {s['fecha']}", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=8, pady=4)
        else:
            ctk.CTkLabel(main_frame, text="No se encontraron servicios asociados.", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", padx=8, pady=2)


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
        # Almacenar la base del anterior mensajero seleccionado
        if self.mensajero_seleccionado and hasattr(self, 'entry_base'):
            base_cruda = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            val_to_save = base_cruda if base_cruda else "0"
            self.bases_mensajeros[self.mensajero_seleccionado["id"]] = val_to_save
            try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], float(val_to_save))
            except Exception: pass

        self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
        self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        self._cargar_mensajeros() # Recargar para resaltar selección
        self._cargar_servicios_dia()

        # Restaurar la base del mensajero recién seleccionado
        if hasattr(self, 'entry_base'):
            self.entry_base.delete(0, "end")
            base_cruda = self.bases_mensajeros.get(id_, "0")
            try:
                base_fmt = fmt_moneda(float(base_cruda))
            except ValueError:
                base_fmt = "$0"
            self.entry_base.insert(0, base_fmt)

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

    def _on_base_key_release(self, event=None):
        if not hasattr(self, 'entry_base'): return
        if event and event.keysym in ["Left", "Right", "Up", "Down", "Tab"]: return
        
        valor_raw = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
        valor = "".join(c for c in valor_raw if c.isdigit())
        
        if valor:
            nuevo_texto = f"{int(valor):,}".replace(",", ".")
        else:
            nuevo_texto = ""
            
        actual = self.entry_base.get().replace("$", "")
        if actual != nuevo_texto:
            self.entry_base.delete(0, "end")
            self.entry_base.insert(0, nuevo_texto)

    def _on_base_focus_in(self, event=None):
        if hasattr(self, 'entry_base'):
            valor = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            self.entry_base.delete(0, "end")
            if valor != "0" and valor != "":
                formatted = f"{int(valor):,}".replace(",", ".")
                self.entry_base.insert(0, formatted)

    def _on_base_focus_out(self, event=None):
        if hasattr(self, 'entry_base'):
            valor_crudo = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            if not valor_crudo:
                valor_crudo = "0"
            try:
                valor_fmt = fmt_moneda(float(valor_crudo))
            except ValueError:
                valor_fmt = "$0"
                valor_crudo = "0"

            self.entry_base.delete(0, "end")
            self.entry_base.insert(0, valor_fmt)

            if self.mensajero_seleccionado:
                self.bases_mensajeros[self.mensajero_seleccionado["id"]] = valor_crudo
                try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], float(valor_crudo))
                except Exception: pass

    def _guardar_base_actual(self, event=None):
        """Asigna la base al dar Enter, quitando el foco para que se dispare el evento FocusOut."""
        self.focus() # quitar foco del input asegurando que se procese el valor

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
            self.tree_servicios.insert("", "end", iid=str(s["id"]), values=(
                s["id"],
                fmt_moneda(s["valor"]),
                s.get("descripcion", ""),
                s["fecha"]
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


        # Permitir edición en columna "valor" (#2) o "descripcion" (#3)
        if columna not in ("#2", "#3"):
            return

        valores = self.tree_servicios.item(item, "values")
        bbox = self.tree_servicios.bbox(item, columna)
        if not bbox:
            return

        if columna == "#2":
            valor_actual = valores[1].replace("$", "").replace(".", "")
            justify = "center"
        else:
            valor_actual = valores[2]
            justify = "left"

        entry = ctk.CTkEntry(
            self.tabla_frame,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text"],
            border_color=COLORS["accent"],
            corner_radius=4,
            justify=justify,
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
        self._edit_col = columna

        entry.bind("<Return>", self._confirmar_edicion_inline)
        entry.bind("<Escape>", lambda e: self._cerrar_edicion_inline())
        entry.bind("<FocusOut>", lambda e: self._cerrar_edicion_inline())

    def _confirmar_edicion_inline(self, event=None):
        """Guarda el nuevo valor editado inline."""
        if not self._edit_widget:
            return

        if hasattr(self, '_edit_col') and self._edit_col == "#3":
            nueva_desc = self._edit_widget.get().strip()
            db.actualizar_descripcion_servicio(self._edit_id, nueva_desc)
            self._cerrar_edicion_inline()
            self._cargar_servicios_dia()
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
        if self._edit_widget and self._edit_widget.winfo_exists():
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
            val_base_str = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            val_base = float(val_base_str) if val_base_str else 0
        except ValueError:
            val_base = 0 # Default to 0 if input is invalid

        subtotal = sum(s["valor"] for s in pendientes)
        comision = subtotal * 0.20
        # Ganancia real del trabajo
        ganancia_neta = (subtotal * 0.80) - 1000

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
            
            # Limpiar UI y la base en memoria
            self.entry_base.delete(0, "end")
            self.entry_base.insert(0, "$0")
            if self.mensajero_seleccionado["id"] in self.bases_mensajeros:
                self.bases_mensajeros[self.mensajero_seleccionado["id"]] = "0"
            try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], 0)
            except Exception: pass
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
            servicios_liq = db.obtener_servicios_por_liquidacion(liq["mensajero_id"], liq["id"])
            num_servicios = len(servicios_liq)
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
