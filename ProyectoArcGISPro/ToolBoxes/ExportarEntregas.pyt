# -*- coding: utf-8 -*-
import arcpy
import os


class Toolbox:
    def __init__(self):
        self.label = "Toolbox"
        self.alias = "toolbox"
        self.tools = [ExportarEntrega]


class ExportarEntrega:
    def __init__(self):
        self.label = "Exportar Entrega"
        self.description = "Recorta una capa en base a geometrías seleccionadas desde otra capa según atributos."

    def getParameterInfo(self):
        params = []

        # 1. Capa base de recorte
        base_layer = arcpy.Parameter(
            displayName="Capa de recorte (con atributos)",
            name="base_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        params.append(base_layer)

        # 2. Campo de atributo
        field_param = arcpy.Parameter(
            displayName="Campo de atributo",
            name="field_name",
            datatype="GPString",  # Campo como texto
            parameterType="Required",
            direction="Input"
        )
        field_param.filter.type = "ValueList"
        field_param.filter.list = ["Mes_Interpretacion", "Bloque", "Plancha"]
        params.append(field_param)


        # 3. Valores únicos del atributo (multi-chequeables)
        values_param = arcpy.Parameter(
            displayName="Valores del atributo",
            name="field_values",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )
        params.append(values_param)

        # 4. Capa objetivo a recortar
        target_layer = arcpy.Parameter(
            displayName="Capa a recortar",
            name="target_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        params.append(target_layer)

        # 5. Salida
        output_fc = arcpy.Parameter(
            displayName="Salida del recorte",
            name="output_fc",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output"
        )
        params.append(output_fc)

        return params

    def updateParameters(self, parameters):
        base_layer = parameters[0].value
        field_name = parameters[1].value
        field_values = parameters[2]

        # Autocompletar valores únicos del campo
        if base_layer and field_name and not field_values.altered:
            try:
                valores_unicos = set()
                with arcpy.da.SearchCursor(base_layer, [field_name]) as cursor:
                    for row in cursor:
                        if row[0] is not None:
                            valores_unicos.add(str(row[0]))
                field_values.filter.list = sorted(valores_unicos)
                field_values.values = sorted(valores_unicos)
            except Exception as e:
                arcpy.AddWarning(f"No se pudieron cargar los valores únicos del campo: {e}")

    def execute(self, parameters, messages):
        base_layer = parameters[0].valueAsText
        field_name = str(parameters[1].value)
        valores = parameters[2].values
        target_layer = parameters[3].valueAsText
        output_fc = parameters[4].valueAsText

        if not valores:
            arcpy.AddError("Debe seleccionar al menos un valor del atributo.")
            return

        # Detectar tipo del campo seleccionado
        field_type = None
        try:
            desc = arcpy.Describe(base_layer)
            for fld in desc.fields:
                if fld.name == field_name:
                    field_type = fld.type  # Ej: "String", "Integer", "Double"
                    break
        except Exception as e:
            arcpy.AddError(f"No se pudo obtener el tipo del campo '{field_name}': {e}")
            return

        if not field_type:
            arcpy.AddError(f"No se pudo determinar el tipo del campo '{field_name}'.")
            return

        # Construir cláusula WHERE
        condiciones = []
        for val in valores:
            try:
                if field_type in ["SmallInteger", "Integer", "Double"]:
                    int(val)  # validar
                    condiciones.append(f"{field_name} = {val}")
                else:
                    val_escaped = val.replace("'", "''")
                    condiciones.append(f"{field_name} = '{val_escaped}'")
            except Exception:
                arcpy.AddError(f"El valor '{val}' no es válido para el campo de tipo {field_type}")
                return

        where_clause = " OR ".join(condiciones)
        arcpy.AddMessage(f"Filtrando capa base con: {where_clause}")

        try:
            arcpy.MakeFeatureLayer_management(base_layer, "recorte_sel", where_clause)
        except Exception as e:
            arcpy.AddError(f"❌ Error al aplicar filtro: {e}")
            return

        try:
            disuelto = arcpy.management.Dissolve("recorte_sel")[0]
        except Exception as e:
            arcpy.AddError(f"❌ Error al disolver geometrías: {e}")
            return

        if not output_fc:
            output_fc = os.path.join(arcpy.env.scratchGDB, f"{field_name}_Recorte")

        try:
            arcpy.analysis.Intersect([target_layer, disuelto], output_fc)
            arcpy.AddMessage(f"✅ Recorte generado en: {output_fc}")
        except Exception as e:
            arcpy.AddError(f"❌ Error durante Intersect: {e}")
