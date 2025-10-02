# -*- coding: utf-8 -*-
import arcpy
import os
import sys

class Toolbox(object):
    def __init__(self):
        """Define el toolbox (.pyt)."""
        self.label = "Herramientas Validación Altura de Cultivos"
        self.alias = "validacionAltura"
        self.tools = [CoberturasFueraDeAltura]


class CoberturasFueraDeAltura(object):
    def __init__(self):
        """Define la herramienta dentro del toolbox."""
        self.label = "Validación de Coberturas Agrícolas por Altura"
        self.description = "Compara la cobertura del suelo (CLC) con un DEM para identificar cultivos fuera del criterio de altitud."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define los parámetros de la herramienta."""
        params = []

        # 1. Capa CLC
        param0 = arcpy.Parameter(
            displayName="Capa CLC",
            name="CapaCLC",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # 2. DEM
        param1 = arcpy.Parameter(
            displayName="Modelo Digital de Elevación (DEM)",
            name="DEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        # 3. Carpeta de salida
        param2 = arcpy.Parameter(
            displayName="Carpeta de salida",
            name="CarpetaSalida",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [param0, param1, param2]

    def execute(self, parameters, messages):
        """Cuerpo principal de la herramienta."""
        CapaCLC = parameters[0].valueAsText
        DEM = parameters[1].valueAsText
        CarpetaSalida = parameters[2].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension("Spatial")

        arcpy.AddMessage("Verificando capas de entrada...")
        arcpy.AddMessage(f"Capa CLC: {CapaCLC}")
        arcpy.AddMessage(f"DEM: {DEM}")
        arcpy.AddMessage(f"Carpeta salida: {CarpetaSalida}")

        # Crear GDB salida
        gdbsalida = "Resultado_Validacion.gdb"
        rtgdbsalida = os.path.join(CarpetaSalida, gdbsalida)
        if not os.path.exists(rtgdbsalida):
            arcpy.management.CreateFileGDB(CarpetaSalida, gdbsalida, "10.0")
            arcpy.AddMessage("GDB creada para resultados.")
        else:
            arcpy.AddMessage("Ya existe la GDB, se agregará el FeatureClass.")

        # Verificar proyección DEM
        desc = arcpy.Describe(DEM)
        sr = desc.spatialReference
        if sr is None:
            arcpy.AddError("El DEM no tiene sistema de coordenadas definido.")
            sys.exit(1)

        origen_nacional = ["MAGNA", "SIRGAS", "BOGOTÁ"]
        if any(nombre in sr.name.upper() for nombre in origen_nacional):
            arcpy.AddMessage(f"DEM con sistema válido: {sr.name}")
        else:
            arcpy.AddError(f"Sistema de referencia diferente: {sr.name}. Debe estar en origen nacional.")
            sys.exit(1)

        # Diccionario de cultivos y altitudes
        dcultivos = {
            '2123': 1500, '2131': 1500, '2134': 1500, '2232': 1500,
            '22121': 1500, '2223': 2000, '2234': 2000, '2212': 2500,
            '2213': 2500, '2222': 2500, '2233': 2500, '22122': 2500,
            '2224': 3000, '2122': 3500, '2121': [0, 1700], '2151': [1500, 4500]
        }
        where_clause = f"codigo IN ({', '.join(map(str, dcultivos))})"
        arcpy.AddMessage(f"Condición: {where_clause}")

        # Filtrar CLC
        CLC_filtrada = os.path.join(rtgdbsalida, "CLC_CultivosFiltrados")
        arcpy.analysis.Select(CapaCLC, CLC_filtrada, where_clause)
        arcpy.AddMessage(f"Capa filtrada: {CLC_filtrada}")

        # Recortar DEM
        DEM_recortado = os.path.join(CarpetaSalida, "DEM_Recortado.tif")
        extent = arcpy.Describe(CLC_filtrada).extent
        extent_str = f"{extent.XMin} {extent.YMin} {extent.XMax} {extent.YMax}"
        arcpy.management.Clip(
            in_raster=DEM,
            rectangle=extent_str,
            out_raster=DEM_recortado,
            in_template_dataset=CLC_filtrada,
            nodata_value="32767",
            clipping_geometry="ClippingGeometry",
            maintain_clipping_extent="NO_MAINTAIN_EXTENT"
        )
        arcpy.AddMessage(f"DEM recortado: {DEM_recortado}")

        # Crear capa reducida
        CLC_reducida = os.path.join(rtgdbsalida, "Herramienta01")
        arcpy.management.CopyFeatures(CLC_filtrada, CLC_reducida)

        # Campo ID
        arcpy.management.AddField(CLC_reducida, "ID", "LONG")
        arcpy.management.CalculateField(CLC_reducida, "ID", "!OBJECTID!", "PYTHON3")

        # Limpiar campos
        campos_mantener = ["ID", "codigo", "area_ha", "Elev_Max", "Elev_Min", "Cumple"]
        campos_protegidos = ["SHAPE", "SHAPE_Length", "SHAPE_Area", "OBJECTID"]
        campos_existentes = [f.name for f in arcpy.ListFields(CLC_reducida)]
        campos_eliminar = [c for c in campos_existentes if c not in campos_mantener and c not in campos_protegidos]
        if campos_eliminar:
            arcpy.management.DeleteField(CLC_reducida, campos_eliminar)

        # Campos extra
        arcpy.management.AddField(CLC_reducida, "Elev_Max", "DOUBLE")
        arcpy.management.AddField(CLC_reducida, "Elev_Min", "DOUBLE")
        arcpy.management.AddField(CLC_reducida, "Cumple", "TEXT", field_length=25)

        # Estadísticas zonales
        Elev_Table = os.path.join(CarpetaSalida, "ZonalStats.dbf")
        arcpy.gp.ZonalStatisticsAsTable_sa(CLC_reducida, "ID", DEM_recortado, Elev_Table, "DATA", "MIN_MAX")
        arcpy.management.JoinField(CLC_reducida, "ID", Elev_Table, "ID", ["MIN", "MAX"])
        arcpy.management.CalculateField(CLC_reducida, "Elev_Min", "!MIN!", "PYTHON3")
        arcpy.management.CalculateField(CLC_reducida, "Elev_Max", "!MAX!", "PYTHON3")
        arcpy.management.DeleteField(CLC_reducida, ["MIN", "MAX"])

        # Validar alturas
        with arcpy.da.UpdateCursor(CLC_reducida, ["ID", "codigo", "Elev_Min", "Elev_Max", "Cumple"]) as cursor:
            for row in cursor:
                codigo = str(row[1])
                elev_min, elev_max = row[2], row[3]
                if codigo in dcultivos and elev_min is not None and elev_max is not None:
                    rango = dcultivos[codigo]
                    if isinstance(rango, list):
                        cumple = "Cumple" if (rango[0] <= elev_min) and (elev_max <= rango[1]) else "No Cumple"
                    else:
                        cumple = "Cumple" if elev_max >= rango else "No Cumple"
                    row[4] = cumple
                else:
                    row[4] = "No definido"
                cursor.updateRow(row)
                arcpy.AddMessage(f"ID {row[0]} - Código {codigo} - Cumple: {row[4]}")

        # Limpieza
        arcpy.management.Delete(Elev_Table)
        arcpy.management.Delete(CLC_filtrada)

        arcpy.AddMessage(f"Validación completada. Resultados en: {CLC_reducida}")
