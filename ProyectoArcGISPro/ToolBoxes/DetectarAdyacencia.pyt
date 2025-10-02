# -*- coding: utf-8 -*-
import arcpy
import os

class Toolbox(object):
    def __init__(self):
        self.label = "Detección de Adyacencias"
        self.alias = "adyacencia_toolbox"
        self.tools = [DetectarAdyacencia]

class DetectarAdyacencia(object):
    def __init__(self):
        self.label = "Detectar Polígonos Adyacentes"
        self.description = "Detecta pares de polígonos que se tocan y tienen el mismo código. Estos deberían estar disueltos."
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = []

        # Parámetro 0: Feature Layer
        input_fc = arcpy.Parameter(
            displayName="Capa de Entrada",
            name="input_fc",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input")

        # Parámetro 1: Campo CODIGO (auto llenado)
        codigo_field = arcpy.Parameter(
            displayName="Campo de Código",
            name="codigo_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        codigo_field.parameterDependencies = [input_fc.name]
        codigo_field.filter.list = ['Short', 'Long', 'Text']

        # Parámetro 2: Tabla de salida
        output_table = arcpy.Parameter(
            displayName="Tabla de Salida",
            name="output_table",
            datatype="Table",
            parameterType="Required",
            direction="Output")

        params.extend([input_fc, codigo_field, output_table])
        return params

    def execute(self, parameters, messages):
        input_fc = parameters[0].valueAsText
        codigo_field = parameters[1].valueAsText
        output_table = parameters[2].valueAsText

        arcpy.AddMessage(f"Analizando adyacencias por campo: {codigo_field}")

        # Leer todas las geometrías y atributos
        features = []
        with arcpy.da.SearchCursor(input_fc, ["OID@", "SHAPE@", codigo_field]) as cursor:
            for row in cursor:
                if row[1] is not None:
                    features.append((row[0], row[1], row[2]))

        # Comparar cada polígono con los siguientes
        resultado = []
        total = len(features)
        for i in range(total):
            oid1, geom1, code1 = features[i]
            for j in range(i + 1, total):
                oid2, geom2, code2 = features[j]

                if code1 == code2 and geom1.touches(geom2):
                    resultado.append((oid1, oid2, code1))

        arcpy.AddMessage(f"Se encontraron {len(resultado)} pares adyacentes con mismo código.")

        # Crear tabla de salida
        if arcpy.Exists(output_table):
            arcpy.Delete_management(output_table)

        arcpy.management.CreateTable(os.path.dirname(output_table), os.path.basename(output_table))
        arcpy.management.AddField(output_table, "OID_1", "LONG")
        arcpy.management.AddField(output_table, "OID_2", "LONG")
        arcpy.management.AddField(output_table, "CODIGO", "TEXT")

        with arcpy.da.InsertCursor(output_table, ["OID_1", "OID_2", "CODIGO"]) as insert_cursor:
            for row in resultado:
                insert_cursor.insertRow(row)

        arcpy.AddMessage(f"Resultados guardados en: {output_table}")
        
        # Crear shapefile con los polígonos involucrados
        arcpy.AddMessage("Exportando polígonos involucrados en adyacencias...")

        # Obtener todos los OIDs únicos que participaron
        oids_involucrados = set()
        for r in resultado:
            oids_involucrados.add(r[0])
            oids_involucrados.add(r[1])

        # Construir cláusula SQL para seleccionar esos OIDs
        oid_field = arcpy.Describe(input_fc).OIDFieldName
        oid_list = ",".join(str(oid) for oid in oids_involucrados)
        where_clause = f"{oid_field} IN ({oid_list})"

        # Crear una capa y seleccionar
        arcpy.MakeFeatureLayer_management(input_fc, "layer_involucrados", where_clause)

        # Exportar la selección a shapefile
        shp_output = os.path.splitext(output_table)[0] + "_adyacentes.shp"
        arcpy.CopyFeatures_management("layer_involucrados", shp_output)

        arcpy.AddMessage(f"Shapefile exportado: {shp_output}")

        arcpy.AddMessage("Análisis completado correctamente.")
        
