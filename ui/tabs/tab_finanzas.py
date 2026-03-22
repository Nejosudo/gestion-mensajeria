import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime
from core.config import COLORS, fmt_moneda
from database import database as db
from CTkMessagebox import CTkMessagebox

class TabFinanzas(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)

        self._build_ui()
        self.reload_data()

    def _build_ui(self):
        # --- Filtros ---
        filtros_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        filtros_frame.pack(fill="x", padx=0, pady=(0, 15))

        ctk.CTkLabel(
            filtros_frame, text="🕒 Período:",
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
                command=self.reload_data
            ).pack(side="left", padx=10, pady=12)

        # --- Dashboard ---
        dash_frame = ctk.CTkFrame(self, fg_color="transparent")
        dash_frame.pack(fill="x", pady=(0, 15))
        
        self.card_ingresos = self._crear_card(dash_frame, "Total Ingresos", "$0", COLORS["success"])
        self.card_ingresos.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.card_gastos = self._crear_card(dash_frame, "Total Gastos", "$0", COLORS["danger"])
        self.card_gastos.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_balance = self._crear_card(dash_frame, "Balance Neto", "$0", COLORS["accent"])
        self.card_balance.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # --- Tablas ---
        tablas_contenedor = ctk.CTkFrame(self, fg_color="transparent")
        tablas_contenedor.pack(fill="both", expand=True)
        tablas_contenedor.grid_columnconfigure(0, weight=1)
        tablas_contenedor.grid_columnconfigure(1, weight=1)
        tablas_contenedor.grid_rowconfigure(0, weight=1)

        # Columna Ingresos (Liquidaciones)
        f_ingresos = ctk.CTkFrame(tablas_contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        f_ingresos.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        ctk.CTkLabel(f_ingresos, text="📈 Detalle de Ingresos (Comisiones + Aseo)", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent"]).pack(pady=10)
        
        self.tree_ingresos = self._crear_tabla(f_ingresos, ("id", "fecha", "comision", "aseo", "total"))
        self.tree_ingresos.heading("id", text="ID")
        self.tree_ingresos.heading("fecha", text="Fecha")
        self.tree_ingresos.heading("comision", text="Comisión")
        self.tree_ingresos.heading("aseo", text="Aseo")
        self.tree_ingresos.heading("total", text="Total")
        
        for col, width in zip(("id", "fecha", "comision", "aseo", "total"), (40, 140, 90, 80, 100)):
            self.tree_ingresos.column(col, width=width, anchor="center")

        # Columna Gastos
        f_gastos = ctk.CTkFrame(tablas_contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        f_gastos.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        header_gastos = ctk.CTkFrame(f_gastos, fg_color="transparent")
        header_gastos.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(header_gastos, text="📉 Detalle de Gastos", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["danger"]).pack(side="left")
        
        ctk.CTkButton(header_gastos, text="➕ Agregar Gasto", width=120, height=28,
                     fg_color=COLORS["danger"], hover_color="#c0392b",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     command=self._abrir_modal_gasto).pack(side="right")

        self.tree_gastos = self._crear_tabla(f_gastos, ("id", "fecha", "descripcion", "monto"))
        self.tree_gastos.heading("id", text="ID")
        self.tree_gastos.heading("fecha", text="Fecha")
        self.tree_gastos.heading("descripcion", text="Descripción")
        self.tree_gastos.heading("monto", text="Monto")
        
        for col, width in zip(("id", "fecha", "descripcion", "monto"), (40, 140, 180, 100)):
            self.tree_gastos.column(col, width=width, anchor="center")
            
        # Botón eliminar gasto
        ctk.CTkButton(f_gastos, text="🗑️ Eliminar Gasto Seleccionado", height=32,
                     fg_color="transparent", border_width=1, border_color=COLORS["danger"],
                     text_color=COLORS["danger"], font=ctk.CTkFont(size=12),
                     command=self._confirmar_eliminar_gasto).pack(pady=10)

    def _crear_card(self, parent, titulo, valor, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12, height=100)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(pady=(15, 0))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
        lbl_valor.pack(pady=(5, 15))
        card.lbl_valor = lbl_valor
        return card

    def _crear_tabla(self, parent, columnas):
        tabla_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tabla_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", style="Dark.Treeview")
        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("par", background=COLORS["table_row_2"])
        return tree

    def reload_data(self):
        filtro = self.filtro_var.get()
        
        # Cargar Ingresos (Liquidaciones)
        for item in self.tree_ingresos.get_children():
            self.tree_ingresos.delete(item)
        
        liquidaciones = db.obtener_liquidaciones(filtro)
        total_ingresos = 0
        for i, liq in enumerate(liquidaciones):
            comision = liq["comision_empresa"]
            aseo = liq["descuento_aseo"]
            total_fila = comision + aseo
            total_ingresos += total_fila
            tags = ("par",) if i % 2 == 1 else ()
            self.tree_ingresos.insert("", "end", values=(
                liq["id"], liq["fecha"], fmt_moneda(comision), fmt_moneda(aseo), fmt_moneda(total_fila)
            ), tags=tags)
        
        # Cargar Gastos
        for item in self.tree_gastos.get_children():
            self.tree_gastos.delete(item)
            
        gastos = db.obtener_gastos(filtro)
        total_gastos = 0
        for i, g in enumerate(gastos):
            total_gastos += g["monto"]
            tags = ("par",) if i % 2 == 1 else ()
            self.tree_gastos.insert("", "end", values=(
                g["id"], g["fecha"], g["descripcion"], fmt_moneda(g["monto"])
            ), tags=tags)
            
        # Actualizar Dashboard
        self.card_ingresos.lbl_valor.configure(text=fmt_moneda(total_ingresos))
        self.card_gastos.lbl_valor.configure(text=fmt_moneda(total_gastos))
        self.card_balance.lbl_valor.configure(text=fmt_moneda(total_ingresos - total_gastos))

    def _abrir_modal_gasto(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Registrar Nuevo Gasto")
        modal.geometry("350x250")
        modal.configure(fg_color=COLORS["bg_card"])
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        # Centrar
        modal.update_idletasks()
        root = self.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() // 2) - (350 // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (250 // 2)
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text="Descripción del Gasto:", font=ctk.CTkFont(size=13)).pack(pady=(20, 5))
        entry_desc = ctk.CTkEntry(modal, width=250, placeholder_text="Ej: Combustible, Papelería...")
        entry_desc.pack(pady=5)
        
        ctk.CTkLabel(modal, text="Monto ($):", font=ctk.CTkFont(size=13)).pack(pady=(10, 5))
        entry_monto = ctk.CTkEntry(modal, width=250, placeholder_text="0")
        entry_monto.pack(pady=5)

        def guardar():
            desc = entry_desc.get().strip()
            try:
                monto = float(entry_monto.get().replace(".", "").replace(",", ""))
                if not desc: throw
            except:
                CTkMessagebox(title="Error", message="Ingresa una descripción y un monto válido.", icon="cancel")
                return
            
            db.crear_gasto(desc, monto)
            modal.destroy()
            self.reload_data()

        ctk.CTkButton(modal, text="💾 Guardar Gasto", fg_color=COLORS["success"], command=guardar).pack(pady=20)

    def _confirmar_eliminar_gasto(self):
        seleccion = self.tree_gastos.selection()
        if not seleccion:
            CTkMessagebox(title="Aviso", message="Selecciona un gasto de la lista.", icon="warning")
            return
        
        item = self.tree_gastos.item(seleccion[0])
        id_gasto = item["values"][0]
        
        msg = CTkMessagebox(title="Confirmar", message=f"¿Eliminar el gasto #{id_gasto}?", 
                           icon="question", option_1="Cancelar", option_2="Eliminar")
        
        if msg.get() == "Eliminar":
            db.eliminar_gasto(id_gasto)
            self.reload_data()
