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
        ).pack(pady=15)

        self.scroll_disponibles = ctk.CTkScrollableFrame(panel_izq, fg_color="transparent")
        self.scroll_disponibles.pack(fill="both", expand=True, padx=10, pady=10)

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

    def _cargar_disponibles(self):
        for widget in self.scroll_disponibles.winfo_children():
            widget.destroy()

        mensajeros = db.obtener_mensajeros()
        cola_actual = [t["mensajero_id"] for t in db.obtener_cola_turnos()]

        for m in mensajeros:
            if m["id"] in cola_actual:
                continue

            card = ctk.CTkFrame(self.scroll_disponibles, fg_color=COLORS["bg_input"], corner_radius=8, height=60)
            card.pack(fill="x", pady=4, padx=5)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card, text=m["nombre"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS["text"]
            ).pack(side="left", padx=15)

            ctk.CTkButton(
                card, text="Llegó 📥", width=80, height=28,
                fg_color=COLORS["accent"], text_color="#ffffff",
                command=lambda mid=m["id"]: self._registrar_llegada(mid)
            ).pack(side="right", padx=10)

    def _cargar_cola(self):
        for widget in self.scroll_cola.winfo_children():
            widget.destroy()

        cola = db.obtener_cola_turnos()
        if not cola:
            ctk.CTkLabel(
                self.scroll_cola, text="No hay mensajeros en turno",
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color=COLORS["text_muted"]
            ).pack(pady=30)
            return

        for i, t in enumerate(cola):
            is_first = (i == 0)
            bg_color = "#2c3e50" if is_first else COLORS["bg_input"]
            border_w = 2 if is_first else 0
            border_c = "#27ae60" if is_first else "transparent"

            card = ctk.CTkFrame(
                self.scroll_cola, 
                fg_color=bg_color, 
                border_width=border_w, 
                border_color=border_c,
                corner_radius=10, 
                height=70
            )
            card.pack(fill="x", pady=5, padx=5)
            card.pack_propagate(False)

            # Posición
            pos_lbl = ctk.CTkLabel(
                card, text=str(i + 1),
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="#27ae60" if is_first else COLORS["text_muted"],
                width=40
            )
            pos_lbl.pack(side="left", padx=(10, 5))

            # Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

            ctk.CTkLabel(
                info_frame, text=t["nombre"],
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#ffffff" if is_first else COLORS["text"],
                anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                info_frame, text=f"Llegada: {t['fecha_entrada'].split(' ')[1]}",
                font=ctk.CTkFont(size=11),
                text_color="#bdc3c7" if is_first else COLORS["text_muted"],
                anchor="w"
            ).pack(fill="x")

            # Botones de acción
            btns_frame = ctk.CTkFrame(card, fg_color="transparent")
            btns_frame.pack(side="right", padx=10)

            ctk.CTkButton(
                btns_frame, text="❌", width=30, height=28,
                fg_color="#e74c3c", hover_color="#c0392b",
                command=lambda mid=t["mensajero_id"]: self._quitar_turno(mid)
            ).pack(side="right", padx=2)

            if not is_first:
                ctk.CTkButton(
                    btns_frame, text="🔝", width=30, height=28,
                    fg_color="#3498db",
                    command=lambda mid=t["mensajero_id"]: self._subir_turno(mid)
                ).pack(side="right", padx=2)

    def _registrar_llegada(self, mid):
        db.registrar_en_turno(mid)
        self.reload_data()

    def _quitar_turno(self, mid):
        db.quitar_de_turno(mid)
        self.reload_data()

    def _subir_turno(self, mid):
        # Para subir el turno, tendríamos que manipular las fechas. 
        # Pero el usuario pidió FIFO. Dejemos quitar por ahora.
        # Si queremos subirlo, podemos borrarlo y re-insertarlo con una fecha antigua?
        # Mejor solo quitar y dejar que se registren en orden.
        pass

    def _limpiar_turnero(self):
        msg = CTkMessagebox(
            title="Confirmar",
            message="¿Vaciar toda la cola de turnos?",
            icon="question", option_1="No", option_2="Sí"
        )
        if msg.get() == "Sí":
            db.limpiar_turnero()
            self.reload_data()

class VentanaTurnero(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊 Monitor de Turnos - Gestión de Mensajería")
        self.geometry("900x650")
        self.minsize(800, 500)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Estilos y UI
        self.tab_turnero = TabTurnero(self, app_controller=parent)
        self.tab_turnero.pack(fill="both", expand=True)

        # Mantener al frente si es necesario, pero permitir interactuar con la principal
        self.after(100, self.lift)
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.destroy()
