# -*- coding: utf-8 -*-
import arcpy

class Toolbox:
    def __init__(self):
        self.label = "Area Filter Toolbox"
        self.alias = "area_filter_toolbox"
        self.tools = [FilterPolygonsByArea]

class FilterPolygonsByArea:
    def __init__(self):
        self.label = "Encontrar Polígonos por area"
        self.description = "Filtra polígonos cuya área es menor a 5 ha, 25 ha o ambas y exporta el resultado a un nuevo shapefile."

    def getParameterInfo(self):
        params = []

        # Parámetro 0 - Capa de entrada
        in_fc = arcpy.Parameter(
            displayName="Capa de entrada (polígonos)",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Parámetro 1 - Campo de área
        area_field = arcpy.Parameter(
            displayName="Campo de área (hectáreas)",
            name="area_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        area_field.parameterDependencies = [in_fc.name]  # Depende de la capa de entrada

        # Parámetro 2 - Menores a 5 ha
        less_than_5 = arcpy.Parameter(
            displayName="Incluir polígonos < 5 ha",
            name="less_than_5",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        less_than_5.value = True

        # Parámetro 3 - Menores a 25 ha
        less_than_25 = arcpy.Parameter(
            displayName="Incluir polígonos < 25 ha",
            name="less_than_25",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        less_than_25.value = False

        # Parámetro 4 - Salida
        out_fc = arcpy.Parameter(
            displayName="Capa de salida",
            name="out_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        params.extend([in_fc, area_field, less_than_5, less_than_25, out_fc])
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        in_fc = parameters[0].valueAsText
        area_field = parameters[1].valueAsText
        include_5 = parameters[2].value
        include_25 = parameters[3].value
        out_fc = parameters[4].valueAsText

        if not include_5 and not include_25:
            raise arcpy.ExecuteError("Debe seleccionar al menos una de las opciones: < 5 ha o < 25 ha")

        # Crear expresión de filtro
        expressions = []
        if include_5:
            expressions.append(f'"{area_field}" < 5')
        if include_25:
            expressions.append(f'"{area_field}" < 25')

        where_clause = " OR ".join(expressions)

        # Usar MakeFeatureLayer y SelectLayerByAttribute
        temp_layer = "temp_layer"
        arcpy.MakeFeatureLayer_management(in_fc, temp_layer)
        arcpy.SelectLayerByAttribute_management(temp_layer, "NEW_SELECTION", where_clause)

        # Copiar la selección al shapefile de salida
        arcpy.CopyFeatures_management(temp_layer, out_fc)

        arcpy.AddMessage(f"Se ha generado correctamente la capa con polígonos que cumplen: {where_clause}")
        return
