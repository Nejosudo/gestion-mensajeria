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

        # Centrado manual robusto
        ancho, alto = 400, 580
        self.withdraw() # Ocultar mientras se posiciona
        self.update_idletasks()
        
        if parent and parent.winfo_exists():
            p_w, p_h = parent.winfo_width(), parent.winfo_height()
            p_x, p_y = parent.winfo_x(), parent.winfo_y()
            
            # Si las dimensiones son inválidas, usar centro de pantalla
            if p_w <= 1:
                p_w, p_h = self.winfo_screenwidth(), self.winfo_screenheight()
                p_x, p_y = 0, 0
            
            x = p_x + (p_w // 2) - (ancho // 2)
            y = p_y + (p_h // 2) - (alto // 2)
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
        
        self.deiconify() # Mostrar ya centrado
        self.lift()
        self.focus()
        self.after(100, self.grab_set)

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

        # Cuerpo
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=35, pady=(20, 10))

        # --- Info del Mensajero --- 
        ctk.CTkLabel(cuerpo, text=f"👤 {datos['mensajero']}", 
                    font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text"]).pack(anchor="w")
        
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        ctk.CTkLabel(cuerpo, text=f"📅 Fecha: {fecha_str}", 
                    font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 15))

        # --- SECCIÓN SUPERIOR (Gris) ---
        f_superior = ctk.CTkFrame(cuerpo, fg_color="#f8f9fa", corner_radius=12)
        f_superior.pack(fill="x", pady=5)

        # Servicios realizados
        f_srv = ctk.CTkFrame(f_superior, fg_color="transparent")
        f_srv.pack(fill="x", padx=15, pady=(15, 8))
        ctk.CTkLabel(f_srv, text="📦  Servicios realizados", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(f_srv, text=str(datos['cant_servicios']), font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(side="right")

        # Subtotal generado
        f_sub = ctk.CTkFrame(f_superior, fg_color="transparent")
        f_sub.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f_sub, text="💰  Subtotal generado", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(f_sub, text=fmt_moneda(datos['subtotal']), font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(side="right")

        # Pago a Mensajero (Rojo y Negativo)
        f_pago = ctk.CTkFrame(f_superior, fg_color="transparent")
        f_pago.pack(fill="x", padx=15, pady=(8, 15))
        ctk.CTkLabel(f_pago, text="🏍️   Pago a Mensajero", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(f_pago, text=f"- {fmt_moneda(datos['pago_final'])}", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["danger"]).pack(side="right")

        # Separador
        ctk.CTkFrame(cuerpo, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20)

        # --- SECCIÓN INFERIOR ---
        # Ganancia Empresa
        f_ganancia = ctk.CTkFrame(cuerpo, fg_color="transparent")
        f_ganancia.pack(fill="x", pady=6)
        ctk.CTkLabel(f_ganancia, text="🏢  GANANCIA EMPRESA:", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(f_ganancia, text=fmt_moneda(datos['comision']), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")

        # Aseo
        f_aseo = ctk.CTkFrame(cuerpo, fg_color="transparent")
        f_aseo.pack(fill="x", pady=6)
        ctk.CTkLabel(f_aseo, text="🖌️  ASEO:", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(f_aseo, text=fmt_moneda(datos['descuento_aseo']), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["success"]).pack(side="right")

        # Base a Devolver
        f_base = ctk.CTkFrame(cuerpo, fg_color="transparent")
        f_base.pack(fill="x", pady=(6, 15))
        ctk.CTkLabel(f_base, text="🏠  BASE A DEVOLVER:", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(f_base, text=fmt_moneda(datos['base']), font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["warning"]).pack(side="right")

        # Botones de acción
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", side="bottom", padx=30, pady=25)

        ctk.CTkButton(
            btns, text="Cancelar", height=42, corner_radius=10,
            fg_color="transparent", border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text_muted"], hover_color="#f8f9fa",
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._btn_confirmar = ctk.CTkButton(
            btns, text="Confirmar y Liquidar", height=42, corner_radius=10,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#ffffff", font=ctk.CTkFont(size=13, weight="bold"),
            command=self._confirmar
        )
        self._btn_confirmar.pack(side="left", fill="x", expand=True)

    def _item_resumen(self, master, label, valor, row, color=None):
        ctk.CTkLabel(master, text=label, font=ctk.CTkFont(size=13), 
                    text_color=COLORS["text"]).grid(row=row, column=0, sticky="w", pady=5)
        ctk.CTkLabel(master, text=valor, font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color=color if color else COLORS["text"]).grid(row=row, column=1, sticky="e", pady=5)
        master.grid_columnconfigure(1, weight=1)

    def _confirmar(self):
        if not self.winfo_exists():
            return
        # Deshabilitar el botón inmediatamente para evitar doble ejecución por doble clic
        self._btn_confirmar.configure(state="disabled", text="Procesando...")
        self.update_idletasks()
        
        # Primero guardamos la referencia a la callback
        callback = self.on_confirm
        
        # Destruimos esta ventana para liberar el foco antes de que la siguiente modal (éxito) aparezca
        self.destroy()
        
        # Ejecutamos la acción final
        callback()


class DialogoExito(ctk.CTkToplevel):
    """Diálogo de éxito centrado manualmente sobre la ventana padre."""
    def __init__(self, parent, titulo="✅ Éxito", mensaje="Operación completada.", boton="Excelente"):
        super().__init__(parent)
        self.title(titulo)
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        self.resizable(False, False)

        # Centrado manual robusto
        ancho, alto = 380, 200
        self.withdraw()
        self.update_idletasks()
        
        if parent and parent.winfo_exists():
            p_w, p_h = parent.winfo_width(), parent.winfo_height()
            p_x, p_y = parent.winfo_x(), parent.winfo_y()
            if p_w <= 1:
                p_w, p_h = self.winfo_screenwidth(), self.winfo_screenheight()
                p_x, p_y = 0, 0
            
            x = p_x + (p_w // 2) - (ancho // 2)
            y = p_y + (p_h // 2) - (alto // 2)
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
        else:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            x, y = (sw // 2) - (ancho // 2), (sh // 2) - (alto // 2)
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
            
        self.deiconify()
        self.lift()
        self.focus()
        self.after(100, self.grab_set)

        # Ícono y mensaje
        ctk.CTkLabel(
            self, text="✅",
            font=ctk.CTkFont(size=36)
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text=mensaje,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            wraplength=320
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            self, text=boton, height=38, width=160,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self.destroy
        ).pack(pady=(0, 20))


class FormularioMensajero(ctk.CTkToplevel):
    """Ventana modal para Crear y Editar mensajeros."""

    def __init__(self, parent, callback, mensajero=None):
        super().__init__(parent)
        self.callback = callback
        self.mensajero = mensajero

        self.title("👤 Datos del Mensajero")
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        self.resizable(False, False)

        # Centrado manual robusto
        ancho, alto = 400, 350
        self.withdraw()
        self.update_idletasks()
        
        if parent and parent.winfo_exists():
            p_w, p_h = parent.winfo_width(), parent.winfo_height()
            p_x, p_y = parent.winfo_x(), parent.winfo_y()
            if p_w <= 1:
                p_w, p_h = self.winfo_screenwidth(), self.winfo_screenheight()
                p_x, p_y = 0, 0
                
            x = p_x + (p_w // 2) - (ancho // 2)
            y = p_y + (p_h // 2) - (alto // 2)
            self.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.deiconify()
        self.lift()
        self.focus()
        self.after(100, self.grab_set)

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
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(parent)
        self.resizable(False, False)
        
        # Centrado manual robusto
        ancho, alto = 400, 480
        self.withdraw()
        self.update_idletasks()
        
        if parent and parent.winfo_exists():
            p_w, p_h = parent.winfo_width(), parent.winfo_height()
            p_x, p_y = parent.winfo_x(), parent.winfo_y()
            if p_w <= 1:
                p_w, p_h = self.winfo_screenwidth(), self.winfo_screenheight()
                p_x, p_y = 0, 0
                
            x = p_x + (p_w // 2) - (ancho // 2)
            y = p_y + (p_h // 2) - (alto // 2)
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
            
        self.deiconify()
        self.lift()
        self.focus()
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
            self, text="💾 Guardar Cambios" if cliente else "➕ Registrar Cliente",
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
