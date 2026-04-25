import customtkinter as ctk
from tkinter import ttk
from core.config import COLORS, CTkToolTip
from database import database as db
from ui.modals import FormularioCliente
from CTkMessagebox import CTkMessagebox
from tkcalendar import DateEntry
import tkinter as tk

class TabClientes(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()
        self.reload_data()
        self.pack(fill="both", expand=True)

    def _build_ui(self):
        # Header y Filtros
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        header.pack(fill="x", padx=0, pady=(0, 15))

        # --- Título y Buscador ---
        left_header = ctk.CTkFrame(header, fg_color="transparent")
        left_header.pack(side="left", fill="y", padx=10)

        ctk.CTkLabel(
            left_header, text="👥 Gestión de Clientes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=10, pady=15)

        # Buscador
        search_frame = ctk.CTkFrame(left_header, fg_color=COLORS["bg_input"], corner_radius=8, width=220, height=35)
        search_frame.pack(side="left", padx=10, pady=15)
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=8)
        self.entry_buscar = ctk.CTkEntry(
            search_frame, placeholder_text="Buscar cliente...",
            fg_color="transparent", border_width=0, text_color=COLORS["text"]
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.reload_data())

        # --- Filtros de Periodo ---
        filtros_frame = ctk.CTkFrame(header, fg_color="transparent")
        filtros_frame.pack(side="left", padx=10, pady=15)

        self.filtro_var = ctk.StringVar(value="todo")
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
            rb.pack(side="left", padx=2)
            CTkToolTip(rb, desc)

        # Filtro por calendario
        self.rb_fecha = ctk.CTkRadioButton(
            filtros_frame, text="📆", variable=self.filtro_var, value="fecha",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"], text_color=COLORS["text"],
            font=ctk.CTkFont(size=14, weight="bold"), width=40,
            command=self._on_filter_changed
        )
        self.rb_fecha.pack(side="left", padx=(10, 5))
        CTkToolTip(self.rb_fecha, "Filtrar por Rango de Fechas")

        # Contenedor de calendarios (OCULTO POR DEFECTO)
        self.cal_container = ctk.CTkFrame(header, fg_color="transparent")
        
        self.frame_desde = ctk.CTkFrame(self.cal_container, fg_color=COLORS["bg_input"], border_color=COLORS["border"], border_width=1, corner_radius=8, height=30)
        self.frame_desde.pack(side="left", padx=2)
        self.frame_desde.pack_propagate(False)

        self.cal_desde = DateEntry(
            self.frame_desde, width=10, background=COLORS["accent"],
            foreground=COLORS["text"], borderwidth=0, date_pattern='yyyy-mm-dd',
            locale='es_ES', font=("Arial", 9),
            headersbackground=COLORS["accent"], headersforeground='white',
            selectbackground=COLORS["accent"], selectforeground='white',
            relief="flat"
        )
        self.cal_desde.pack(padx=5, pady=0, fill="both", expand=True)
        
        self.frame_hasta = ctk.CTkFrame(self.cal_container, fg_color=COLORS["bg_input"], border_color=COLORS["border"], border_width=1, corner_radius=8, height=30)
        self.frame_hasta.pack(side="left", padx=2)
        self.frame_hasta.pack_propagate(False)

        self.cal_hasta = DateEntry(
            self.frame_hasta, width=10, background=COLORS["accent"],
            foreground=COLORS["text"], borderwidth=0, date_pattern='yyyy-mm-dd',
            locale='es_ES', font=("Arial", 9),
            headersbackground=COLORS["accent"], headersforeground='white',
            selectbackground=COLORS["accent"], selectforeground='white',
            relief="flat"
        )
        self.cal_hasta.pack(padx=5, pady=0, fill="both", expand=True)
        
        self.cal_desde.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())
        self.cal_hasta.bind("<<DateEntrySelected>>", lambda e: self._on_date_changed())

        # Botón Nuevo Cliente
        ctk.CTkButton(
            header, text="➕ Nuevo Cliente", 
            fg_color=COLORS["success"], hover_color="#219150",
            font=ctk.CTkFont(weight="bold"),
            command=self._abrir_formulario_nuevo
        ).pack(side="right", padx=20, pady=15)

        # Contenedor Tabla
        self.tabla_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        self.tabla_frame.pack(fill="both", expand=True)

        # Acciones rápidas (Editar/Eliminar)
        acciones_frame = ctk.CTkFrame(self.tabla_frame, fg_color="transparent", height=45)
        acciones_frame.pack(fill="x", side="bottom", padx=10, pady=5)

        self.btn_edit = ctk.CTkButton(
            acciones_frame, text="✏️ Editar", width=100,
            fg_color=COLORS["warning"], text_color="white",
            command=self._abrir_formulario_editar
        )
        self.btn_edit.pack(side="left", padx=5)

        self.btn_delete = ctk.CTkButton(
            acciones_frame, text="🗑️ Eliminar", width=100,
            fg_color=COLORS["danger"], text_color="white",
            command=self._eliminar_cliente
        )
        self.btn_delete.pack(side="left", padx=5)

        # Label Total Servicios (Bottom Right)
        self.lbl_total_general = ctk.CTkLabel(
            acciones_frame, text="Total servicios: 0",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#000000" # Black light? I'll use black for now.
        )
        self.lbl_total_general.pack(side="right", padx=20)

        # Treeview para Clientes
        self.tree = ttk.Treeview(
            self.tabla_frame,
            columns=("id", "nombre", "direccion", "telefono", "servicios", "ultima_vez"),
            show="headings",
            style="Dark.Treeview"
        )
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre / Empresa")
        self.tree.heading("direccion", text="Dirección")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("servicios", text="Servicios")
        self.tree.heading("ultima_vez", text="Último pedido")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nombre", width=180, anchor="center")
        self.tree.column("direccion", width=220, anchor="center")
        self.tree.column("telefono", width=130, anchor="center")
        self.tree.column("servicios", width=120, anchor="center")
        self.tree.column("ultima_vez", width=180, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        
        # Scrollbar
        sb = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.place(relx=1.0, rely=0, relheight=1, anchor='ne', x=-10, y=10) # Adjusted position

    def reload_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        busqueda = self.entry_buscar.get().strip()
        
        # Obtener el filtro de fecha
        filtro = self.filtro_var.get()
        if filtro == "fecha":
            f_inicio = self.cal_desde.get_date().strftime("%Y-%m-%d")
            f_fin = self.cal_hasta.get_date().strftime("%Y-%m-%d")
            filtro = f"{f_inicio}..{f_fin}"
            
        clientes = db.obtener_clientes(busqueda, filtro=filtro)
        
        for c in clientes:
            ultima = c.get("ultima_fecha", "Nunca")
            if ultima is None: ultima = "Nunca"
            
            self.tree.insert("", "end", iid=str(c["id"]), values=(
                c["id"],
                c["nombre"],
                c.get("direccion", ""),
                c.get("telefono", ""),
                c.get("total_servicios", 0),
                ultima
            ))
        
        self._on_selection_changed()

    def _on_filter_changed(self):
        self._actualizar_estado_calendarios()
        self.reload_data()

    def _on_date_changed(self):
        self.filtro_var.set("fecha")
        self.reload_data()

    def _actualizar_estado_calendarios(self):
        es_fecha = self.filtro_var.get() == "fecha"
        if es_fecha:
            self.cal_container.pack(side="left", padx=5)
        else:
            self.cal_container.pack_forget()

    def _on_selection_changed(self, event=None):
        seleccion = self.tree.selection()
        total = 0
        if not seleccion:
            # Si no hay nada seleccionado, podríamos mostrar el total de lo que hay en la lista?
            # El usuario dice "al seleccionar clientes".
            pass
        else:
            for item in seleccion:
                valores = self.tree.item(item, "values")
                try:
                    total += int(valores[4]) # Columna de servicios
                except:
                    pass
        
        self.lbl_total_general.configure(text=f"Total servicios: {total}")

    def _abrir_formulario_nuevo(self):
        FormularioCliente(self.winfo_toplevel(), self._procesar_formulario)

    def _abrir_formulario_editar(self):
        sel = self.tree.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecciona un cliente de la lista.", icon="warning")
            return
        
        id_cliente = int(sel[0])
        # Obtener datos actuales
        vals = self.tree.item(sel[0], "values")
        cliente_data = {
            "id": id_cliente,
            "nombre": vals[1],
            "direccion": vals[2],
            "telefono": vals[3]
        }
        FormularioCliente(self.winfo_toplevel(), self._procesar_formulario, cliente_data)

    def _procesar_formulario(self, nombre, direccion, telefono, id_=None):
        if id_:
            db.actualizar_cliente(id_, nombre, direccion, telefono)
        else:
            db.crear_cliente(nombre, direccion, telefono)
        self.reload_data()

    def _eliminar_cliente(self):
        sel = self.tree.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecciona un cliente para eliminar.", icon="warning")
            return
        
        nombre = self.tree.item(sel[0], "values")[1]
        if CTkMessagebox(title="Confirmar", message=f"¿Eliminar al cliente {nombre}?", icon="question", option_1="No", option_2="Sí").get() == "Sí":
            db.eliminar_cliente(int(sel[0]))
            self.reload_data()
