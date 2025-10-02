# ArcGIS Pro Add-In: Herramientas de Control de Calidad  

## 📌 Descripción  
Este Add-In para **ArcGIS Pro**, desarrollado en **.NET (C#)**, está diseñado para **automatizar procesos de control de calidad cartográfico** en proyectos de entrega de información geoespacial.  
Incluye además un **proyecto de ArcGIS Pro** y un conjunto de **toolboxes personalizados**, lo que permite integrar todo el flujo de trabajo de validación y reporte en un solo entorno.  

## 🚀 Características  
- **Gestión de entregas de datos**  
  - Exportación y fusión de entregas  
- **Control de calidad automatizado**  
  - Validación de adyacencia entre polígonos  
  - Revisión de áreas mínimas  
  - Validación de cambios lógicos  
  - Revisión de códigos de cambio  
- **Generación automática de reportes**  
- **Anotaciones sobre geodatabases de QA**  
- **Exportación rápida** a Shapefile  
- **Herramientas de contexto** para coberturas fuera de altura o fuera de costa  

## 🛠️ Tecnologías Utilizadas  
- **Lenguaje:** C#  
- **Framework:** .NET (ArcGIS Pro SDK)  
- **Plataforma:** ArcGIS Pro  
- **Toolboxes:** Python / ModelBuilder  
- **Control de versiones:** Git + GitHub  

## 📂 Estructura del Repositorio  
```
/CodigoAddin         -> Proyecto en .NET con el código fuente del Add-In  
/ProyectoArcGISPro   -> Proyecto de ArcGIS Pro con toolboxes y geodatabase de ejemplo  
```  

## 📦 Instalación

### Abrir el proyecto en Visual Studio
- Navegar a la carpeta `/CodigoAddin`
- Abrir el archivo `.sln`
- Verificar dependencias del SDK de ArcGIS Pro

### Compilar el Add-In
- Seleccionar la configuración `Debug` o `Release`
- Compilar y generar el archivo `.esriAddInX`

### Instalar el Add-In en ArcGIS Pro
- Copiar el archivo `.esriAddInX` en la carpeta de complementos de ArcGIS Pro
- Activar el Add-In desde la interfaz del software

### (Opcional) Cargar el proyecto de ejemplo
- Abrir `/ProyectoArcGISPro` en ArcGIS Pro para probar el flujo completo con los toolboxes incluidos

## 📌 Uso del Add-In
1. Abrir el **proyecto de ArcGIS Pro** o cargar tus propios datos  
2. Acceder a la pestaña del Add-In en la cinta de ArcGIS Pro  
3. Seleccionar la herramienta de control de calidad requerida  
4. Ejecutar las validaciones o reportes según el flujo definido  
5. Revisar las anotaciones y resultados generados en la geodatabase  

## 🐛 Reporte de Problemas y Sugerencias
Si encuentras algún error o deseas proponer mejoras, puedes abrir un **issue** en este repositorio de GitHub.  

## 📜 Licencia
Este proyecto está licenciado bajo la **Apache License 2.0**. Para más detalles, consulta el archivo [LICENSE](LICENSE).  

## 📣 Créditos
**Desarrollado por:** Vyper1027

