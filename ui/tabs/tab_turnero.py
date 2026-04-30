import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime
from CTkMessagebox import CTkMessagebox
from core.config import COLORS
from database import database as db

class TabTurnero(ctk.CTkFrame):
    def __init__(self, parent, app_controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app_controller
        self.pack(fill="both", expand=True)

        self._disponibles_cards = {} # Trackers para evitar parpadeo
        self._cola_cards = {}

        self._build_ui()
        self.reload_data()

    def _build_ui(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)
        contenedor.grid_columnconfigure(0, weight=1) # Lista Mensajeros
        contenedor.grid_columnconfigure(1, weight=1) # Cola de Turnos
        contenedor.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Disponibles para Turno ---
        panel_izq = ctk.CTkFrame(contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            panel_izq, text="👤 Mensajeros en Base",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(15, 10))

        # Buscador
        search_frame = ctk.CTkFrame(panel_izq, fg_color=COLORS["bg_input"], corner_radius=8, height=35)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=8)
        
        self.entry_buscar = ctk.CTkEntry(
            search_frame, placeholder_text="Buscar mensajero...",
            fg_color="transparent", border_width=0, text_color=COLORS["text"]
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.reload_data())

        self.scroll_disponibles = ctk.CTkScrollableFrame(panel_izq, fg_color="transparent")
        self.scroll_disponibles.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- Panel Derecho: Cola de Turnos ---
        panel_der = ctk.CTkFrame(contenedor, fg_color=COLORS["bg_card"], corner_radius=12)
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        header_der = ctk.CTkFrame(panel_der, fg_color="transparent")
        header_der.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            header_der, text="🔄 Cola de Turnos",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#27ae60"
        ).pack(side="left")

        ctk.CTkButton(
            header_der, text="🧹 Limpiar Todo", width=100, height=28,
            fg_color=COLORS["danger"], text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._limpiar_turnero
        ).pack(side="right")

        self.scroll_cola = ctk.CTkScrollableFrame(panel_der, fg_color="transparent")
        self.scroll_cola.pack(fill="both", expand=True, padx=10, pady=10)

    def reload_data(self):
        self._cargar_disponibles()
        self._cargar_cola()

    def _on_buscar_key_release(self, event=None):
        """Debounce más ágil."""
        if hasattr(self, "_search_job") and self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(100, self._cargar_disponibles)


    def _cargar_disponibles(self):
        busqueda = self.entry_buscar.get().strip()
        mensajeros = db.obtener_mensajeros(busqueda)
        cola = db.obtener_cola_turnos()
        ids_en_cola = [t["mensajero_id"] for t in cola]
        pos_cola = {id_m: i for i, id_m in enumerate(ids_en_cola)}

        # Ordenar mensajeros: primero los que están en la cola (en el mismo orden), luego el resto
        en_cola = [m for m in mensajeros if m["id"] in pos_cola]
        en_cola.sort(key=lambda x: pos_cola[x["id"]])
        fuera_cola = [m for m in mensajeros if m["id"] not in pos_cola]
        lista_final = en_cola + fuera_cola

        ids_nuevos = [m["id"] for m in lista_final]
        ids_actuales = list(self._disponibles_cards.keys())

        for mid in ids_actuales:
            if mid not in ids_nuevos:
                card = self._disponibles_cards.pop(mid)
                card.destroy()

        if not lista_final:
            for w in self.scroll_disponibles.winfo_children(): w.destroy()
            self._disponibles_cards.clear()
            ctk.CTkLabel(self.scroll_disponibles, text="No hay mensajeros", font=ctk.CTkFont(size=11, slant="italic"), text_color=COLORS["text_muted"]).grid(row=0, column=0, pady=20, sticky="ew")
            self.scroll_disponibles.grid_columnconfigure(0, weight=1)
            return

        # Limpiar mensajes
        for w in self.scroll_disponibles.winfo_children():
            if isinstance(w, ctk.CTkLabel) and "No hay" in w.cget("text"): w.destroy()

        # 2. Reordenar o Crear usando GRID
        self.scroll_disponibles.grid_columnconfigure(0, weight=1)
        for i, m in enumerate(lista_final):
            mid = m["id"]
            # Si está en la cola, no mostrar botón para agregar
            show_btn = mid not in ids_en_cola
            # Resaltar igual que en el turnero si es el primero en la cola
            es_primero_en_cola = (len(ids_en_cola) > 0 and mid == ids_en_cola[0])
            bg_color_card = "#ebf9f1" if es_primero_en_cola else COLORS["bg_input"]
            border_width = 2 if es_primero_en_cola else 0
            border_color = COLORS["success"] if es_primero_en_cola else bg_color_card

            if mid not in self._disponibles_cards:
                card = ctk.CTkFrame(self.scroll_disponibles, fg_color=bg_color_card, corner_radius=10, height=70, border_width=border_width, border_color=border_color)
                card.grid(row=i, column=0, pady=4, padx=5, sticky="ew")
                card.grid_propagate(False)

                txt_frame = ctk.CTkFrame(card, fg_color=bg_color_card)
                txt_frame.pack(side="left", fill="both", expand=True, padx=(12, 5), pady=8)

                lbl_n = ctk.CTkLabel(txt_frame, text=f"👤 {m['nombre']}", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"], anchor="w")
                lbl_n.pack(fill="x", side="top")

                lbl_t = ctk.CTkLabel(txt_frame, text=f"📞 {m['telefono']}", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w")
                lbl_t.pack(fill="x", side="top")

                btn_add = None
                if show_btn:
                    btn_add = ctk.CTkButton(card, text="➕", width=40, height=35, fg_color=COLORS["success"], hover_color="#219150", font=ctk.CTkFont(size=18, weight="bold"), command=lambda mid=mid: self._registrar_llegada(mid))
                    btn_add.pack(side="right", padx=10)
                card._btn_add = btn_add
                self._disponibles_cards[mid] = card
            else:
                card = self._disponibles_cards[mid]
                card.grid(row=i, column=0, pady=4, padx=5, sticky="ew")
                card.configure(fg_color=bg_color_card, border_width=border_width, border_color=border_color)
                # Eliminar botón si existe y no debe mostrarse
                if hasattr(card, '_btn_add') and card._btn_add:
                    card._btn_add.destroy()
                    card._btn_add = None
                # Volver a crear el botón si debe mostrarse
                if show_btn and (not hasattr(card, '_btn_add') or card._btn_add is None):
                    btn_add = ctk.CTkButton(card, text="➕", width=40, height=35, fg_color=COLORS["success"], hover_color="#219150", font=ctk.CTkFont(size=18, weight="bold"), command=lambda mid=mid: self._registrar_llegada(mid))
                    btn_add.pack(side="right", padx=10)
                    card._btn_add = btn_add

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
            ctk.CTkLabel(self.scroll_cola, text="No hay nadie en turno", font=ctk.CTkFont(size=13, slant="italic"), text_color=COLORS["text_muted"]).grid(row=0, column=0, pady=30, sticky="ew")
            self.scroll_cola.grid_columnconfigure(0, weight=1)
            return

        # Limpiar mensajes
        for w in self.scroll_cola.winfo_children():
            if isinstance(w, ctk.CTkLabel) and "No hay" in w.cget("text"): w.destroy()

        # 2. Reordenar o Crear usando GRID
        self.scroll_cola.grid_columnconfigure(0, weight=1)
        for i, t in enumerate(cola):
            mid = t["mensajero_id"]
            is_first = (i == 0)
            bg_color = "#ebf9f1" if is_first else COLORS["bg_input"]

            if mid not in self._cola_cards:
                card_kwargs = {"master": self.scroll_cola, "fg_color": bg_color, "corner_radius": 10, "height": 70}
                if is_first:
                    card_kwargs["border_width"] = 2
                    card_kwargs["border_color"] = COLORS["success"]
                card = ctk.CTkFrame(**card_kwargs)
                card.grid(row=i, column=0, pady=5, padx=5, sticky="ew")
                card.grid_propagate(False)

                pos_lbl = ctk.CTkLabel(card, text=str(i + 1), font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["success"] if is_first else COLORS["text_muted"], width=40)
                pos_lbl.pack(side="left", padx=(10, 5))

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                lbl_n = ctk.CTkLabel(info_frame, text=t["nombre"], font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["text"], anchor="w")
                lbl_n.pack(fill="x")

                lbl_f = ctk.CTkLabel(info_frame, text=f"Llegada: {t['fecha_entrada'].split(' ')[1]}", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w")
                lbl_f.pack(fill="x")

                btns_frame = ctk.CTkFrame(card, fg_color="transparent")
                btns_frame.pack(side="right", padx=10)

                ctk.CTkButton(btns_frame, text="❌", width=30, height=28, fg_color="#e74c3c", hover_color="#c0392b", command=lambda mid=mid: self._quitar_turno(mid)).pack(side="right", padx=2)
                self._cola_cards[mid] = (card, pos_lbl, lbl_n, lbl_f)
            else:
                card, pos_lbl, lbl_n, lbl_f = self._cola_cards[mid]
                card.grid(row=i, column=0, pady=5, padx=5, sticky="ew")
                card.configure(fg_color=bg_color)
                if is_first:
                    card.configure(border_width=2, border_color=COLORS["success"])
                else:
                    card.configure(border_width=0)
                pos_lbl.configure(text=str(i + 1), text_color=COLORS["success"] if is_first else COLORS["text_muted"])
                lbl_n.configure(text=t["nombre"], text_color=COLORS["text"])
                lbl_f.configure(text=f"Llegada: {t['fecha_entrada'].split(' ')[1]}", text_color=COLORS["text_muted"])


    def _registrar_llegada(self, mid):
        db.registrar_en_turno(mid)
        self.reload_data()
        if hasattr(self.app, 'refresh_gestion'):
            self.app.refresh_gestion()

    def _quitar_turno(self, mid):
        db.quitar_de_turno(mid)
        self.reload_data()
        if hasattr(self.app, 'refresh_gestion'):
            self.app.refresh_gestion()


    def _limpiar_turnero(self):
        msg = CTkMessagebox(
            title="Confirmar",
            message="¿Vaciar toda la cola de turnos?",
            icon="question", option_1="No", option_2="Sí"
        )
        if msg.get() == "Sí":
            db.limpiar_turnero()
            self.reload_data()
            if hasattr(self.app, 'refresh_gestion'):
                self.app.refresh_gestion()

class VentanaTurnero(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊 Monitor de Turnos - Gestión de Mensajería")
        width, height = 900, 650
        self.geometry(f"{width}x{height}")
        self.minsize(800, 500)
        self.configure(fg_color=COLORS["bg_dark"])

        # Centrar respecto a la ventana principal
        self.update_idletasks()
        p_w, p_h = parent.winfo_width(), parent.winfo_height()
        p_x, p_y = parent.winfo_x(), parent.winfo_y()
        # Si las dimensiones son inválidas, usar centro de pantalla
        if p_w <= 1:
            p_w, p_h = self.winfo_screenwidth(), self.winfo_screenheight()
            p_x, p_y = 0, 0
        x = p_x + (p_w // 2) - (width // 2)
        y = p_y + (p_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Estilos y UI
        self.tab_turnero = TabTurnero(self, app_controller=parent)
        self.tab_turnero.pack(fill="both", expand=True)


        # No usar lift, grab_set ni focus_force para no bloquear la principal ni forzar foco
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.destroy()
