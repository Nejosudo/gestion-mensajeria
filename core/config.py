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
