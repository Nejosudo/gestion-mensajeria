import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime
from CTkMessagebox import CTkMessagebox
from core.config import COLORS, fmt_moneda
from database import database as db
from ui.modals import FormularioMensajero, VentanaResumen

class TabGestion(ctk.CTkFrame):
    def __init__(self, parent, app_controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app_controller
        self.pack(fill="both", expand=True)

        self.mensajero_seleccionado: dict | None = None
        self.bases_mensajeros: dict[int, str] = {} # {id_mensajero: valor_string}
        self._messenger_cards: dict[int, tuple[ctk.CTkFrame, ctk.CTkFrame, ctk.CTkLabel, ctk.CTkLabel, ctk.CTkFrame]] = {} # {id_mensajero: (card_widget, inner_frame, name_label, tel_label, status_dot)}
        for m in db.obtener_mensajeros():
            base_bd = m.get("base_actual", 0)
            if base_bd is None: base_bd = 0
            self.bases_mensajeros[m["id"]] = str(int(base_bd) if base_bd == int(base_bd) else base_bd) if base_bd else "0"
            
        self._edit_widget: ctk.CTkEntry | None = None
        self._after_search_id: str | None = None
        self._top_sugerencias: ctk.CTkToplevel | None = None
        self._lista_sugerencias: tk.Listbox | None = None

        self._build_ui()
        self._cargar_mensajeros()


    def _build_ui(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
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
        self.entry_buscar.bind("<KeyRelease>", self._on_search_key_release)


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
            dialog.transient(self.app)
            # Centrar
            dialog.update_idletasks()
            x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (320 // 2)
            y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (150 // 2)
            dialog.geometry(f"320x150+{x}+{y}")
            dialog.lift()
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
            barra_acciones, text="➕ Agregar servicio", width=140, height=32,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            command=self._asignar_servicio
        ).pack(side="right", padx=10)

        # Tabla de servicios del día
        tabla_header = ctk.CTkFrame(panel_der, fg_color="transparent")
        tabla_header.pack(fill="x", padx=15, pady=(5, 0))

        ctk.CTkLabel(
            tabla_header, text="📋  DOMICILIOS DEL DÍA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left")

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

        # Estilo para Treeview (solo una vez en app_controller, pero aquí aseguramos si es necesario)
        style = ttk.Style()
        style.theme_use("clam")
        
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
        self.tree_servicios.tag_configure("par", background=COLORS["table_row_2"])
        self.tree_servicios.tag_configure("atrasado", foreground="#e74c3c") # Color rojo para servicios antiguos

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree_servicios.pack(fill="both", expand=True, padx=2, pady=2)
        self.tree_servicios.bind("<Double-1>", self._on_doble_clic_servicio)

    def _on_search_key_release(self, event=None):
        if self._after_search_id:
            self.after_cancel(self._after_search_id)
        self._after_search_id = self.after(300, self._cargar_mensajeros)

    def _cargar_mensajeros(self):
        for widget in self.lista_mensajeros.winfo_children():
            widget.destroy()
        self._messenger_cards = {}

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
            is_sel = self.mensajero_seleccionado is not None and self.mensajero_seleccionado.get("id") == m["id"]
            tiene_pedidos = (m.get("servicios_pendientes", 0) > 0)
            color_status = COLORS["success"] if tiene_pedidos else COLORS["danger"]
            bg_color_card = COLORS["highlight"] if is_sel else COLORS["bg_card"]
            
            # --- CARD DEL MENSAJERO ---
            card = ctk.CTkFrame(
                self.lista_mensajeros,
                fg_color=bg_color_card,
                border_width=1 if is_sel else 0,
                border_color=COLORS["accent"] if is_sel else bg_color_card,
                corner_radius=10,
                height=70, 
                cursor="hand2"
            )
            card.pack(fill="x", pady=4, padx=8)
            card.pack_propagate(False)

            # Contenedor Texto (Sin usar 'transparent' para total estabilidad)
            txt_frame = ctk.CTkFrame(card, fg_color=bg_color_card)
            txt_frame.pack(side="left", fill="both", expand=True, padx=(12, 5), pady=8)

            lbl_nombre = ctk.CTkLabel(
                txt_frame, text=f"👤 {m['nombre']}",
                font=ctk.CTkFont(size=13, weight="bold" if is_sel else "normal"),
                text_color=COLORS["text"],
                anchor="w",
                wraplength=170,
                fg_color=bg_color_card
            )
            lbl_nombre.pack(fill="x", side="top")

            lbl_tel = ctk.CTkLabel(
                txt_frame, text=f"📞 {m['telefono']}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
                anchor="w",
                fg_color=bg_color_card
            )
            lbl_tel.pack(fill="x", side="top")

            # Indicador de Estatus (Derecha)
            status_dot = ctk.CTkFrame(
                card, width=12, height=12, 
                corner_radius=6, 
                fg_color=color_status
            )
            status_dot.pack(side="right", padx=15)

            # Bindings manuales (estos son 100% compatibles)
            def on_click(event, mid=m["id"], mn=m["nombre"], mt=m["telefono"]):
                self._seleccionar_mensajero(mid, mn, mt)

            card.bind("<Button-1>", on_click)
            lbl_nombre.bind("<Button-1>", on_click)
            lbl_tel.bind("<Button-1>", on_click)
            txt_frame.bind("<Button-1>", on_click)
            status_dot.bind("<Button-1>", on_click)
            
            # Guardar referencia para actualizar sin recargar lista
            self._messenger_cards[m["id"]] = (card, txt_frame, lbl_nombre, lbl_tel, status_dot)

    def _seleccionar_mensajero(self, id_: int, nombre: str, telefono: str):
        # Limpiar búsqueda y quitar foco
        self.entry_buscar.delete(0, "end")
        self.focus()

        if self.mensajero_seleccionado and hasattr(self, 'entry_base'):
            base_cruda = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            val_to_save = base_cruda if base_cruda else "0"
            self.bases_mensajeros[self.mensajero_seleccionado["id"]] = val_to_save
            try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], float(val_to_save))
            except Exception: pass

        self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
        self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        
        # ACTUALIZACIÓN VISUAL DE LA LISTA SIN RECARGAR (Evita Pestañeo)
        for mid, (card, txt, ln, lt, dot) in self._messenger_cards.items():
            is_new_sel = (mid == id_)
            bg = COLORS["highlight"] if is_new_sel else COLORS["bg_card"]
            card.configure(fg_color=bg, border_width=1 if is_new_sel else 0, border_color=COLORS["accent"] if is_new_sel else bg)
            txt.configure(fg_color=bg)
            ln.configure(fg_color=bg, font=ctk.CTkFont(size=13, weight="bold" if is_new_sel else "normal"))
            lt.configure(fg_color=bg)

        self._cargar_servicios_pendientes()

        if hasattr(self, 'entry_base'):
            self.entry_base.delete(0, "end")
            base_cruda = self.bases_mensajeros.get(id_, "0")
            try:
                base_fmt = fmt_moneda(float(base_cruda))
            except ValueError:
                base_fmt = "$0"
            self.entry_base.insert(0, base_fmt)

    def _abrir_form_nuevo(self):
        FormularioMensajero(self.app, self._procesar_form_mensajero)

    def _abrir_form_editar(self):
        if not self.mensajero_seleccionado:
            CTkMessagebox(title="Aviso", message="Selecciona un mensajero de la lista.", icon="warning")
            return
        FormularioMensajero(self.app, self._procesar_form_mensajero, self.mensajero_seleccionado)

    def _procesar_form_mensajero(self, nombre, telefono, id_=None):
        if id_ and self.mensajero_seleccionado:
            db.actualizar_mensajero(id_, nombre, telefono)
            self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
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
            title="👤 Confirmar eliminación",
            message=f"¿Eliminar al mensajero '{self.mensajero_seleccionado['nombre']}'?\n\n"
                    f"Nota: Las facturas y liquidaciones pasadas se conservarán para el historial del negocio.",
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
        if hasattr(self, 'focus'):
            self.focus()

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

        db.crear_servicio(self.mensajero_seleccionado["id"], valor, "")
        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, "5000")
        self._cargar_servicios_pendientes()
        self._actualizar_status_visual_mensajero(self.mensajero_seleccionado["id"])
        
        # Actualizar contador de clientes
        if hasattr(self.app, 'refresh_clientes'):
            self.app.refresh_clientes()

    def _cargar_servicios_pendientes(self):
        self._limpiar_tabla_servicios()
        if not self.mensajero_seleccionado:
            return

        servicios = db.obtener_servicios_pendientes(self.mensajero_seleccionado["id"])
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        for i, s in enumerate(servicios):
            tags = []
            if i % 2 == 1:
                tags.append("par")
            
            # Si el servicio no es de hoy, marcar como atrasado
            fecha_servicio = s["fecha"].split(" ")[0]
            if fecha_servicio != hoy:
                tags.append("atrasado")
                
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
        seleccion = self.tree_servicios.selection()
        if not seleccion:
            CTkMessagebox(title="⚠️ Sin selección", message="Selecciona un servicio de la tabla.",
                          icon="warning", option_1="OK")
            return
        id_servicio = int(seleccion[0])
        valores = self.tree_servicios.item(seleccion[0], "values")
        # Assuming the status is not directly in values, but rather implied by being "pending"
        # If there was a "status" column, we'd check that. For now, assume it's pending if in this list.
        
        msg = CTkMessagebox(
            title="🗑️ Eliminar servicio",
            message=f"¿Eliminar el servicio #{id_servicio} con valor {valores[1]}?",
            icon="question", option_1="Cancelar", option_2="Eliminar"
        )
        if msg.get() == "Eliminar":
            try:
                db.eliminar_servicio(id_servicio)
                self._cargar_servicios_pendientes()
                if self.mensajero_seleccionado:
                    self._actualizar_status_visual_mensajero(self.mensajero_seleccionado["id"])
            except Exception as e:
                CTkMessagebox(title="Error", message=f"No se pudo eliminar el servicio: {e}", icon="cancel")

    def _on_doble_clic_servicio(self, event):
        self._cerrar_edicion_inline()
        region = self.tree_servicios.identify("region", event.x, event.y)
        if region != "cell": return
        columna = self.tree_servicios.identify_column(event.x)
        item = self.tree_servicios.identify_row(event.y)
        if not item: return
        if columna not in ("#2", "#3"): return

        valores = self.tree_servicios.item(item, "values")
        bbox = self.tree_servicios.bbox(item, columna)
        if not bbox: return

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
        entry.bind("<FocusOut>", lambda e: self._on_inline_focus_out(e))

        if columna == "#3":
            entry.bind("<KeyRelease>", lambda e: self._autocomplete_key_release(e, entry))

    def _confirmar_edicion_inline(self, event=None):
        if not self._edit_widget: return

        if hasattr(self, '_edit_col') and self._edit_col == "#3":
            nueva_desc = self._edit_widget.get().strip()
            db.actualizar_descripcion_servicio(self._edit_id, nueva_desc)
            self._cerrar_edicion_inline()
            self._cargar_servicios_pendientes()
            # Actualizar contador de clientes
            if hasattr(self.app, 'refresh_clientes'):
                self.app.refresh_clientes()
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
        self._cargar_servicios_pendientes()

    def _cerrar_edicion_inline(self):
        if self._edit_widget and self._edit_widget.winfo_exists():
            self._edit_widget.destroy()
        self._edit_widget = None

    def _ejecutar_liquidacion(self):
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

        try:
            val_base_str = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            val_base = float(val_base_str) if val_base_str else 0
        except ValueError:
            val_base = 0

        # Calcular aseo por días calendario desde el más antiguo hasta hoy
        fechas = [datetime.strptime(s["fecha"], "%Y-%m-%d %H:%M:%S").date() for s in pendientes]
        fecha_min = min(fechas)
        fecha_hoy = datetime.now().date()
        num_dias = (fecha_hoy - fecha_min).days + 1
        descuento_aseo_total = 1000 * num_dias

        subtotal = sum(s["valor"] for s in pendientes)
        comision = subtotal * 0.20
        ganancia_neta = (subtotal * 0.80) - descuento_aseo_total

        datos_liquidacion = {
            "nombre": self.mensajero_seleccionado['nombre'],
            "num_servicios": len(pendientes),
            "subtotal": subtotal,
            "comision": comision,
            "neto": ganancia_neta,
            "base": val_base,
            "descuento_aseo": descuento_aseo_total
        }

        def confirmar_final():
            db.ejecutar_liquidacion(self.mensajero_seleccionado["id"], val_base, pendientes)
            self.entry_base.delete(0, "end")
            self.entry_base.insert(0, "$0")
            if self.mensajero_seleccionado["id"] in self.bases_mensajeros:
                self.bases_mensajeros[self.mensajero_seleccionado["id"]] = "0"
            try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], 0)
            except Exception: pass
            self._cargar_servicios_pendientes()
            self._actualizar_status_visual_mensajero(self.mensajero_seleccionado["id"])
            
            # TRIGGER UPDATE ON FACTURAS TAB
            if hasattr(self.app, 'refresh_facturas'):
                self.app.refresh_facturas()
                
            CTkMessagebox(
                title="✅ Éxito",
                message="La liquidación se ha procesado correctamente.",
                icon="check", option_1="Excelente"
            )

        VentanaResumen(self.app, datos_liquidacion, confirmar_final)

    # ── Autocomplete Logic ─────────────────────────────────────────────

    def _autocomplete_key_release(self, event, entry):
        # Ignorar teclas que no sean letras, números o espacios (como Backspace, Flechas, etc)
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Return", "Escape", "Tab"):
            return

        texto = entry.get()
        if not texto: return

        # Buscar sugerencia (solo que empiecen por el texto ingresado)
        sugerencias = db.sugerir_clientes(texto)
        if sugerencias:
            sugerencia = sugerencias[0]
            if sugerencia.lower().startswith(texto.lower()):
                # Insertar el resto y seleccionarlo
                pos = len(texto)
                entry.delete(0, "end")
                entry.insert(0, sugerencia)
                entry.select_range(pos, "end")
                entry.icursor(pos) 

    def _actualizar_status_visual_mensajero(self, id_mensajero: int):
        """Actualiza el color del círculo de estatus sin recargar toda la lista."""
        if id_mensajero not in self._messenger_cards: return
        
        # Consultar solo los pendientes de este mensajero
        pendientes = db.obtener_servicios_pendientes(id_mensajero)
        tiene_trabajo = len(pendientes) > 0
        color = COLORS["success"] if tiene_trabajo else COLORS["danger"]
        
        # Actualizar el widget
        dot = self._messenger_cards[id_mensajero][4]
        dot.configure(fg_color=color)

    def _on_inline_focus_out(self, event):
        self._cerrar_edicion_inline()
