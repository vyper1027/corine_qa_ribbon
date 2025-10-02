# -*- coding: utf-8 -*-
import arcpy
import os
import sys

class Toolbox(object):
    def __init__(self):
        """Define el toolbox (.pyt)."""
        self.label = "Revisión de Códigos de Cambio CLC"
        self.alias = "cambioCLC"
        self.tools = [RevisarCodigosCambio]


class RevisarCodigosCambio(object):
    def __init__(self):
        """Define la herramienta dentro del toolbox."""
        self.label = "Revisión Códigos de Cambio"
        self.description = ("Compara dos capas CLC (año original y reinterpretado) "
                            "para asignar el atributo 'cambio' según reglas definidas.")
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define los parámetros de entrada."""
        params = []

        # 1. Capa original
        param0 = arcpy.Parameter(
            displayName="Capa original (año par)",
            name="CapaOriginal",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # 2. Año original
        param1 = arcpy.Parameter(
            displayName="Año original (ej. 2018)",
            name="AnioOriginal",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        # 3. Capa reinterpretada
        param2 = arcpy.Parameter(
            displayName="Capa reinterpretada (año par)",
            name="CapaReinterpretada",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # 4. Año reinterpretado
        param3 = arcpy.Parameter(
            displayName="Año reinterpretado (ej. 2020)",
            name="AnioReinterpretado",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        # 5. Carpeta de salida
        param4 = arcpy.Parameter(
            displayName="Carpeta de salida",
            name="CarpetaSalida",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        """Ejecución principal."""
        capa_original = parameters[0].valueAsText
        anio_original = int(parameters[1].valueAsText)
        capa_reinterpretada = parameters[2].valueAsText
        anio_reinterpretado = int(parameters[3].valueAsText)
        carpeta_salida = parameters[4].valueAsText

        arcpy.env.overwriteOutput = True

        # --- Validar que los años sean pares ---
        if anio_original % 2 != 0 or anio_reinterpretado % 2 != 0:
            arcpy.AddError("Los años deben ser números pares (ej. 2018, 2020).")
            sys.exit(1)

        if anio_original >= anio_reinterpretado:
            arcpy.AddError("El año original debe ser menor que el año reinterpretado.")
            sys.exit(1)

        # --- Paso 1: centroides de la capa original ---
        centroides = os.path.join(carpeta_salida, f"Centroides_{anio_original}.shp")
        arcpy.FeatureToPoint_management(capa_original, centroides, "INSIDE")
        arcpy.AddMessage(f"Centroides generados: {centroides}")

        # --- Paso 2: selección espacial de polígonos idénticos ---
        arcpy.MakeFeatureLayer_management(capa_reinterpretada, "capa_reint_lyr")
        arcpy.SelectLayerByLocation_management("capa_reint_lyr", "ARE_IDENTICAL_TO", capa_original)

        seleccion_identicos = os.path.join(carpeta_salida, f"Seleccion_Idem_{anio_reinterpretado}.shp")
        arcpy.CopyFeatures_management("capa_reint_lyr", seleccion_identicos)
        arcpy.AddMessage(f"Polígonos idénticos exportados: {seleccion_identicos}")

        # --- Paso 3: selección inversa (polígonos que cambiaron) ---
        arcpy.SelectLayerByLocation_management("capa_reint_lyr", "ARE_IDENTICAL_TO", capa_original, invert_spatial_relationship="INVERT")
        seleccion_cambiados = os.path.join(carpeta_salida, f"Seleccion_Cambiados_{anio_reinterpretado}.shp")
        arcpy.CopyFeatures_management("capa_reint_lyr", seleccion_cambiados)
        arcpy.AddMessage(f"Polígonos que cambiaron exportados: {seleccion_cambiados}")

        # --- Paso 4: join espacial ---
        join_out = os.path.join(carpeta_salida, f"Join_{anio_original}_{anio_reinterpretado}.shp")
        arcpy.SpatialJoin_analysis(seleccion_identicos, centroides, join_out, "JOIN_ONE_TO_ONE", "KEEP_COMMON")
        arcpy.AddMessage(f"Join espacial generado: {join_out}")

        # --- Paso 5: asignación de cambio ---
        arcpy.AddField_management(join_out, "cambio_co", "SHORT")

        """with arcpy.da.UpdateCursor(join_out, ["codigo", "codigo_{}".format(anio_original), "cambio_co"]) as cursor:"""
        with arcpy.da.UpdateCursor(join_out, ["codigo", "codigo_1", "cambio_co"]) as cursor:
            for row in cursor:
                codigo_reint = row[0]
                codigo_orig = row[1]

                if codigo_orig == codigo_reint:
                    row[2] = 1
                elif codigo_orig == 223 and codigo_reint == 2231:
                    row[2] = 1
                else:
                    row[2] = 2  # o 4 según reglas adicionales

                cursor.updateRow(row)

        arcpy.AddMessage(f"Atributo 'cambio' calculado en: {join_out}")
        arcpy.AddMessage("Proceso completado 🚀")
