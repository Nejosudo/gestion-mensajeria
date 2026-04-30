import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime
from CTkMessagebox import CTkMessagebox
from core.config import COLORS, fmt_moneda, CTkToolTip
from database import database as db
from ui.modals import FormularioMensajero, VentanaResumen, DialogoExito
from database.exportador import exportar_servicios_pendientes
import tkinter as tk

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
        self._cargar_cola()


    def _build_ui(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_columnconfigure(0, weight=1, minsize=280) # Mensajeros
        contenedor.grid_columnconfigure(1, weight=1, minsize=260) # Turnero
        contenedor.grid_columnconfigure(2, weight=2, minsize=400) # Servicios
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
            dialog.update()
            x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (320 // 2)
            y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (150 // 2)
            dialog.geometry(f"320x150+{x}+{y}")
            dialog.lift()
            dialog.after(100, dialog.grab_set)

            ctk.CTkLabel(dialog, text="Ingrese la contraseña", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(18, 8))
            entry = ctk.CTkEntry(dialog, show="*", width=180)
            entry.pack(pady=5)

            def check():
                if entry.get() == db.get_app_password():
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
        panel_der.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=0)

        # Barra superior del panel derecho
        barra_sup = ctk.CTkFrame(panel_der, fg_color="transparent")
        barra_sup.pack(fill="x", padx=15, pady=(12, 5))

        self.lbl_mensajero_sel = ctk.CTkLabel(
            barra_sup, text="Selecciona un mensajero ←",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        )
        self.lbl_mensajero_sel.pack(side="left")

        # ── Barra de Acciones (Servicio + Cliente + Descripción + Base) ──
        barra_acciones = ctk.CTkFrame(panel_der, fg_color=COLORS["bg_input"], corner_radius=10, height=60)
        barra_acciones.pack(fill="x", padx=15, pady=(0, 8))
        barra_acciones.pack_propagate(False) 

        # Sección Servicio
        section_svc = ctk.CTkFrame(barra_acciones, fg_color="transparent")
        section_svc.pack(side="left", fill="y", padx=(10, 0))

        ctk.CTkLabel(section_svc, text="💰", font=ctk.CTkFont(size=14)).pack(side="left", padx=2)
        self.entry_valor = ctk.CTkEntry(
            section_svc, width=70, placeholder_text="5000",
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text"], corner_radius=6, height=28,
            justify="center"
        )
        self.entry_valor.pack(side="left", padx=2)
        self.entry_valor.insert(0, "5000")

        # Separador visual
        ctk.CTkFrame(barra_acciones, width=1, fg_color=COLORS["border"]).pack(side="left", fill="y", padx=10, pady=12)

        # Sección Base
        section_base = ctk.CTkFrame(barra_acciones, fg_color="transparent")
        section_base.pack(side="left", fill="y")

        ctk.CTkLabel(section_base, text="🏦 Base", font=ctk.CTkFont(size=14)).pack(side="left", padx=2)
        self.entry_base = ctk.CTkEntry(
            section_base, width=75, placeholder_text="0",
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

        # Botones de acción a la derecha
        self.btn_agregar = ctk.CTkButton(
            barra_acciones, text="Agregar servicio", width=160, height=32,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
            command=self._asignar_servicio
        )
        self.btn_agregar.pack(side="right", padx=10)
        CTkToolTip(self.btn_agregar, "Asignar este servicio al mensajero")

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

        # Estilo para Treeview
        style = ttk.Style()
        style.theme_use("clam")
        
        self.tree_servicios = ttk.Treeview(
            self.tabla_frame,
            columns=("id", "cliente", "valor", "descripcion", "fecha"),
            show="headings",
            style="Dark.Treeview",
            selectmode="extended"
        )
        self.tree_servicios.heading("id", text="ID")
        self.tree_servicios.heading("cliente", text="👤 Cliente")
        self.tree_servicios.heading("valor", text="💰 Valor")
        self.tree_servicios.heading("descripcion", text="📝 Notas / Descripción")
        self.tree_servicios.heading("fecha", text="🕒 Fecha / Hora")

        self.tree_servicios.column("id", width=40, anchor="center")
        self.tree_servicios.column("cliente", width=140, anchor="w")
        self.tree_servicios.column("valor", width=90, anchor="center")
        self.tree_servicios.column("descripcion", width=180, anchor="w")
        self.tree_servicios.column("fecha", width=150, anchor="center")
        self.tree_servicios.tag_configure("par", background=COLORS["table_row_2"])
        self.tree_servicios.tag_configure("atrasado", foreground="#e74c3c") # Color rojo para servicios antiguos

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree_servicios.pack(fill="both", expand=True, padx=2, pady=2)
        self.tree_servicios.bind("<Double-1>", self._on_doble_clic_servicio)


        # ── Panel Central: Turnero ──
        panel_turnero = ctk.CTkFrame(contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        panel_turnero.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        header_turnero = ctk.CTkFrame(panel_turnero, fg_color="transparent")
        header_turnero.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header_turnero, text="🔄 Turnero",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#27ae60"
        ).pack(side="left")

        ctk.CTkButton(
            header_turnero, text="🧹 Limpiar", width=70, height=28,
            fg_color=COLORS["danger"], text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._limpiar_turnero
        ).pack(side="right")

        # Entrada por teclado para identificativo
        frame_input_turno = ctk.CTkFrame(panel_turnero, fg_color="transparent")
        frame_input_turno.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(frame_input_turno, text="⌨️ Identificativo:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        self.entry_turno_id = ctk.CTkEntry(frame_input_turno, width=80, fg_color=COLORS["bg_input"], text_color=COLORS["text"])
        self.entry_turno_id.pack(side="left", fill="x", expand=True)
        self.entry_turno_id.bind("<Return>", self._procesar_id_turno)

        self.scroll_cola = ctk.CTkScrollableFrame(panel_turnero, fg_color="transparent")
        self.scroll_cola.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Variables para render del turnero
        self._cola_cards = {}

    def _on_search_key_release(self, event=None):
        """Debounce más corto para mayor agilidad."""
        if hasattr(self, "_search_job") and self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(100, self._cargar_mensajeros)

    def _cargar_mensajeros(self):
        busqueda = self.entry_buscar.get().strip()
        
        # 1. Obtener datos necesarios
        cola = db.obtener_cola_turnos()
        ids_en_cola = [t["mensajero_id"] for t in cola]
        pos_cola = {id_m: i for i, id_m in enumerate(ids_en_cola)}
        mensajeros_all = db.obtener_mensajeros(busqueda)
        
        # 2. Separar y ordenar
        mensajeros_activos = [m for m in mensajeros_all if (m.get("estado_trabajo") or "trabajando").lower() != "descanso"]
        en_cola = [m for m in mensajeros_activos if m["id"] in pos_cola]
        en_cola.sort(key=lambda x: pos_cola[x["id"]])
        fuera_cola = [m for m in mensajeros_activos if m["id"] not in pos_cola]
        lista_final = en_cola + fuera_cola

        # 3. Limpieza y Reconciliación (Grid es más estable)
        ids_nuevos = [m["id"] for m in lista_final]
        ids_actuales = list(self._messenger_cards.keys())

        for mid in ids_actuales:
            if mid not in ids_nuevos:
                widgets = self._messenger_cards.pop(mid)
                widgets[0].destroy()

        if not lista_final:
            for w in self.lista_mensajeros.winfo_children(): w.destroy()
            self._messenger_cards.clear()
            ctk.CTkLabel(self.lista_mensajeros, text="No hay mensajeros", font=ctk.CTkFont(size=11, slant="italic"), text_color=COLORS["text_muted"]).grid(row=0, column=0, pady=20, sticky="ew")
            self.lista_mensajeros.grid_columnconfigure(0, weight=1)
            return

        # Limpiar mensaje de "No hay" si existe
        for w in self.lista_mensajeros.winfo_children():
            if isinstance(w, ctk.CTkLabel) and "No hay" in w.cget("text"): w.destroy()

        # 4. Actualizar o Crear usando GRID
        self.lista_mensajeros.grid_columnconfigure(0, weight=1)
        for i, m in enumerate(lista_final):
            mid = m["id"]
            is_sel = self.mensajero_seleccionado is not None and self.mensajero_seleccionado.get("id") == mid
            tiene_pedidos = (m.get("servicios_pendientes", 0) > 0)
            color_status = COLORS["success"] if tiene_pedidos else COLORS["danger"]

            # El color verde del primero en la cola siempre prevalece
            es_primero_en_cola = (len(ids_en_cola) > 0 and mid == ids_en_cola[0])
            if es_primero_en_cola:
                bg_color_card = "#ebf9f1"
                border_width = 2
                border_color = COLORS["success"]
            else:
                bg_color_card = COLORS["highlight"] if is_sel else COLORS["bg_card"]
                border_width = 1 if is_sel else 0
                border_color = COLORS["accent"] if is_sel else bg_color_card

            if mid not in self._messenger_cards:
                card = ctk.CTkFrame(self.lista_mensajeros, fg_color=bg_color_card, corner_radius=10, height=70, cursor="hand2", border_width=border_width, border_color=border_color)
                card.grid(row=i, column=0, pady=4, padx=8, sticky="ew")
                card.grid_propagate(False)

                txt_frame = ctk.CTkFrame(card, fg_color=bg_color_card)
                txt_frame.pack(side="left", fill="both", expand=True, padx=(12, 5), pady=8)

                ln = ctk.CTkLabel(txt_frame, text=f"👤 {m['nombre']}", font=ctk.CTkFont(size=18, weight="bold" if is_sel else "normal"), text_color=COLORS["text"], anchor="w", wraplength=170, fg_color=bg_color_card)
                ln.pack(fill="x", side="top")

                lt = ctk.CTkLabel(txt_frame, text=f"📞 {m['telefono']}", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], anchor="w", fg_color=bg_color_card)
                lt.pack(fill="x", side="top")

                # Mostrar días de descanso si existen
                descanso_txt = m.get('dias_descanso', '').strip()
                descanso_str = f"💤 Descansa: {descanso_txt}" if descanso_txt else "💤 Sin asignar"
                ld = ctk.CTkLabel(txt_frame, text=descanso_str, font=ctk.CTkFont(size=10, slant="italic"), text_color=COLORS["text_muted"], anchor="w", fg_color=bg_color_card)
                ld.pack(fill="x", side="top")

                dot = ctk.CTkFrame(card, width=12, height=12, corner_radius=6, fg_color=color_status)
                dot.pack(side="right", padx=15)

                def on_click(event, _mid=mid, _mn=m["nombre"], _mt=m["telefono"]):
                    self._seleccionar_mensajero(_mid, _mn, _mt)

                for w in (card, txt_frame, ln, lt, ld, dot): w.bind("<Button-1>", on_click)
                self._messenger_cards[mid] = (card, txt_frame, ln, lt, ld, dot)
            else:
                card, txt, ln, lt, ld, dot = self._messenger_cards[mid]
                card.grid(row=i, column=0, pady=4, padx=8, sticky="ew")
                card.configure(fg_color=bg_color_card, border_width=border_width, border_color=border_color)
                txt.configure(fg_color=bg_color_card)
                ln.configure(text=f"👤 {m['nombre']}", fg_color=bg_color_card, font=ctk.CTkFont(size=18, weight="bold" if is_sel else "normal"))
                lt.configure(text=f"📞 {m['telefono']}", fg_color=bg_color_card)
                descanso_txt = m.get('dias_descanso', '').strip()
                ld.configure(text=f"💤 Descansa: {descanso_txt}" if descanso_txt else "💤 Sin asignar", fg_color=bg_color_card)
                dot.configure(fg_color=color_status)



    def _seleccionar_mensajero(self, id_: int, nombre: str, telefono: str):
        # Guardar base actual del mensajero previo antes de cambiar
        if self.mensajero_seleccionado and hasattr(self, 'entry_base'):
            base_cruda = self.entry_base.get().replace("$", "").replace(".", "").replace(",", "").strip()
            val_to_save = base_cruda if base_cruda else "0"
            self.bases_mensajeros[self.mensajero_seleccionado["id"]] = val_to_save
            try: db.actualizar_base_mensajero(self.mensajero_seleccionado["id"], float(val_to_save))
            except Exception: pass

        self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
        self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        self.focus()

        # Solo recargamos todo si el buscador tenía texto (porque la lista estaba filtrada)
        busqueda_previa = self.entry_buscar.get().strip()
        if busqueda_previa:
            self.entry_buscar.delete(0, "end")
            self._cargar_mensajeros() # Esto restaura la lista completa
        else:
            # Si no hay búsqueda, hacemos una actualización suave de colores sin pestañear
            cola = db.obtener_cola_turnos()
            ids_en_cola = [t["mensajero_id"] for t in cola]
            for mid, (card, txt, ln, lt, ld, dot) in self._messenger_cards.items():
                is_sel_card = (mid == id_)
                es_primero_en_cola = (len(ids_en_cola) > 0 and mid == ids_en_cola[0])
                if es_primero_en_cola:
                    bg = "#ebf9f1"
                    bw = 2
                    bc = COLORS["success"]
                else:
                    bg = COLORS["highlight"] if is_sel_card else COLORS["bg_card"]
                    bw = 1 if is_sel_card else 0
                    bc = COLORS["accent"] if is_sel_card else bg
                card.configure(fg_color=bg, border_width=bw, border_color=bc)
                txt.configure(fg_color=bg)
                ln.configure(fg_color=bg, font=ctk.CTkFont(size=18, weight="bold" if is_sel_card else "normal"))
                lt.configure(fg_color=bg)
                ld.configure(fg_color=bg)

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

    def _procesar_form_mensajero(self, nombre, telefono, identificativo, estado_trabajo, dias_descanso, id_=None):
        if id_ and self.mensajero_seleccionado:
            db.actualizar_mensajero(id_, nombre, telefono, identificativo, estado_trabajo, dias_descanso)
            self.mensajero_seleccionado = {"id": id_, "nombre": nombre, "telefono": telefono}
            self.lbl_mensajero_sel.configure(text=f"👤  {nombre}  —  📞 {telefono}")
        else:
            db.crear_mensajero(nombre, telefono, identificativo, estado_trabajo, dias_descanso)
        self._cargar_mensajeros()
        
    def _cargar_cola(self):
        cola = db.obtener_cola_turnos()
        ids_nuevos = [t["mensajero_id"] for t in cola]
        ids_actuales = list(self._cola_cards.keys())

        for mid in ids_actuales:
            if mid not in ids_nuevos:
                widgets = self._cola_cards.pop(mid)
                widgets[0].destroy()

        if not cola:
            for w in self.scroll_cola.winfo_children(): w.destroy()
            self._cola_cards.clear()
            ctk.CTkLabel(self.scroll_cola, text="No hay nadie en turno", font=ctk.CTkFont(size=12, slant="italic"), text_color=COLORS["text_muted"]).grid(row=0, column=0, pady=20, sticky="ew")
            self.scroll_cola.grid_columnconfigure(0, weight=1)
            return

        for w in self.scroll_cola.winfo_children():
            if isinstance(w, ctk.CTkLabel) and "No hay" in w.cget("text"): w.destroy()

        self.scroll_cola.grid_columnconfigure(0, weight=1)
        for i, t in enumerate(cola):
            mid = t["mensajero_id"]
            is_first = (i == 0)
            bg_color = "#ebf9f1" if is_first else COLORS["bg_input"]

            if mid not in self._cola_cards:
                card_kwargs = {"master": self.scroll_cola, "fg_color": bg_color, "corner_radius": 8, "height": 50}
                if is_first:
                    card_kwargs["border_width"] = 2
                    card_kwargs["border_color"] = COLORS["success"]
                card = ctk.CTkFrame(**card_kwargs)
                card.grid(row=i, column=0, pady=3, padx=2, sticky="ew")
                card.grid_propagate(False)

                pos_lbl = ctk.CTkLabel(card, text=str(i + 1), font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["success"] if is_first else COLORS["text_muted"], width=30)
                pos_lbl.pack(side="left", padx=(5, 2))

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

                lbl_n = ctk.CTkLabel(info_frame, text=t["nombre"], font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"], anchor="w")
                lbl_n.pack(fill="x")

                lbl_f = ctk.CTkLabel(info_frame, text=f"Llegó: {t['fecha_entrada'].split(' ')[1]}", font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"], anchor="w")
                lbl_f.pack(fill="x")

                btns_frame = ctk.CTkFrame(card, fg_color="transparent")
                btns_frame.pack(side="right", padx=5)

                ctk.CTkButton(btns_frame, text="❌", width=25, height=25, fg_color="#e74c3c", hover_color="#c0392b", command=lambda mid=mid: self._quitar_turno(mid)).pack(side="right")
                self._cola_cards[mid] = (card, pos_lbl, lbl_n, lbl_f)
            else:
                card, pos_lbl, lbl_n, lbl_f = self._cola_cards[mid]
                card.grid(row=i, column=0, pady=3, padx=2, sticky="ew")
                card.configure(fg_color=bg_color)
                if is_first:
                    card.configure(border_width=2, border_color=COLORS["success"])
                else:
                    card.configure(border_width=0)
                pos_lbl.configure(text=str(i + 1), text_color=COLORS["success"] if is_first else COLORS["text_muted"])
                lbl_n.configure(text=t["nombre"], text_color=COLORS["text"])
                lbl_f.configure(text=f"Llegó: {t['fecha_entrada'].split(' ')[1]}", text_color=COLORS["text_muted"])

    def _procesar_id_turno(self, event=None):
        id_input = self.entry_turno_id.get().strip()
        if not id_input: return
        self.entry_turno_id.delete(0, "end")
        
        try:
            identificativo = int(id_input)
        except ValueError:
            CTkMessagebox(title="Error", message="Identificativo inválido.", icon="cancel")
            return
            
        mensajeros = db.obtener_mensajeros()
        mensajero = next((m for m in mensajeros if m.get("identificativo") == identificativo), None)
        
        if not mensajero:
            CTkMessagebox(title="Error", message="Mensajero no encontrado.", icon="cancel")
            return
            
        estado = (mensajero.get("estado_trabajo") or "trabajando").lower()
        if estado == "descanso":
            CTkMessagebox(title="Aviso", message=f"El mensajero {mensajero['nombre']} está en descanso.", icon="warning")
            return
            
        # Comprobar si ya está en cola
        cola = db.obtener_cola_turnos()
        if any(t["mensajero_id"] == mensajero["id"] for t in cola):
            CTkMessagebox(title="Aviso", message="El mensajero ya está en la cola.", icon="info")
            return
            
        db.registrar_en_turno(mensajero["id"])
        self._cargar_cola()
        self._cargar_mensajeros()

    def _quitar_turno(self, mid):
        db.quitar_de_turno(mid)
        self._cargar_cola()
        self._cargar_mensajeros()

    def _limpiar_turnero(self):
        msg = CTkMessagebox(
            title="Confirmar",
            message="¿Vaciar toda la cola de turnos?",
            icon="question", option_1="No", option_2="Sí"
        )
        if msg.get() == "Sí":
            db.limpiar_turnero()
            self._cargar_cola()
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

        cliente_nombre = ""
        descripcion = ""

        db.crear_servicio(self.mensajero_seleccionado["id"], valor, descripcion, cliente_nombre=cliente_nombre)
        

        # Permitir asignar servicios aunque la cola esté vacía
        siguiente = db.obtener_siguiente_en_turno()
        if siguiente and siguiente["mensajero_id"] == self.mensajero_seleccionado["id"]:
            db.quitar_de_turno(self.mensajero_seleccionado["id"])

            # Actualizar la ventana de turnero si está abierta
            if hasattr(self.app, 'v_turnero') and self.app.v_turnero and self.app.v_turnero.winfo_exists():
                self.app.v_turnero.tab_turnero.reload_data()

            # Auto-seleccionar al siguiente en turno para el próximo servicio
            self.after(500, self._seleccionar_siguiente_en_turno)

        # Limpiar entradas
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
                s.get("cliente_nombre") or "",
                fmt_moneda(s["valor"]),
                s.get("descripcion") or "",
                s["fecha"]
            ), tags=tags)

    def _limpiar_tabla_servicios(self):
        for item in self.tree_servicios.get_children():
            self.tree_servicios.delete(item)

    def _eliminar_servicio(self):
        seleccion = self.tree_servicios.selection()
        if not seleccion:
            CTkMessagebox(title="⚠️ Sin selección", message="Selecciona uno o más servicios de la tabla.",
                          icon="warning", option_1="OK")
            return
        
        num_sel = len(seleccion)
        if num_sel == 1:
            id_servicio = int(seleccion[0])
            valores = self.tree_servicios.item(seleccion[0], "values")
            mensaje = f"¿Eliminar el servicio #{id_servicio} con valor {valores[1]}?"
        else:
            mensaje = f"¿Deseas eliminar los {num_sel} servicios seleccionados de forma masiva?"
            
        msg = CTkMessagebox(
            title="🗑️ Confirmar eliminación",
            message=mensaje,
            icon="question", option_1="Cancelar", option_2="Eliminar"
        )
        if msg.get() == "Eliminar":
            try:
                for item_id in seleccion:
                    id_serv = int(item_id)
                    db.eliminar_servicio(id_serv)
                
                self._cargar_servicios_pendientes()
                # Actualizar estatus visual del mensajero
                if self.mensajero_seleccionado:
                    self._actualizar_status_visual_mensajero(self.mensajero_seleccionado["id"])
            except Exception as e:
                CTkMessagebox(title="Error", message=f"No se pudo eliminar: {str(e)}", icon="cancel")
                CTkMessagebox(title="Error", message=f"No se pudo eliminar el servicio: {e}", icon="cancel")

    def _on_doble_clic_servicio(self, event):
        self._cerrar_edicion_inline()
        region = self.tree_servicios.identify("region", event.x, event.y)
        if region != "cell": return
        columna = self.tree_servicios.identify_column(event.x)
        item = self.tree_servicios.identify_row(event.y)
        if not item: return
        
        # Columnas editables: Cliente (#2), Valor (#3), Descripción (#4)
        if columna not in ("#2", "#3", "#4"): return

        valores = self.tree_servicios.item(item, "values")
        bbox = self.tree_servicios.bbox(item, columna)
        if not bbox: return

        if columna == "#2":
            valor_actual = valores[1] # Cliente
            justify = "left"
        elif columna == "#3":
            valor_actual = valores[2].replace("$", "").replace(".", "") # Valor
            justify = "center"
        else:
            valor_actual = valores[3] # Descripción
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

        if columna == "#2":
            entry.bind("<KeyRelease>", lambda e: self._autocomplete_key_release(e, entry))

    def _confirmar_edicion_inline(self, event=None):
        if not self._edit_widget: return

        item = self.tree_servicios.item(self._edit_item)
        valores = item["values"]
        
        id_serv = self._edit_id
        
        # Obtener valores actuales del tree para lo que no se está editando
        # valores index: 0:id, 1:cliente, 2:valor, 3:desc, 4:fecha
        cliente = valores[1]
        try:
            valor = float(valores[2].replace("$", "").replace(".", ""))
        except:
            valor = 5000
        descripcion = valores[3]

        nuevo_input = self._edit_widget.get().strip()

        if self._edit_col == "#2": # Cliente
            cliente = nuevo_input
        elif self._edit_col == "#3": # Valor
            try:
                valor = float(nuevo_input.replace(".", "").replace(",", ""))
            except ValueError:
                CTkMessagebox(title="⚠️ Error", message="Valor numérico inválido.", icon="warning")
                self._cerrar_edicion_inline()
                return
        elif self._edit_col == "#4": # Descripción
            descripcion = nuevo_input

        db.actualizar_servicio_completo(id_serv, valor, descripcion, cliente_nombre=cliente)
        
        self._cerrar_edicion_inline()
        self._cargar_servicios_pendientes()
        
        if hasattr(self.app, 'refresh_clientes'):
            self.app.refresh_clientes()

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

        subtotal = sum(s["valor"] for s in pendientes)
        comision = subtotal * 0.20
        # Aseo: 1000 por cada día único (YYYY-MM-DD)
        dias_unicos = set(s["fecha"].split(" ")[0] for s in pendientes)
        aseo = len(dias_unicos) * 1000
        ganancia_neta = subtotal - comision - aseo

        datos_liquidacion = {
            "mensajero": self.mensajero_seleccionado['nombre'],
            "cant_servicios": len(pendientes),
            "subtotal": subtotal,
            "comision": comision,
            "base": val_base,
            "pago_final": ganancia_neta,
            "descuento_aseo": aseo
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
                
            DialogoExito(
                self.app,
                titulo="✅ Liquidación exitosa",
                mensaje="La liquidación se ha procesado correctamente.",
                boton="Excelente"
            )

        VentanaResumen(self.app, datos_liquidacion, confirmar_final)

    # ── Autocomplete Logic ─────────────────────────────────────────────

    def _show_suggestions(self, entry):
        """Muestra lista desplegable para la edición inline en la tabla."""
        texto = entry.get().strip()
        if not texto:
            self._cerrar_sugerencias()
            return

        sugerencias = db.sugerir_clientes(texto)
        if not sugerencias:
            self._cerrar_sugerencias()
            return

        if not self._top_sugerencias or not self._top_sugerencias.winfo_exists():
            self._top_sugerencias = tk.Toplevel(self)
            self._top_sugerencias.wm_overrideredirect(True)
            self._top_sugerencias.configure(bg=COLORS["bg_card"])
            
            self._lista_sugerencias = tk.Listbox(
                self._top_sugerencias,
                bg=COLORS["bg_card"],
                fg=COLORS["text"],
                font=("Arial", 11),
                borderwidth=1,
                highlightthickness=0,
                selectbackground=COLORS["accent"],
                selectforeground="white"
            )
            self._lista_sugerencias.pack(fill="both", expand=True)
            self._lista_sugerencias.bind("<<ListboxSelect>>", lambda e: self._seleccionar_sugerencia(entry))
            self._top_sugerencias.bind("<FocusOut>", lambda e: self._cerrar_sugerencias())

        self._lista_sugerencias.delete(0, tk.END)
        for s in sugerencias:
            self._lista_sugerencias.insert(tk.END, s)

        self.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        w = entry.winfo_width()
        h = min(len(sugerencias) * 25, 150)
        self._top_sugerencias.wm_geometry(f"{w}x{h}+{x}+{y}")
        self._top_sugerencias.lift()

    def _seleccionar_sugerencia(self, entry):
        if not self._lista_sugerencias: return
        sel = self._lista_sugerencias.curselection()
        if sel:
            nombre = self._lista_sugerencias.get(sel[0])
            if entry.winfo_exists():
                entry.delete(0, tk.END)
                entry.insert(0, nombre)
                # Al seleccionar sugerencia, guardamos de una vez
                self._confirmar_edicion_inline()
            self._cerrar_sugerencias()

    def _cerrar_sugerencias(self):
        if self._top_sugerencias and self._top_sugerencias.winfo_exists():
            self._top_sugerencias.destroy()
        self._top_sugerencias = None
        self._lista_sugerencias = None

    def _autocomplete_key_release(self, event, entry):
        """Controlador para la edición inline (usa lista desplegable)."""
        if event.keysym in ("Return", "Escape", "Up", "Down"):
            return
        self._show_suggestions(entry)

    def _actualizar_status_visual_mensajero(self, id_mensajero: int):
        """Actualiza el color del círculo de estatus sin recargar toda la lista."""
        if id_mensajero not in self._messenger_cards: return
        
        # Consultar solo los pendientes de este mensajero
        pendientes = db.obtener_servicios_pendientes(id_mensajero)
        tiene_trabajo = len(pendientes) > 0
        color = COLORS["success"] if tiene_trabajo else COLORS["danger"]
        
        # Actualizar el widget
        dot = self._messenger_cards[id_mensajero][5]
        dot.configure(fg_color=color)

    def _on_inline_focus_out(self, event):
        # Delay para permitir selección en la lista de sugerencias antes de guardar
        self.after(200, self._confirmar_edicion_inline)

    def _exportar_respaldo_pendientes(self):
        """Exporta todos los servicios pendientes a Excel como respaldo de seguridad."""
        try:
            ruta = exportar_servicios_pendientes()
            # Abrir el archivo automáticamente
            import subprocess, sys
            if sys.platform == "win32":
                subprocess.Popen(["start", "", ruta], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])

            DialogoExito(
                self.app,
                titulo="💾 Respaldo guardado",
                mensaje=f"Servicios pendientes exportados correctamente.\n\n📂 Guardado en el Escritorio como:\n{os.path.basename(ruta)}",
                boton="Perfecto"
            )
        except Exception as e:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(
                master=self.app,
                title="❌ Error al exportar",
                message=f"No se pudo generar el respaldo:\n{e}",
                icon="cancel", option_1="OK"
            )

    def _seleccionar_siguiente_en_turno(self):
        siguiente = db.obtener_siguiente_en_turno()
        if siguiente:
            self._seleccionar_mensajero(siguiente["mensajero_id"], siguiente["nombre"], siguiente["telefono"])
        else:
            CTkMessagebox(title="Turnero Vacío", message="No hay mensajeros registrados en la cola de turnos.", icon="info")
