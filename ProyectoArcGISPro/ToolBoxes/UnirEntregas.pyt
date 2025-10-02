# -*- coding: utf-8 -*-
import arcpy
import os

class Toolbox:
    def __init__(self):
        self.label = "Toolbox Fusionar Entregas"
        self.alias = "fusionar_entregas"
        self.tools = [FusionarEntregas]

class FusionarEntregas:
    def __init__(self):
        self.label = "Fusionar Entregas"
        self.description = "Fusiona dos capas de entregas versionadas y exporta el resultado en una nueva GDB con versionamiento opcional."

    def getParameterInfo(self):
        params = []

        fc1 = arcpy.Parameter(
            displayName="Entrega 1",
            name="fc1",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        fc2 = arcpy.Parameter(
            displayName="Entrega 2",
            name="fc2",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        output_name = arcpy.Parameter(
            displayName="Nombre de la entrega fusionada (opcional)",
            name="output_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )

        validar_topologia = arcpy.Parameter(
            displayName="Validar topología en el resultado",
            name="validate_topology",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        validar_topologia.value = False

        params += [fc1, fc2, output_name, validar_topologia]
        return params

    def execute(self, parameters, messages):
        fc1 = parameters[0].valueAsText
        fc2 = parameters[1].valueAsText
        custom_name = parameters[2].valueAsText if parameters[2].value else None
        validar_topologia = parameters[3].value

        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            project_folder = os.path.dirname(aprx.filePath)
            entregas_folder = os.path.join(project_folder, "entregas")
            os.makedirs(entregas_folder, exist_ok=True)

            # Base name
            if not custom_name:
                base_name = f"Union_{os.path.basename(fc1)}_{os.path.basename(fc2)}"
            else:
                base_name = custom_name

            gdb_name = f"{base_name}.gdb"
            gdb_path = os.path.join(entregas_folder, gdb_name)

            if not arcpy.Exists(gdb_path):
                arcpy.CreateFileGDB_management(entregas_folder, gdb_name)

            spatial_ref = arcpy.Describe(fc1).spatialReference
            dataset_path = os.path.join(gdb_path, base_name)

            if not arcpy.Exists(dataset_path):
                arcpy.CreateFeatureDataset_management(gdb_path, base_name, spatial_ref)

            # 🔁 Función para nombre versionado
            def generar_nombre_versionado(gdb_path, base_name):
                i = 1
                while True:
                    candidate = f"{base_name}_v{i}"
                    existe = False
                    for dirpath, dirnames, filenames in arcpy.da.Walk(gdb_path, datatype="FeatureClass"):
                        if candidate in filenames:
                            existe = True
                            break
                    if not existe:
                        return candidate
                    i += 1

            # Nombre final fusionado versionado
            merged_name = generar_nombre_versionado(gdb_path, base_name)
            merged_fc = os.path.join(dataset_path, merged_name)

            # Fusión
            arcpy.Merge_management([fc1, fc2], merged_fc)
            arcpy.AddMessage(f"✅ Entregas fusionadas en: {merged_fc}")

            # Validar topología si se solicitó
            if validar_topologia:
                topo_name = f"{base_name}_Topology"
                topologia = os.path.join(dataset_path, topo_name)
                arcpy.CreateTopology_management(dataset_path, topo_name, 0.001)
                arcpy.AddFeatureClassToTopology_management(topologia, merged_fc, 1, 1)
                arcpy.AddRuleToTopology_management(topologia, "Must Not Have Gaps (Area)", merged_fc)
                arcpy.AddRuleToTopology_management(topologia, "Must Not Overlap (Area)", merged_fc)
                arcpy.ValidateTopology_management(topologia)
                arcpy.AddMessage("🧪 Topología creada y validada.")

            arcpy.AddMessage(f"📂 GDB de salida: {gdb_path}")
            arcpy.AddMessage(f"📎 Capa fusionada creada: {merged_name}")

        except Exception as e:
            arcpy.AddError(f"❌ Error al fusionar entregas: {e}")
