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

        # 2. Campo de atributo (dinámico)
        field_param = arcpy.Parameter(
            displayName="Campo de atributo",
            name="field_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        field_param.filter.type = "ValueList"  # se llenará dinámicamente
        params.append(field_param)

        # 3. Valores únicos del atributo
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
        field_name = parameters[1]
        field_values = parameters[2]

        # 🔹 Actualizar lista de campos de forma dinámica
        if base_layer and not field_name.altered:
            try:
                desc = arcpy.Describe(base_layer)
                fields = [f.name for f in desc.fields if f.type not in ("Geometry", "OID")]
                field_name.filter.list = fields
            except Exception as e:
                arcpy.AddWarning(f"No se pudieron cargar los campos de la capa: {e}")

        # 🔹 Autocompletar valores únicos del campo seleccionado
        if base_layer and field_name.value and not field_values.altered:
            try:
                valores_unicos = set()
                with arcpy.da.SearchCursor(base_layer, [field_name.value]) as cursor:
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

        # 🔹 Detectar tipo de campo
        field_type = None
        try:
            desc = arcpy.Describe(base_layer)
            for fld in desc.fields:
                if fld.name == field_name:
                    field_type = fld.type  # Ej: "String", "Integer", "Double", "Date"
                    break
        except Exception as e:
            arcpy.AddError(f"No se pudo obtener el tipo del campo '{field_name}': {e}")
            return

        if not field_type:
            arcpy.AddError(f"No se pudo determinar el tipo del campo '{field_name}'.")
            return

        # 🔹 Construcción segura de cláusula WHERE
        condiciones = []
        field_name_sql = arcpy.AddFieldDelimiters(base_layer, field_name)

        for val in valores:
            try:
                if field_type in ["SmallInteger", "Integer", "Double"]:
                    condiciones.append(f"{field_name_sql} = {val}")
                elif field_type == "Date":
                    condiciones.append(f"{field_name_sql} = date '{val}'")  
                else:  # String, GUID, etc.
                    val_escaped = val.replace("'", "''")
                    condiciones.append(f"{field_name_sql} = '{val_escaped}'")
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
