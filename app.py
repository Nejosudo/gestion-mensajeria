import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime
from database import database as db
import platform
from core.config import COLORS
from ui.tabs.tab_gestion import TabGestion
from ui.tabs.tab_facturas import TabFacturas
from ui.tabs.tab_finanzas import TabFinanzas
from ui.tabs.tab_clientes import TabClientes
from ui.tabs.tab_turnero import TabTurnero, VentanaTurnero

# ── Configuración global ──
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()

        # ── Ventana ──
        self.title("📦 Sistema de Mensajería — Gestión y Liquidación")
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        db.init_db()  # Asegurar que las tablas (incluida Configuracion) existan
        self.withdraw()  # Oculta la ventana principal
        self._ventana_login()

    def _ventana_login(self):
        login = ctk.CTkToplevel(self)
        login.title("Acceso restringido")
        login.geometry("340x180")
        login.resizable(False, False)
        
        # Centrar en el centro de la pantalla
        self.update_idletasks()
        screen_w = login.winfo_screenwidth()
        screen_h = login.winfo_screenheight()
        x = (screen_w // 2) - (340 // 2)
        y = (screen_h // 2) - (180 // 2)
        login.geometry(f"340x180+{x}+{y}")
        
        login.lift()
        login.focus_force()
        login.after(100, login.grab_set)

        ctk.CTkLabel(login, text="Ingrese la contraseña", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(20, 10))
        entry_pass = ctk.CTkEntry(login, show="*", width=200)
        entry_pass.pack(pady=5)

        def check_pass():
            if entry_pass.get() == db.get_app_password("login"):
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
        
        if platform.system() == "Windows":
            self.state("zoomed")
        else:
            self.attributes("-zoomed", True)
            
        self._init_global_styles()
        self._build_ui()
            
        self.deiconify()  # Muestra la ventana ya cargada

    def _init_global_styles(self):
        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=COLORS["table_row_1"],
                         foreground=COLORS["text"],
                         fieldbackground=COLORS["table_row_1"],
                         borderwidth=0,
                         rowheight=32,
                         font=("Arial", 11))
        style.configure("Dark.Treeview.Heading",
                         background=COLORS["table_header"],
                         foreground=COLORS["accent"],
                         borderwidth=0,
                         font=("Arial", 11, "bold"),
                         relief="flat")
        style.map("Dark.Treeview",
                   background=[("selected", COLORS["highlight"])],
                   foreground=[("selected", COLORS["text"])])

    def _build_ui(self):
        """Crea el layout principal con CTkTabview."""

        # ── Header ──
        header = ctk.CTkFrame(self, height=60, fg_color=COLORS["bg_card"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="📦  SISTEMA DE MENSAJERÍA",
            font=ctk.CTkFont(family=("Arial", "Segoe UI"), size=20, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=20)

        self.lbl_fecha = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family=("Arial", "Segoe UI"), size=15, weight="bold"),
            text_color=COLORS["text"]
        )
        self.lbl_fecha.pack(side="right", padx=20)

        self.btn_config = ctk.CTkButton(
            header, text="⚙️", width=40, height=32,
            fg_color="transparent", text_color=COLORS["text"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=20),
            command=self._abrir_configuracion
        )
        self.btn_config.pack(side="right", padx=5)
        

        # self._update_clock()

        # ── Tabview ──
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["border"],
            corner_radius=12,
            command=self._on_tab_switch
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # Añadir las pestañas como Frames vacíos primero
        tab1 = self.tabview.add("🏍️  Gestión de Mensajeros")
        tab2 = self.tabview.add("👥  Gestión de Clientes")
        tab3 = self.tabview.add("📊  Facturas e Informes")
        tab4 = self.tabview.add("💰  Ingresos y Gastos")

        # Inyectar las instancias modulares
        self.tab_gestion = TabGestion(tab1, app_controller=self)
        self.tab_clientes = TabClientes(tab2)
        self.tab_facturas = TabFacturas(tab3)
        self.tab_finanzas = TabFinanzas(tab4)
        

        # Forzar color negro en el texto de las pestañas
        try:
            self.tabview._segmented_button.configure(
                text_color="#000000",
                selected_text_color="#3a86ff", # Azul acento cuando está seleccionado
                unselected_text_color="#636e72"
            )
        except Exception:
            pass

    def _update_clock(self):
        """Actualiza la hora cada segundo."""
        ahora = datetime.now()
        texto = ahora.strftime("📅 %d/%m/%Y   —   🕒 %H:%M:%S")
        self.lbl_fecha.configure(text=texto)
        self.after(1000, self._update_clock)

    def _on_tab_switch(self):
        tab = self.tabview.get()
        if "Clientes" in tab and hasattr(self, 'tab_clientes'):
            self.tab_clientes.reload_data()
        elif "Facturas" in tab and hasattr(self, 'tab_facturas'):
            self.tab_facturas.reload_data()

    def refresh_facturas(self):
        """Llamado desde tab_gestion cuando se ejecuta una liquidación."""
        if hasattr(self, 'tab_facturas'):
            self.tab_facturas.reload_data()
        if hasattr(self, 'tab_finanzas'):
            self.tab_finanzas.reload_data()

    def refresh_gestion(self):
        """Refresca la pestaña de gestión (útil cuando cambia el turnero)."""
        if hasattr(self, 'tab_gestion'):
            self.tab_gestion._cargar_mensajeros()

    def _abrir_configuracion(self):
        """Abre ventana de configuración para cambio de contraseña y porcentaje."""
        modal = ctk.CTkToplevel(self)
        modal.title("Configuración")
        modal.geometry("420x550")
        modal.resizable(False, False)
        
        # Centrar relativo a la principal
        x = self.winfo_x() + (self.winfo_width() // 2) - 210
        y = self.winfo_y() + (self.winfo_height() // 2) - 275
        modal.geometry(f"420x550+{x}+{y}")

        # Asegurar que sea visible antes del grab_set
        modal.after(10, modal.focus_force)
        modal.after(100, modal.grab_set)

        ctk.CTkLabel(modal, text="⚙️ Configuración de Seguridad", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        # Frame contenedor
        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(pady=10, padx=40, fill="both")

        # --- SECCIÓN: CONTRASEÑA LOGIN ---
        group_login = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border"])
        group_login.pack(fill="x", pady=(0, 15), ipady=10)
        ctk.CTkLabel(group_login, text="🔑 Cambiar Contraseña de Inicio", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        f_login = ctk.CTkFrame(group_login, fg_color="transparent")
        f_login.pack(fill="x", padx=20)
        
        old_login = ctk.CTkEntry(f_login, show="*", placeholder_text="Contraseña Actual", height=32)
        old_login.pack(fill="x", pady=2)
        new_login = ctk.CTkEntry(f_login, show="*", placeholder_text="Nueva Contraseña", height=32)
        new_login.pack(fill="x", pady=2)
        conf_login = ctk.CTkEntry(f_login, show="*", placeholder_text="Confirmar Nueva", height=32)
        conf_login.pack(fill="x", pady=2)

        def guardar_login():
            actual = old_login.get()
            nueva = new_login.get()
            confirm = conf_login.get()
            if not actual or not nueva:
                CTkMessagebox(title="Aviso", message="Completa los campos de contraseña login.", icon="warning")
                return
            if actual != db.get_app_password("login"):
                CTkMessagebox(title="Error", message="Contraseña actual de inicio incorrecta.", icon="cancel")
                return
            if len(nueva) < 4:
                CTkMessagebox(title="Error", message="Mínimo 4 caracteres.", icon="warning")
                return
            if nueva != confirm:
                CTkMessagebox(title="Error", message="Las contraseñas no coinciden.", icon="warning")
                return
            db.set_app_password(nueva, "login")
            CTkMessagebox(title="Éxito", message="Contraseña de inicio actualizada.", icon="check")
            old_login.delete(0, "end"); new_login.delete(0, "end"); conf_login.delete(0, "end")

        ctk.CTkButton(group_login, text="Actualizar Login", height=30, fg_color=COLORS["accent"], command=guardar_login).pack(pady=10)

        # --- SECCIÓN: CONTRASEÑA OPERATIVA ---
        group_op = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border"])
        group_op.pack(fill="x", pady=(0, 15), ipady=10)
        ctk.CTkLabel(group_op, text="🛡️ Cambiar Contraseña Operativa", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        f_op = ctk.CTkFrame(group_op, fg_color="transparent")
        f_op.pack(fill="x", padx=20)
        
        old_op = ctk.CTkEntry(f_op, show="*", placeholder_text="Contraseña Operativa Actual", height=32)
        old_op.pack(fill="x", pady=2)
        new_op = ctk.CTkEntry(f_op, show="*", placeholder_text="Nueva Contraseña Operativa", height=32)
        new_op.pack(fill="x", pady=2)
        conf_op = ctk.CTkEntry(f_op, show="*", placeholder_text="Confirmar Nueva", height=32)
        conf_op.pack(fill="x", pady=2)

        def guardar_op():
            actual = old_op.get()
            nueva = new_op.get()
            confirm = conf_op.get()
            if not actual or not nueva:
                CTkMessagebox(title="Aviso", message="Completa los campos de contraseña operativa.", icon="warning")
                return
            if actual != db.get_app_password("operativa"):
                CTkMessagebox(title="Error", message="Contraseña operativa actual incorrecta.", icon="cancel")
                return
            if len(nueva) < 4:
                CTkMessagebox(title="Error", message="Mínimo 4 caracteres.", icon="warning")
                return
            if nueva != confirm:
                CTkMessagebox(title="Error", message="Las contraseñas no coinciden.", icon="warning")
                return
            db.set_app_password(nueva, "operativa")
            CTkMessagebox(title="Éxito", message="Contraseña operativa actualizada.", icon="check")
            old_op.delete(0, "end"); new_op.delete(0, "end"); conf_op.delete(0, "end")

        ctk.CTkButton(group_op, text="Actualizar Operativa", height=30, fg_color=COLORS["danger"], command=guardar_op).pack(pady=10)

        # --- SECCIÓN: PORCENTAJE EMPRESA ---
        group_pct = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border"])
        group_pct.pack(fill="x", pady=(0, 15), ipady=10)
        ctk.CTkLabel(group_pct, text="📈 Porcentaje de Ganancia", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        f_pct = ctk.CTkFrame(group_pct, fg_color="transparent")
        f_pct.pack(fill="x", padx=20)
        
        try: pct_val = db.get_porcentaje_empresa()
        except: pct_val = 20
        
        ctk.CTkLabel(f_pct, text="Nuevo Porcentaje (%):", anchor="w").pack(fill="x")
        ent_pct = ctk.CTkEntry(f_pct, height=32)
        ent_pct.pack(fill="x", pady=2)
        ent_pct.insert(0, str(int(pct_val)))
        
        ctk.CTkLabel(f_pct, text="Autorizar con Pass Operativa:", anchor="w", text_color=COLORS["danger"]).pack(fill="x")
        pass_auth = ctk.CTkEntry(f_pct, show="*", placeholder_text="Pass Operativa", height=32)
        pass_auth.pack(fill="x", pady=2)

        def guardar_pct():
            auth = pass_auth.get()
            if auth != db.get_app_password("operativa"):
                CTkMessagebox(title="Error", message="Contraseña operativa incorrecta.", icon="cancel")
                return
            try:
                val = float(ent_pct.get())
                if 0 <= val <= 100:
                    db.set_porcentaje_empresa(val)
                    CTkMessagebox(title="Éxito", message="Porcentaje actualizado.", icon="check")
                    pass_auth.delete(0, "end")
                else: raise ValueError
            except:
                CTkMessagebox(title="Error", message="Ingresa un número entre 0 y 100.", icon="warning")

        ctk.CTkButton(group_pct, text="Guardar Porcentaje", height=30, fg_color=COLORS["success"], command=guardar_pct).pack(pady=10)

        ctk.CTkButton(modal, text="Cerrar Configuración", fg_color="gray", command=modal.destroy, width=150).pack(pady=10)

        # El botón de cerrar ya está arriba.

    def refresh_clientes(self):
        """Llamado desde tab_gestion cuando se asigna un cliente."""
        if hasattr(self, 'tab_clientes'):
            self.tab_clientes.reload_data()

if __name__ == "__main__":
    app = App()
    app.mainloop()
