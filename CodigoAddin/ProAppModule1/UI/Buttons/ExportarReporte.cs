using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Extensions;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.KnowledgeGraph;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using ArcGIS.Desktop.Core.Geoprocessing;

namespace ProAppModule1.UI.Buttons
{
    internal class ExportarReporte : Button
    {
        protected override async void OnClick()
        {
            string aprxPath = Project.Current.URI;

            string projectDirectory = System.IO.Path.GetDirectoryName(aprxPath);

            string toolboxPath = System.IO.Path.Combine(projectDirectory, "Toolboxes", "GenerarReporte.pyt");

            string toolName = "GenerarReporte";

            string toolFullPath = $"{toolboxPath}\\{toolName}";

            await QueuedTask.Run(() =>
            {
                Geoprocessing.OpenToolDialogAsync($"{toolboxPath}\\{toolName}");
            });
        }
    }
}
