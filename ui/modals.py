import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from datetime import datetime
from core.config import COLORS, fmt_moneda

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
        self.update()
        if parent.winfo_exists():
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (ancho // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (alto // 2)
            if self.winfo_exists():
                self.geometry(f"{ancho}x{alto}+{x}+{y}")
            
        self.lift()
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
        ctk.CTkLabel(f_aseo, text=fmt_moneda(datos.get('descuento_aseo', 1000)), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")

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
        self.update()
        if self.master and self.master.winfo_exists():
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (400 // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (350 // 2)
            self.geometry(f"+{x}+{y}")
            
        self.lift()
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
        ctk.CTkLabel(form, text="Telefono:", text_color=COLORS["text_muted"]).pack(anchor="w")
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

class FormularioCliente(ctk.CTkToplevel):
    """Ventana modal para Crear y Editar clientes."""
    def __init__(self, parent, callback, cliente=None):
        super().__init__(parent)
        self.callback = callback
        self.cliente = cliente

        self.title("👥 Datos del Cliente")
        self.geometry("400x480")
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        
        self.update()
        if self.master and self.master.winfo_exists():
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (400 // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (480 // 2)
            self.geometry(f"+{x}+{y}")
            
        self.lift()
        self.grab_set()

        ctk.CTkLabel(self, text="GESTIÓN DE CLIENTE", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["accent"]).pack(pady=20)
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=40)

        ctk.CTkLabel(form, text="Nombre Completo:", text_color=COLORS["text_muted"]).pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(form, height=35, fg_color=COLORS["bg_input"])
        self.entry_nombre.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Dirección:", text_color=COLORS["text_muted"]).pack(anchor="w")
        self.entry_dir = ctk.CTkEntry(form, height=35, fg_color=COLORS["bg_input"])
        self.entry_dir.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Teléfono:", text_color=COLORS["text_muted"]).pack(anchor="w")
        vcmd = (self.register(self._validar_telefono), '%P')
        self.entry_tel = ctk.CTkEntry(
            form, height=35, fg_color=COLORS["bg_input"],
            validate="key", validatecommand=vcmd
        )
        self.entry_tel.pack(fill="x", pady=(2, 10))

        if cliente:
            self.entry_nombre.insert(0, cliente["nombre"])
            self.entry_dir.insert(0, cliente.get("direccion", ""))
            self.entry_tel.insert(0, cliente.get("telefono", ""))

        self.btn_guardar = ctk.CTkButton(
            self, text="💾 Guardar Clientes" if cliente else "➕ Registrar Cliente",
            fg_color=COLORS["success"], hover_color="#219150", height=45,
            font=ctk.CTkFont(weight="bold"),
            command=self._guardar
        )
        self.btn_guardar.pack(fill="x", padx=40, pady=25)

    def _validar_telefono(self, P):
        """Valida que el teléfono solo contenga números y máximo 11 dígitos."""
        if P == "": return True
        return P.isdigit() and len(P) <= 11

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        direccion = self.entry_dir.get().strip()
        telefono = self.entry_tel.get().strip()

        if not nombre:
            CTkMessagebox(title="Error", message="El nombre es obligatorio.", icon="warning")
            return
            
        self.callback(nombre, direccion, telefono, self.cliente["id"] if self.cliente else None)
        self.destroy()
