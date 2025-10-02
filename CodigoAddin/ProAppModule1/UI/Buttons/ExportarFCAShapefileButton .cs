using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;

namespace ProAppModule1.UI.Buttons
{
    internal class ExportarFCAShapefileButton : Button
    {
        protected override async void OnClick()
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

                var gdbName = Path.GetFileNameWithoutExtension(selectedGdbPath);
                var fcName = $"CC_{gdbName}"; // 👈 Feature class esperado
                var fcPath = Path.Combine(selectedGdbPath, fcName);

                bool exists = false;

                await ArcGIS.Desktop.Framework.Threading.Tasks.QueuedTask.Run(() =>
                {
                    using var gdb = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(selectedGdbPath)));
                    exists = gdb.GetDefinitions<FeatureClassDefinition>()
                                .Any(fc => fc.GetName().Equals(fcName, StringComparison.OrdinalIgnoreCase));
                });

                if (!exists)
                {
                    MessageBox.Show($"No se encontró la capa {fcName} en la geodatabase seleccionada.",
                        "Error", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
                    return;
                }

                // Abrir la herramienta "Feature Class to Shapefile"
                var parameters = Geoprocessing.MakeValueArray(
                    new string[] { fcPath }, // Input Features (array aunque sea 1)
                    Environment.GetFolderPath(Environment.SpecialFolder.Desktop) // Default salida (puedes ajustarlo)
                );

                Geoprocessing.OpenToolDialog("FeatureClassToShapefile_conversion", parameters);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al exportar: {ex.Message}",
                    "Error", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }
    }
}
