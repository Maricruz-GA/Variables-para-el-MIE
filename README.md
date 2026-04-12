# Flujo de trabajo par integrar el modelo **3T-EII** 

Exploración de datos y desarrollo de una estrategia de producción del **3T-EII** basada en Python. Incluye la gama completa de tareas para hacer disponibles en forma homogenes datos geoespaciales desde fuentes estadísticas, prospección en el terreno y satelitales. El flujo de trabajo incluye limpieza/preparación, ingesta, procesamiento del modedlo y entrega de los productos cartográficos digitales.

Dentro de la propuesta de workflow hay una carpeta scripts. Ya están ahí todos los scripts que encontré, (**R** y Python), "refactorizados" para una operación **qgis-headless** es decir, no requieren para su ejecución de la interfaz grpafica de QGis. Sí se asume la existencia y operación dentro de un entorno virtual `qgis_env`que contiene las bibliotecas necesarias `qgis.core, geooandas, gdal`, etc.
