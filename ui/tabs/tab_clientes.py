import customtkinter as ctk
from tkinter import ttk
from core.config import COLORS
from database import database as db
from ui.modals import FormularioCliente
from CTkMessagebox import CTkMessagebox

class TabClientes(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()
        self.reload_data()
        self.pack(fill="both", expand=True)

    def _build_ui(self):
        # Header y Buscador
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        header.pack(fill="x", padx=0, pady=(0, 15))

        ctk.CTkLabel(
            header, text="👥 Gestión de Clientes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=20, pady=15)

        # Buscador
        search_frame = ctk.CTkFrame(header, fg_color=COLORS["bg_input"], corner_radius=8, width=250, height=35)
        search_frame.pack(side="left", padx=10, pady=15)
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=8)
        self.entry_buscar = ctk.CTkEntry(
            search_frame, placeholder_text="Buscar cliente...",
            fg_color="transparent", border_width=0, text_color=COLORS["text"]
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.reload_data())

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
        acciones_frame = ctk.CTkFrame(self.tabla_frame, fg_color="transparent", height=40)
        acciones_frame.pack(fill="x", side="bottom", padx=10, pady=10)

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

        # Treeview para Clientes
        style = ttk.Style()
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

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar
        sb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def reload_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        busqueda = self.entry_buscar.get().strip()
        clientes = db.obtener_clientes(busqueda)
        
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

    def _abrir_formulario_nuevo(self):
        FormularioCliente(self.winfo_toplevel(), self._procesar_formulario)

    def _abrir_formulario_editar(self):
        sel = self.tree.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecciona un cliente de la lista.", icon="warning")
            return
        
        id_cliente = int(sel[0])
        # Obtener datos actuales (podríamos traerlo del tree o volver a consultar)
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
