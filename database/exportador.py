import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def formatear_moneda(valor: float) -> str:
    """Formatea un número como moneda COP: $5.000"""
    return f"${valor:,.0f}".replace(",", ".")


def exportar_liquidaciones(datos: list[dict], ruta_destino: str | None = None) -> str:
    """
    Genera un archivo .xlsx con las liquidaciones.
    Retorna la ruta del archivo generado.
    """
    if not ruta_destino:
        escritorio = os.path.join(os.path.expanduser("~"), "Escritorio")
        if not os.path.exists(escritorio):
            escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(escritorio):
            escritorio = os.path.expanduser("~")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_destino = os.path.join(escritorio, f"Liquidaciones_{timestamp}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Liquidaciones"

    # ── Estilos ──
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1a1a2e", end_color="1a1a2e", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    cell_font = Font(name="Calibri", size=10)
    money_font = Font(name="Calibri", size=10, color="2ecc71")
    border = Border(
        left=Side(style="thin", color="333333"),
        right=Side(style="thin", color="333333"),
        top=Side(style="thin", color="333333"),
        bottom=Side(style="thin", color="333333"),
    )
    alt_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    # ── Título del reporte ──
    ws.merge_cells("A1:G1")
    titulo_cell = ws["A1"]
    titulo_cell.value = "REPORTE DE LIQUIDACIONES — MENSAJERÍA"
    titulo_cell.font = Font(name="Calibri", bold=True, size=14, color="1a1a2e")
    titulo_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:G2")
    fecha_cell = ws["A2"]
    fecha_cell.value = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    fecha_cell.font = Font(name="Calibri", italic=True, size=9, color="666666")
    fecha_cell.alignment = Alignment(horizontal="center")

    # ── Encabezados ──
    headers = ["ID", "Mensajero", "Fecha", "Subtotal Servicios",
               "Comisión (20%)", "Aseo", "Base Prestada", "Neto Mensajero", "Ganancia Empresa", "Domicilios"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = border

    # ── Datos ──
    from database import database as db
    for row_num, liq in enumerate(datos, 5):
        comision = liq.get("comision_empresa", 0)
        aseo = liq.get("descuento_aseo", 0)
        ganancia_empresa = comision + aseo
        servicios_liq = db.obtener_servicios_por_liquidacion(liq["id"])
        descripciones = ", ".join([s.get("descripcion", "") for s in servicios_liq if s.get("descripcion")])

        valores = [
            liq.get("id", ""),
            liq.get("mensajero_nombre", ""),
            liq.get("fecha", ""),
            formatear_moneda(liq.get("subtotal_servicios", 0)),
            formatear_moneda(comision),
            formatear_moneda(aseo),
            formatear_moneda(liq.get("base_prestada", 0)),
            formatear_moneda(liq.get("neto_mensajero", 0)),
            formatear_moneda(ganancia_empresa),
            descripciones
        ]
        for col_num, valor in enumerate(valores, 1):
            cell = ws.cell(row=row_num, column=col_num, value=valor)
            cell.font = money_font if 4 <= col_num <= 9 else cell_font
            cell.border = border
            cell.alignment = Alignment(horizontal="center" if col_num <= 3 else "right")
            if (row_num - 5) % 2 == 1:
                cell.fill = alt_fill

    # ── Totales ──
    if datos:
        fila_total = len(datos) + 5
        ws.cell(row=fila_total, column=3, value="TOTALES:").font = Font(bold=True, size=11)
        total_subtotal = sum(d.get("subtotal_servicios", 0) for d in datos)
        total_comision = sum(d.get("comision_empresa", 0) for d in datos)
        total_aseo = sum(d.get("descuento_aseo", 0) for d in datos)
        total_base = sum(d.get("base_prestada", 0) for d in datos)
        total_neto = sum(d.get("neto_mensajero", 0) for d in datos)
        total_ganancia_empresa = sum(d.get("comision_empresa", 0) + d.get("descuento_aseo", 0) for d in datos)

        ws.cell(row=fila_total, column=4, value=formatear_moneda(total_subtotal)).font = Font(bold=True, color="2ecc71")
        ws.cell(row=fila_total, column=5, value=formatear_moneda(total_comision)).font = Font(bold=True, color="e74c3c")
        ws.cell(row=fila_total, column=6, value=formatear_moneda(total_aseo)).font = Font(bold=True, color="e67e22")
        ws.cell(row=fila_total, column=7, value=formatear_moneda(total_base)).font = Font(bold=True, color="e67e22")
        ws.cell(row=fila_total, column=8, value=formatear_moneda(total_neto)).font = Font(bold=True, color="2ecc71")
        ws.cell(row=fila_total, column=9, value=formatear_moneda(total_ganancia_empresa)).font = Font(bold=True, color="1a1a2e", size=12)

    # ── Ajustar ancho de columnas ──
    anchos = [8, 22, 22, 22, 18, 12, 15, 18, 20, 40]
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    wb.save(ruta_destino)
    return ruta_destino
