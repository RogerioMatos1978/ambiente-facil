"""Utilitários genéricos de exportação: CSV, Excel (XLSX) e PDF."""

import csv
import io

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def exportar_csv(nome_arquivo: str, cabecalhos: list, linhas: list) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}.csv"'
    escritor = csv.writer(response)
    escritor.writerow(cabecalhos)
    escritor.writerows(linhas)
    return response


def exportar_xlsx(nome_arquivo: str, cabecalhos: list, linhas: list, titulo_planilha="Dados") -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = titulo_planilha
    ws.append(cabecalhos)
    for celula in ws[1]:
        celula.font = Font(bold=True)
    for linha in linhas:
        ws.append(linha)
    for coluna in ws.columns:
        largura = max(len(str(c.value)) if c.value is not None else 0 for c in coluna) + 2
        ws.column_dimensions[coluna[0].column_letter].width = min(largura, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}.xlsx"'
    return response


def exportar_pdf(nome_arquivo: str, titulo: str, cabecalhos: list, linhas: list) -> HttpResponse:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elementos = [Paragraph(titulo, estilos["Title"])]

    dados_tabela = [cabecalhos] + [[str(v) for v in linha] for linha in linhas]
    tabela = Table(dados_tabela, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )
    elementos.append(tabela)
    doc.build(elementos)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}.pdf"'
    return response
