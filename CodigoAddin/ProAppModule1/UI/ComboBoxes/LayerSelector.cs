using System.IO;
using System.Linq;
using System.Threading.Tasks;
using ArcGIS.Core.Data;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Threading.Tasks;

namespace ProAppModule1.UI.ComboBoxes
{
    internal class QCAnnotationComboBox : ComboBox
    {
        private static string _selectedGdbPath;
        public static string SelectedGdbPath => _selectedGdbPath;

        public QCAnnotationComboBox()
        {
            _ = LoadGdbsAsync();
        }

        protected override void OnDropDownOpened()
        {
            _ = LoadGdbsAsync();
        }

        protected override void OnSelectionChange(ComboBoxItem item)
        {
            if (item is QCComboItem qcItem && qcItem.Enabled)
                _selectedGdbPath = qcItem.Path;
            else
                _selectedGdbPath = null;
        }

        private async Task LoadGdbsAsync()
        {
            Clear();
            QCComboItem firstValid = null;

            var gdbItems = Project.Current.GetItems<GDBProjectItem>();

            foreach (var gdbItem in gdbItems)
            {
                bool isValid = false;

                await QueuedTask.Run(() =>
                {
                    using var gdb = gdbItem.GetDatastore() as Geodatabase;
                    if (gdb != null)
                        isValid = true;
                });

                string gdbPath = gdbItem.Path;
                string gdbName = Path.GetFileName(gdbPath);
                string displayName = isValid ? gdbName : $"{gdbName} (inaccesible)";

                var comboItem = new QCComboItem(displayName, gdbPath, isValid);
                Add(comboItem);

                if (firstValid == null && isValid)
                    firstValid = comboItem;
            }

            // Seleccionar la primera válida
            if (SelectedItem == null && firstValid != null)
            {
                SelectedItem = firstValid.Text;
                _selectedGdbPath = firstValid.Path;
            }
        }
    }

    internal class QCComboItem : ComboBoxItem
    {
        public string Path { get; }
        public bool Enabled { get; }

        public QCComboItem(string display, string path, bool enabled) : base(display)
        {
            Path = path;
            Enabled = enabled;
        }
    }
}
