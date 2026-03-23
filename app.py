import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime
from database import database as db
import platform

from core.config import COLORS
from ui.tabs.tab_gestion import TabGestion
from ui.tabs.tab_facturas import TabFacturas
from ui.tabs.tab_finanzas import TabFinanzas

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
        
        if platform.system() == "Windows":
            self.state("zoomed")
        else:
            self.attributes("-zoomed", True)
            
        db.init_db()
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

        # Añadir las pestañas como Frames vacíos primero
        tab1 = self.tabview.add("🏍️  Gestión de Mensajeros")
        tab2 = self.tabview.add("📊  Facturas e Informes")
        tab3 = self.tabview.add("💰  Ingresos y Gastos")

        # Inyectar las instancias modulares
        self.tab_gestion = TabGestion(tab1, app_controller=self)
        self.tab_facturas = TabFacturas(tab2)
        self.tab_finanzas = TabFinanzas(tab3)

        # Forzar color negro en el texto de las pestañas
        try:
            self.tabview._segmented_button.configure(
                text_color="#000000",
                selected_text_color="#000000",
                unselected_text_color="#000000"
            )
        except Exception:
            pass

    def refresh_facturas(self):
        """Llamado desde tab_gestion cuando se ejecuta una liquidación."""
        if hasattr(self, 'tab_facturas'):
            self.tab_facturas.reload_data()
        if hasattr(self, 'tab_finanzas'):
            self.tab_finanzas.reload_data()

if __name__ == "__main__":
    app = App()
    app.mainloop()
