import customtkinter as ctk

# Colores
COLORS = {
    "bg_dark":      "#f4f7f6",
    "bg_card":      "#ffffff",
    "bg_input":     "#fdfdfd",
    "accent":       "#3a86ff",
    "accent_hover": "#2a6fdf",
    "success":      "#27ae60",
    "danger":       "#e74c3c",
    "warning":      "#f39c12",
    "text":         "#2d3436",
    "text_muted":   "#636e72",
    "border":       "#dfe6e9",
    "table_header": "#f1f2f6",
    "table_row_1":  "#ffffff",
    "table_row_2":  "#f9f9f9",
    "highlight":    "#eef2ff",
}

def fmt_moneda(valor: float) -> str:
    """Formatea un número a moneda COP: $5.000"""
    return f"${valor:,.0f}".replace(",", ".")

class CTkToolTip:
    """Implementación de Tooltip mejorada para evitar que queden huérfanos."""
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.id = None
        
        # Bindings mejorados para asegurar la destrucción del tooltip
        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.on_leave, add="+")
        self.widget.bind("<FocusOut>", self.on_leave, add="+")
        self.widget.bind("<Unmap>", self.on_leave, add="+") # Cuando se oculta el widget (cambio de tab)

    def on_enter(self, event=None):
        self._cancel_scheduled()
        self.id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event=None):
        self._cancel_scheduled()
        self.hide_tooltip()

    def _cancel_scheduled(self):
        if self.id:
            try: self.widget.after_cancel(self.id)
            except: pass
            self.id = None

    def show_tooltip(self):
        if self.tooltip or not self.text: return
        # No mostrar si el widget no es visible o ya no existe
        if not self.widget.winfo_exists() or not self.widget.winfo_viewable(): return
        
        try:
            x = self.widget.winfo_pointerx() + 15
            y = self.widget.winfo_pointery() + 15
            
            self.tooltip = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)
            tw.configure(fg_color="#333333")
            
            label = ctk.CTkLabel(tw, text=self.text, fg_color="#333333", text_color="white", 
                                 corner_radius=6, padx=8, pady=4, font=ctk.CTkFont(size=11))
            label.pack()
        except:
            self.hide_tooltip()

    def hide_tooltip(self):
        if self.tooltip:
            try:
                if self.tooltip.winfo_exists():
                    self.tooltip.destroy()
            except:
                pass
            self.tooltip = None
