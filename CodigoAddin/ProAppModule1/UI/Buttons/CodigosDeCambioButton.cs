using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Core.Geoprocessing;

namespace ProAppModule1.UI.Buttons
{
    internal class CodigosDeCambioButton : Button
    {
        protected override async void OnClick()
        {
            string aprxPath = Project.Current.URI;

            string projectDirectory = System.IO.Path.GetDirectoryName(aprxPath);

            string toolboxPath = System.IO.Path.Combine(projectDirectory, "Toolboxes", "RevisionCodigosDeCambio.pyt");

            string toolName = "RevisarCodigosCambio";

            string toolFullPath = $"{toolboxPath}\\{toolName}";

            await QueuedTask.Run(() =>
            {
                Geoprocessing.OpenToolDialogAsync($"{toolboxPath}\\{toolName}");
            });
        }
    }
}
