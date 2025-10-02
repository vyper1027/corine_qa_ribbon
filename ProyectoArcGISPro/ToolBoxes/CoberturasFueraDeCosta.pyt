# -*- coding: utf-8 -*-
import arcpy
import os
from arcpy import env

class Toolbox(object):
    def __init__(self):
        """Define el toolbox (.pyt)."""
        self.label = "Identificacion de coberturas fuera de linea de costa"
        self.alias = "coberturasFueraDeCosta"
        self.tools = [CoberturasFueraDeCosta]


class CoberturasFueraDeCosta(object):
    def __init__(self):
        """Define la herramienta dentro del toolbox."""
        self.label = "Identificación de Coberturas Fuera de Costa"
        self.description = "Genera buffers y selecciona capas CLC según códigos definidos."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define los parámetros de la herramienta."""
        params = []

        # 1. Capa CLC (entrada)
        param0 = arcpy.Parameter(
            displayName="Capa CLC",
            name="CapaCLC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # 2. Línea de costa (entrada)
        param1 = arcpy.Parameter(
            displayName="Línea de costa",
            name="Lcosta",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # 3. Carpeta de salida
        param2 = arcpy.Parameter(
            displayName="Carpeta de salida",
            name="CarpetaSalida",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2]
        return params

    def execute(self, parameters, messages):
        """Cuerpo principal de la herramienta."""
        CapaCLC = parameters[0].valueAsText
        Lcosta = parameters[1].valueAsText
        CarpetaSalida = parameters[2].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension("Spatial")

        buffer1 = "1000"
        fcbuffer1 = os.path.join(CarpetaSalida, f"Buffer1_{buffer1}.shp")
        buffer2 = "2000"
        fcbuffer2 = os.path.join(CarpetaSalida, f"Buffer2_{buffer2}.shp")

        # Crear buffers
        arcpy.AddMessage("Creando Buffer de 1.000 metros...")
        arcpy.analysis.Buffer(Lcosta, fcbuffer1, "1000 Meters", "RIGHT", "ROUND", "ALL", "", "GEODESIC")

        arcpy.AddMessage("Creando Buffer de 2.000 metros...")
        arcpy.analysis.Buffer(Lcosta, fcbuffer2, "2000 Meters", "RIGHT", "ROUND", "ALL", "", "GEODESIC")

        # Selecciones CLC
        SalidaSeleccion1 = os.path.join(CarpetaSalida, "SeleccionCLC1.shp")
        SalidaSeleccion2 = os.path.join(CarpetaSalida, "SeleccionCLC2.shp")

        arcpy.conversion.ExportFeatures(
            CapaCLC, SalidaSeleccion1,
            where_clause="codigo IN (421,422,423,521,522,523,311122,1232)")

        arcpy.conversion.ExportFeatures(
            CapaCLC, SalidaSeleccion2,
            where_clause="codigo IN (523)")

        # Selección invertida con buffers
        arcpy.MakeFeatureLayer_management(SalidaSeleccion1, "salidaslc1")
        arcpy.MakeFeatureLayer_management(SalidaSeleccion2, "salidaslc2")

        arcpy.management.SelectLayerByLocation(
            "salidaslc1", "INTERSECT", fcbuffer1,
            selection_type="NEW_SELECTION", invert_spatial_relationship="INVERT")
        arcpy.CopyFeatures_management("salidaslc1", os.path.join(CarpetaSalida, "ResultadoCapa1.shp"))

        arcpy.management.SelectLayerByLocation(
            "salidaslc2", "INTERSECT", fcbuffer2,
            selection_type="NEW_SELECTION", invert_spatial_relationship="INVERT")
        arcpy.CopyFeatures_management("salidaslc2", os.path.join(CarpetaSalida, "ResultadoCapa2.shp"))

        # Crear GDB de salida
        gdbsalida = "Resultado_Validacion.gdb"
        rtgdbsalida = os.path.join(CarpetaSalida, gdbsalida)
        if not os.path.exists(rtgdbsalida):
            arcpy.management.CreateFileGDB(CarpetaSalida, gdbsalida, "10.0")

        arcpy.CopyFeatures_management("salidaslc1", os.path.join(rtgdbsalida, "Herramienta02_1"))
        arcpy.CopyFeatures_management("salidaslc2", os.path.join(rtgdbsalida, "Herramienta02_2"))

        # Limpieza de capas temporales
        arcpy.management.Delete([fcbuffer1, fcbuffer2, SalidaSeleccion1, SalidaSeleccion2,
                                 os.path.join(CarpetaSalida, "ResultadoCapa1.shp"),
                                 os.path.join(CarpetaSalida, "ResultadoCapa2.shp")])

        arcpy.AddMessage("Proceso completado con éxito 🚀")
