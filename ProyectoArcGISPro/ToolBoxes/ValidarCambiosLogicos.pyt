# -*- coding: utf-8 -*-
import arcpy
import os
import uuid

class Toolbox(object):
    def __init__(self):
        self.label = "Validación de Cambios Temáticos"
        self.alias = "validar_cambios"
        self.tools = [ValidarCambiosTematicos]

class ValidarCambiosTematicos(object):
    def __init__(self):
        self.label = "HerramientaNo12 - Exportar y preparar T1/T2"
        self.description = (
            "Exporta T1 y T2 con CodigoT1/CodigoT2, intersecta, "
            "marca cambios ilógicos y selecciona cambios lógicos menores al umbral. "
            "Aplica filtro de internos (no tocan el límite) a ambas salidas. "
            "Las áreas se calculan como AREA en EPSG:9377."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = []

        p0 = arcpy.Parameter(
            displayName="Capa periodo 1 (T1)",
            name="capa_p1",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        ); params.append(p0)

        p1 = arcpy.Parameter(
            displayName="Campo código periodo 1",
            name="campo_codigo_p1",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        p1.parameterDependencies = ["capa_p1"]
        params.append(p1)

        p2 = arcpy.Parameter(
            displayName="Capa periodo 2 (T2)",
            name="capa_p2",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        ); params.append(p2)

        p3 = arcpy.Parameter(
            displayName="Campo código periodo 2",
            name="campo_codigo_p2",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        p3.parameterDependencies = ["capa_p2"]
        params.append(p3)

        p4 = arcpy.Parameter(
            displayName="Carpeta de salida (se usará/creará Resultado_Validacion.gdb)",
            name="carpeta_salida",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        ); params.append(p4)

        p5 = arcpy.Parameter(
            displayName="Conservar capas temporales (Herramienta12_Temp#)",
            name="guardar_intermedios",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        p5.value = True
        params.append(p5)

        p6 = arcpy.Parameter(
            displayName="Umbral de área para cambios lógicos (hectáreas)",
            name="umbral_ha",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )
        p6.value = 5.0
        params.append(p6)

        p7 = arcpy.Parameter(
            displayName="Salida final: Herramienta12_Ilogicos",
            name="out_ilogicos",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output"
        ); params.append(p7)

        p8 = arcpy.Parameter(
            displayName="Salida final: Herramienta12_LogicosMenor5ha",
            name="out_logicos_menor_ha",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output"
        ); params.append(p8)

        return params

    def updateMessages(self, parameters):
        if parameters[0].value:
            if getattr(arcpy.Describe(parameters[0].value), "shapeType", "").lower() != "polygon":
                parameters[0].setErrorMessage("T1 debe ser POLÍGONO.")
        if parameters[2].value:
            if getattr(arcpy.Describe(parameters[2].value), "shapeType", "").lower() != "polygon":
                parameters[2].setErrorMessage("T2 debe ser POLÍGONO.")
        if parameters[4].value and not os.path.isdir(parameters[4].valueAsText):
            parameters[4].setErrorMessage("Debe seleccionar una carpeta válida.")
        if parameters[6].value and float(parameters[6].value) <= 0:
            parameters[6].setErrorMessage("El umbral debe ser mayor que 0.")
        return

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        arcpy.env.addOutputsToMap = False

        capa_p1 = parameters[0].valueAsText
        campo1  = parameters[1].valueAsText
        capa_p2 = parameters[2].valueAsText
        campo2  = parameters[3].valueAsText
        carpeta = parameters[4].valueAsText
        guardar = bool(parameters[5].value)
        umbral_ha = float(parameters[6].value) if parameters[6].value else 5.0

        gdbname = "Resultado_Validacion.gdb"
        gdbpath = os.path.join(carpeta, gdbname)
        if not arcpy.Exists(gdbpath):
            arcpy.AddMessage("Creando geodatabase de resultados...")
            arcpy.management.CreateFileGDB(carpeta, gdbname)

        Temp1 = os.path.join(gdbpath, "Herramienta12_Temp1")  # T1 export con CodigoT1
        Temp2 = os.path.join(gdbpath, "Herramienta12_Temp2")  # T2 export con CodigoT2
        Temp3 = os.path.join(gdbpath, "Herramienta12_Temp3")  # PairwiseIntersect T1-T2
        Temp4 = os.path.join(gdbpath, "Herramienta12_Temp4")  # Cambios filtrados + LogicFlag + area_ha_9377
        Temp5 = os.path.join(gdbpath, "Herramienta12_Temp5_Limite")  # Límite disuelto (externo)
        OUT_ILOG = os.path.join(gdbpath, "Herramienta12_Ilogicos")
        OUT_LOGS = os.path.join(gdbpath, "Herramienta12_LogicosMenor5ha")

        parameters[7].value = OUT_ILOG
        parameters[8].value = OUT_LOGS

        for fc in [Temp1, Temp2, Temp3, Temp4, Temp5, OUT_ILOG, OUT_LOGS]:
            if arcpy.Exists(fc):
                try: arcpy.management.Delete(fc)
                except: pass

        # 1) Exportar T1 (CodigoT1) y limpiar campos
        arcpy.AddMessage(f"Exportando T1 a: {Temp1}")
        arcpy.conversion.ExportFeatures(capa_p1, Temp1)
        if "CodigoT1" not in [f.name for f in arcpy.ListFields(Temp1)]:
            arcpy.management.AddField(Temp1, "CodigoT1", "TEXT", field_length=255)
        arcpy.management.CalculateField(Temp1, "CodigoT1", f"!{campo1}!", "PYTHON3")

        drop_list = [
            "codigo","leyenda","insumo","apoyo","confiabili","cambio",
            "nivel_1","nivel_2","nivel_3","nivel_4","nivel_5","nivel_6","area_ha"
        ]
        exist_t1 = [f.name for f in arcpy.ListFields(Temp1)]
        to_drop_t1 = [f for f in drop_list if f in exist_t1]
        if to_drop_t1:
            arcpy.management.DeleteField(Temp1, to_drop_t1)

        # 2) Exportar T2 (CodigoT2) y limpiar campos
        arcpy.AddMessage(f"Exportando T2 a: {Temp2}")
        arcpy.conversion.ExportFeatures(capa_p2, Temp2)
        if "CodigoT2" not in [f.name for f in arcpy.ListFields(Temp2)]:
            arcpy.management.AddField(Temp2, "CodigoT2", "TEXT", field_length=255)
        arcpy.management.CalculateField(Temp2, "CodigoT2", f"!{campo2}!", "PYTHON3")
        exist_t2 = [f.name for f in arcpy.ListFields(Temp2)]
        to_drop_t2 = [f for f in drop_list if f in exist_t2]
        if to_drop_t2:
            arcpy.management.DeleteField(Temp2, to_drop_t2)

        # 3) PairwiseIntersect T1 & T2
        arcpy.AddMessage("Ejecutando PairwiseIntersect entre T1 y T2...")
        arcpy.analysis.PairwiseIntersect(
            in_features=f"{Temp1};{Temp2}",
            out_feature_class=Temp3,
            join_attributes="NO_FID",
            cluster_tolerance=None,
            output_type="INPUT"
        )

        # 4) Filtrar cambios (CodigoT1 != CodigoT2) y sin nulos → Temp4
        arcpy.AddMessage("Filtrando cambios (CodigoT1 <> CodigoT2) y sin nulos...")
        arcpy.management.MakeFeatureLayer(Temp3, "lyr_pw")
        arcpy.management.SelectLayerByAttribute(
            "lyr_pw", "NEW_SELECTION",
            "CodigoT1 IS NOT NULL AND CodigoT2 IS NOT NULL AND CodigoT1 <> CodigoT2"
        )
        arcpy.management.CopyFeatures("lyr_pw", Temp4)

        # 5) LogicFlag + área planar (EPSG:9377) en Temp4
        ilogicos = [
            '111_112','111_121','111_124','111_125','111_131','111_141','111_142',
            '111_511','111_512','111_231','111_233','111_242','111_243','111_244',
            '111_411','112_212','112_221','112_223','112_241','112_511','112_231',
            '112_232','112_233','112_242','112_243','112_244','112_245','112_311',
            '112_314','112_321','112_322','112_323','121_111','121_112','121_124',
            '121_131','121_132','121_142','121_212','121_221','121_223','121_241',
            '121_225','121_231','121_233','121_242','121_315','122_233','124_242',
            '124_244','131_311','131_313','212_313','212_314','214_314','223_311',
            '223_314','231_311','231_313','231_314','232_313','233_311','233_312',
            '233_313','233_314','241_311','241_313','242_311','242_313','242_314',
            '243_311','243_313','311_312','311_321','311_322','312_311','312_321',
            '312_322','313_321','313_322','314_321','314_322','315_311','315_313',
            '315_314','321_311','321_312','321_313','321_314','321_322','321_323',
            '322_311','322_313','322_314','322_321','322_323','323_321','323_322',
            '331_311','331_314','331_323','333_311','333_313','413_521','514_242'
        ]

        if "LogicFlag" not in [f.name for f in arcpy.ListFields(Temp4)]:
            arcpy.management.AddField(Temp4, "LogicFlag", "TEXT", field_length=10)

        with arcpy.da.UpdateCursor(Temp4, ["CodigoT1","CodigoT2","LogicFlag"]) as cursor:
            for c1, c2, _ in cursor:
                combo = f"{str(c1).strip()}_{str(c2).strip()}"[:7]
                lf = "ilógico" if combo in ilogicos else "lógico"
                cursor.updateRow([c1, c2, lf])

        sr9377 = arcpy.SpatialReference(9377)
        if "area_ha_9377" not in [f.name for f in arcpy.ListFields(Temp4)]:
            arcpy.management.AddField(Temp4, "area_ha_9377", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            Temp4, [["area_ha_9377", "AREA"]],
            area_unit="HECTARES",
            coordinate_system=sr9377
        )

        # 6) Exportar ilógicos → OUT_ILOG
        arcpy.management.MakeFeatureLayer(Temp4, "lyr_ilog")
        arcpy.management.SelectLayerByAttribute("lyr_ilog", "NEW_SELECTION", "LogicFlag = 'ilógico'")
        arcpy.management.CopyFeatures("lyr_ilog", OUT_ILOG)
        messages.addMessage(f"Total cambios ilógicos (antes de filtrar internos): {arcpy.management.GetCount(OUT_ILOG)[0]}")

        # 7) Exportar lógicos < umbral → OUT_LOGS
        arcpy.management.MakeFeatureLayer(Temp4, "lyr_logs")
        arcpy.management.SelectLayerByAttribute(
            "lyr_logs", "NEW_SELECTION",
            f"LogicFlag = 'lógico' AND area_ha_9377 < {umbral_ha}"
        )
        arcpy.management.CopyFeatures("lyr_logs", OUT_LOGS)
        messages.addMessage(f"Cambios lógicos < {umbral_ha} ha (antes de filtrar internos): {arcpy.management.GetCount(OUT_LOGS)[0]}")

        # 8) CREAR LÍMITE CORRECTAMENTE: MERGE(Temp1,Temp2) -> PairwiseDissolve -> Temp5
        arcpy.AddMessage("Generando límite disuelto y filtrando internos (no tocan borde)...")
        tmp_merge = os.path.join("in_memory", f"tmp_merge_{uuid.uuid4().hex[:8]}")
        arcpy.management.Merge([Temp1, Temp2], tmp_merge)
        arcpy.analysis.PairwiseDissolve(tmp_merge, Temp5)

        def dejar_internos(fc_salida, nombre_lyr):
            if not arcpy.Exists(fc_salida) or int(arcpy.management.GetCount(fc_salida)[0]) == 0:
                return
            arcpy.management.MakeFeatureLayer(fc_salida, nombre_lyr)
            arcpy.management.SelectLayerByLocation(
                in_layer=nombre_lyr,
                overlap_type="SHARE_A_LINE_SEGMENT_WITH",
                select_features=Temp5,
                selection_type="NEW_SELECTION",
                invert_spatial_relationship="INVERT"
            )
            tmp_int = os.path.join("in_memory", f"{uuid.uuid4().hex[:8]}_int")
            arcpy.management.CopyFeatures(nombre_lyr, tmp_int)
            arcpy.management.Delete(fc_salida)
            arcpy.management.CopyFeatures(tmp_int, fc_salida)

        dejar_internos(OUT_ILOG, "lyr_ilog_int")
        dejar_internos(OUT_LOGS, "lyr_logs_int")

        # Recuento final
        if arcpy.Exists(OUT_ILOG):
            messages.addMessage(f"Ilógicos internos (final): {arcpy.management.GetCount(OUT_ILOG)[0]}")
        if arcpy.Exists(OUT_LOGS):
            messages.addMessage(f"Lógicos < {umbral_ha} ha internos (final): {arcpy.management.GetCount(OUT_LOGS)[0]}")

        # 9) Limpiar temporales si no se quieren conservar
        if not guardar:
            arcpy.AddMessage("Eliminando capas temporales (Herramienta12_Temp#)...")
            for fc in [Temp1, Temp2, Temp3, Temp4, Temp5]:
                try:
                    if arcpy.Exists(fc):
                        arcpy.management.Delete(fc)
                except:
                    pass
        else:
            arcpy.AddMessage("Temporales conservadas en Resultado_Validacion.gdb (Herramienta12_Temp1..Temp5).")

        arcpy.AddMessage(f"Salidas en: {gdbpath}")
