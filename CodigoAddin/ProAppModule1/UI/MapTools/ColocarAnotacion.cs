using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;

namespace ProAppModule1.UI.MapTools
{
    internal class ColocarAnotacion : MapTool
    {
        private string _featureClassName;
        private string _fcPath;

        public ColocarAnotacion()
        {
            IsSketchTool = true;
            SketchType = SketchGeometryType.Point;
            SketchOutputMode = SketchOutputMode.Map;
        }

        protected override async Task OnToolActivateAsync(bool active)
        {
            try
            {
                var selectedGdbPath = UI.ComboBoxes.QCAnnotationComboBox.SelectedGdbPath;
                if (string.IsNullOrEmpty(selectedGdbPath))
                {
                    MessageBox.Show("Debe seleccionar una geodatabase en el combo de anotaciones.",
                        "Advertencia", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                    return;
                }

                // Nombre de la capa: CC_<GDBName>
                var gdbName = Path.GetFileNameWithoutExtension(selectedGdbPath);
                _featureClassName = $"CC_{gdbName}";
                _fcPath = Path.Combine(selectedGdbPath, _featureClassName);

                await QueuedTask.Run(async () =>
                {
                    using var gdb = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(selectedGdbPath)));

                    // Verificar si ya existe la feature class
                    var fcExists = gdb.GetDefinitions<FeatureClassDefinition>()
                                      .Any(fc => fc.GetName().Equals(_featureClassName, StringComparison.OrdinalIgnoreCase));

                    if (!fcExists)
                    {
                        // Crear la feature class en la raíz de la GDB
                        var parameters = Geoprocessing.MakeValueArray(
                            selectedGdbPath,          // in_dataset (root GDB)
                            _featureClassName,        // out_name
                            "POINT",                  // geometry type
                            null,                     // template
                            "DISABLED",               // has_m
                            "DISABLED",               // has_z
                            SpatialReferences.WGS84.Wkid.ToString() // spatial reference
                        );

                        var gpResult = await Geoprocessing.ExecuteToolAsync(
                            "CreateFeatureclass_management",
                            parameters,
                            null,
                            null,
                            null,
                            GPExecuteToolFlags.None
                        );

                        if (gpResult.IsFailed)
                            throw new Exception($"No se pudo crear la capa de anotaciones: {gpResult.ErrorMessages}");

                        // 👇 Agregar el campo "Observacion" a la nueva feature class
                        var addFieldParams = Geoprocessing.MakeValueArray(
                            Path.Combine(selectedGdbPath, _featureClassName), // in_table
                            "Observacion",                                   // field_name
                            "TEXT"                                           // field_type
                        );

                        var gpAddField = await Geoprocessing.ExecuteToolAsync(
                            "AddField_management",
                            addFieldParams,
                            null,
                            null,
                            null,
                            GPExecuteToolFlags.None
                        );

                        if (gpAddField.IsFailed)
                            throw new Exception($"No se pudo agregar el campo Observacion: {gpAddField.ErrorMessages}");
                    }
                });

                // Agregar la capa al mapa si no está ya
                var map = await GetActiveOrFirstMapAsync();
                await QueuedTask.Run(() =>
                {
                    var existing = map.GetLayersAsFlattenedList()
                                      .OfType<FeatureLayer>()
                                      .FirstOrDefault(fl => fl.Name.Equals(_featureClassName, StringComparison.OrdinalIgnoreCase));

                    if (existing == null)
                        LayerFactory.Instance.CreateLayer(new Uri(_fcPath), map, 0, _featureClassName);
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al preparar la capa de anotaciones: {ex.Message}",
                    "Error", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }


        protected override async Task<bool> OnSketchCompleteAsync(Geometry geometry)
        {
            var selectedGdbPath = UI.ComboBoxes.QCAnnotationComboBox.SelectedGdbPath;
            if (string.IsNullOrEmpty(selectedGdbPath))
            {
                MessageBox.Show("Debe seleccionar una geodatabase en el combo de anotaciones.",
                    "Advertencia", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return false;
            }

            // Recalcular la capa destino en base a la GDB seleccionada actualmente
            var gdbName = Path.GetFileNameWithoutExtension(selectedGdbPath);
            _featureClassName = $"CC_{gdbName}";
            _fcPath = Path.Combine(selectedGdbPath, _featureClassName);

            if (geometry is not MapPoint mp)
                return false;

            try
            {
                // 👇 Verificar/crear capa si no existe
                await QueuedTask.Run(async () =>
                {
                    using var gdb = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(selectedGdbPath)));

                    var fcExists = gdb.GetDefinitions<FeatureClassDefinition>()
                                      .Any(fc => fc.GetName().Equals(_featureClassName, StringComparison.OrdinalIgnoreCase));

                    if (!fcExists)
                    {
                        var parameters = Geoprocessing.MakeValueArray(
                            selectedGdbPath,          // in_dataset
                            _featureClassName,        // out_name
                            "POINT",                  // geometry type
                            null,                     // template
                            "DISABLED",               // has_m
                            "DISABLED",               // has_z
                            SpatialReferences.WGS84.Wkid.ToString()
                        );

                        var gpResult = await Geoprocessing.ExecuteToolAsync(
                            "CreateFeatureclass_management",
                            parameters,
                            null,
                            null,
                            null,
                            GPExecuteToolFlags.None
                        );

                        if (gpResult.IsFailed)
                            throw new Exception($"No se pudo crear la capa de anotaciones: {gpResult.ErrorMessages}");

                        // Agregar campo Observacion
                        var addFieldParams = Geoprocessing.MakeValueArray(
                            Path.Combine(selectedGdbPath, _featureClassName),
                            "Observacion",
                            "TEXT"
                        );

                        var gpAddField = await Geoprocessing.ExecuteToolAsync(
                            "AddField_management",
                            addFieldParams,
                            null,
                            null,
                            null,
                            GPExecuteToolFlags.None
                        );

                        if (gpAddField.IsFailed)
                            throw new Exception($"No se pudo agregar el campo Observacion: {gpAddField.ErrorMessages}");
                    }
                });

                // 👇 Pedir texto de observación
                var observacion = Microsoft.VisualBasic.Interaction.InputBox(
                    "Ingrese el texto de la observación:",
                    "Nueva Observación",
                    "Escriba aquí...");

                if (string.IsNullOrWhiteSpace(observacion))
                    return false;

                var map = await GetActiveOrFirstMapAsync();

                FeatureLayer targetLayer = null;
                await QueuedTask.Run(() =>
                {
                    targetLayer = map.GetLayersAsFlattenedList()
                                     .OfType<FeatureLayer>()
                                     .FirstOrDefault(fl => fl.Name.Equals(_featureClassName, StringComparison.OrdinalIgnoreCase));

                    if (targetLayer == null)
                        targetLayer = LayerFactory.Instance.CreateLayer(new Uri(_fcPath), map, 0, _featureClassName) as FeatureLayer;
                });

                if (targetLayer == null)
                {
                    MessageBox.Show("No se pudo agregar la capa al mapa.",
                        "Error", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
                    return false;
                }

                // Reproyectar si hace falta
                MapPoint mpForLayer = mp;
                await QueuedTask.Run(() =>
                {
                    var layerSR = targetLayer.GetSpatialReference();
                    if (layerSR != null && !layerSR.Equals(mp.SpatialReference))
                        mpForLayer = (MapPoint)GeometryEngine.Instance.Project(mp, layerSR);
                });

                // Insertar el punto
                await QueuedTask.Run(() =>
                {
                    var att = new Dictionary<string, object>
            {
                { "Observacion", observacion }
            };

                    var op = new EditOperation
                    {
                        Name = "Insertar Observación QC",
                        SelectNewFeatures = false
                    };
                    op.Create(targetLayer, mpForLayer, att);

                    if (!op.Execute())
                        throw new Exception("No se pudo crear la observación.");
                });

                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al crear observación: {ex.Message}",
                    "Error", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
                return false;
            }
        }

        protected override void OnToolKeyDown(ArcGIS.Desktop.Mapping.MapViewKeyEventArgs k)
        {
            if (k.Key == System.Windows.Input.Key.Escape)
            {
                // Liberar el control y volver a la herramienta por defecto (Explore)
                ArcGIS.Desktop.Framework.FrameworkApplication.CurrentTool = "esri_mapping_exploreTool";

                k.Handled = true;
            }

            base.OnToolKeyDown(k);
        }



        private async Task<Map> GetActiveOrFirstMapAsync()
        {
            Map targetMap = null;

            await QueuedTask.Run(() =>
            {
                if (MapView.Active != null)
                {
                    targetMap = MapView.Active.Map;
                }
                else
                {
                    var mapItem = Project.Current.GetItems<MapProjectItem>().FirstOrDefault();
                    if (mapItem != null)
                        targetMap = mapItem.GetMap();
                }
            });

            if (targetMap == null)
                throw new InvalidOperationException("No se encontró ningún mapa en el proyecto.");

            if (MapView.Active == null || MapView.Active.Map != targetMap)
                await ArcGIS.Desktop.Framework.FrameworkApplication.Panes.CreateMapPaneAsync(targetMap);

            return targetMap;
        }
    }
}
