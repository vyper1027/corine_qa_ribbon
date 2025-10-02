# -*- coding: utf-8 -*-
"""
Toolbox: Calidad Cartográfica
Propósito: Diligenciar automáticamente el formato GCI-CT-F013 en Excel
Autor: [Tu nombre]
"""

import arcpy
import os
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage


class Toolbox(object):
    def __init__(self):
        self.label = "Calidad Cartográfica"
        self.alias = "calidad"
        self.tools = [GenerarReporte]


class GenerarReporte(object):
    def __init__(self):
        self.label = "Generar Reporte Excel (GCI-CT-F013)"
        self.description = "Llena el formato Excel de control de calidad a partir de parámetros ingresados por el usuario."
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = []

        # ========================
        # GENERAL
        # ========================
        params.append(arcpy.Parameter(
            displayName="Nombre del Intérprete",
            name="interprete",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="General"
        ))

        params.append(arcpy.Parameter(
            displayName="Plancha(s) / Bloque(s)",
            name="planchas",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="General"
        ))

        params.append(arcpy.Parameter(
            displayName="Nombre de Control de Calidad Asignado",
            name="control_calidad",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="General"
        ))

        params.append(arcpy.Parameter(
            displayName="Fecha de Entrega a CC",
            name="fecha_cc",
            datatype="GPDate",
            parameterType="Required",
            direction="Input",
            category="General"
        ))

        params.append(arcpy.Parameter(
            displayName="Fecha de Entrega al Intérprete",
            name="fecha_interp",
            datatype="GPDate",
            parameterType="Required",
            direction="Input",
            category="General"
        ))

        # ========================
        # SEMÁNTICA (con ValueTable)
        # ========================
        vt = arcpy.Parameter(
            displayName="Tabla de registros (diligenciados y faltantes)",
            name="tabla_semantica",
            datatype="GPValueTable",
            parameterType="Required",
            direction="Input",
            category="Semántica"
        )
        vt.columns = [
            ["GPString", "Código"],
            ["GPString", "Insumo"],
            ["GPString", "Apoyo"],
            ["GPString", "Confiabilidad"],
            ["GPString", "Cambio"]
        ]
        params.append(vt)

        # ========================
        # TOPOLOGÍA
        # ========================
        params.append(arcpy.Parameter(
            displayName="Errores topológicos sobrepuestos",
            name="errores_sobrepuestos",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            category="Topología"
        ))

        params.append(arcpy.Parameter(
            displayName="Errores topológicos huecos",
            name="errores_huecos",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            category="Topología"
        ))

        # ========================
        # TEMÁTICA
        # ========================
        params.append(arcpy.Parameter(
            displayName="Número de polígonos con área < unidad mínima",
            name="poligonos_area_min",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            category="Temática"
        ))

        params.append(arcpy.Parameter(
            displayName="Número de puntos entregados para revisión",
            name="puntos_revision",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            category="Temática"
        ))

        # ========================
        # EMPALMES
        # ========================
        params.append(arcpy.Parameter(
            displayName="Número de errores de empalmes",
            name="errores_empalmes",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
            category="Empalmes"
        ))

        # ========================
        # CONTROL DE CAMBIOS
        # ========================
        params.append(arcpy.Parameter(
            displayName="Versión de Control de Cambios",
            name="version",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="Control de cambios"
        ))

        params.append(arcpy.Parameter(
            displayName="Descripción del Cambio",
            name="descripcion",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="Control de cambios"
        ))

        # ========================
        # FIRMAS
        # ========================
        params.append(arcpy.Parameter(
            displayName="Firma del Intérprete (PNG/JPG)",
            name="firma_interprete",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
            category="Firmas"
        ))

        params.append(arcpy.Parameter(
            displayName="Firma Control de Calidad (PNG/JPG)",
            name="firma_cc",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
            category="Firmas"
        ))

        return params

    def execute(self, parameters, messages):

        # === General ===
        interprete = parameters[0].valueAsText
        planchas = parameters[1].valueAsText
        control_calidad = parameters[2].valueAsText
        fecha_cc = parameters[3].value
        fecha_interp = parameters[4].value

        # === Semántica (tabla con dos filas: diligenciados, faltantes) ===
        tabla_semantica = parameters[5].values  # lista de listas
        # Fila 1: Registros diligenciados (E11:I11)
        if len(tabla_semantica) > 0:
            ws_row = tabla_semantica[0]
            ws_control_row_dil = ws_control_row_fal = None  # para claridad
        # Fila 2: Registros faltantes (E12:I12)
        if len(tabla_semantica) > 1:
            ws_row = tabla_semantica[1]

        # === Topología ===
        errores_sobrepuestos = int(parameters[6].value)
        errores_huecos = int(parameters[7].value)

        # === Temática ===
        poligonos_area_min = int(parameters[8].value)
        puntos_revision = int(parameters[9].value)

        # === Empalmes ===
        errores_empalmes = int(parameters[10].value)

        # === Control de cambios ===
        version = parameters[11].valueAsText
        descripcion = parameters[12].valueAsText

        # === Firmas ===
        firma_interprete = parameters[13].valueAsText
        firma_cc = parameters[14].valueAsText

        # ============================
        # Rutas
        # ============================
        toolbox_dir = os.path.dirname(__file__)
        excel_base = os.path.join(toolbox_dir, "GCI-CT-F013.xlsx")

        parent_dir = os.path.dirname(toolbox_dir)
        report_dir = os.path.join(parent_dir, "reporte")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        excel_out = os.path.join(
            report_dir,
            f"GCI-CT-F013_diligenciado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        wb = load_workbook(excel_base)
        ws_control = wb["CONTROL CALIDAD INTERPRETACION"]

        # ============================
        # Hoja: CONTROL DE CALIDAD
        # ============================
        # General
        ws_control["D4"] = interprete
        ws_control["D5"] = planchas
        ws_control["C6"] = control_calidad
        ws_control["J3"] = fecha_cc
        ws_control["J4"] = fecha_interp

        # Semántica (dos filas)
        if len(tabla_semantica) > 0:
            ws_row = tabla_semantica[0]
            ws_control["E11"], ws_control["F11"], ws_control["G11"], ws_control["H11"], ws_control["I11"] = ws_row
        if len(tabla_semantica) > 1:
            ws_row = tabla_semantica[1]
            ws_control["E12"], ws_control["F12"], ws_control["G12"], ws_control["H12"], ws_control["I12"] = ws_row

        # Topológica
        ws_control["E18"] = errores_sobrepuestos
        ws_control["E19"] = errores_huecos

        # Temática
        ws_control["E28"] = poligonos_area_min
        ws_control["E29"] = puntos_revision

        # Empalmes
        ws_control["E34"] = errores_empalmes

        # Firmas
        if firma_interprete and os.path.exists(firma_interprete):
            img = XLImage(firma_interprete)
            img.width, img.height = 120, 50
            ws_control.add_image(img, "C40")

        if firma_cc and os.path.exists(firma_cc):
            img = XLImage(firma_cc)
            img.width, img.height = 120, 50
            ws_control.add_image(img, "H40")

        # ============================
        # Hoja: CONTROL DE CAMBIOS
        # ============================
        ws_cambios = wb["Control de Cambios"]
        last_row = ws_cambios.max_row + 1
        ws_cambios[f"B{last_row}"] = version
        ws_cambios[f"C{last_row}"] = datetime.now().strftime("%Y-%m-%d")
        ws_cambios[f"D{last_row}"] = descripcion

        # ============================
        # Guardar copia
        # ============================
        wb.save(excel_out)
        arcpy.AddMessage(f"✅ Reporte generado en: {excel_out}")
