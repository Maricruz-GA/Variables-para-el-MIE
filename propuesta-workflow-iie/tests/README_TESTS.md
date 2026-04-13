## Guía de Pytest para el Equipo de Desarrollo

Esta guía establece el estándar para las pruebas de nuestros scripts de procesamiento geoespacial.

Podría parecer que una estrategia formal de *testing* es simplemente una tarea extra que quita tiempo y que hacemos por moda o lucimiento. En realidad es el **seguro de vida** del desarrollo. El proyecto que estamos abordando es complejo y desafiante. Es a la ves una oportunidad de aprendizaje y la oportunidad de producir un resultado de gran trascendencia. La ayuda que recursos como Pytest nos ofrecen es bienvenida. 

En la sección 6 de este README se ofrecen algunos argumentos adicionales para apreciar los beneficios y comprender su relevancia. El *testing* es una herramienta de diseño. Un código que es fácil de poner a prueba es, por definición, un código bien escrito: modular, claro y desacoplado. Al adoptar `Pytest`, no solo estamos validando datos geoespaciales; nos estamos comprometiendo con nuestras capacidades hacia la sabiduía de la ingeniería de software.

<br> 

##### Dicho entre los desarrolladores de software:

> *Un código sin pruebas no es código terminado, es solo una propuesta.*


<br>

### 1. Convenciones y Estructura

Para que Pytest funcione sin dar demasiada lata, seguiremos estas reglas:

* **Nombres de archivos:** Deben empezar por `test_` (ej. `test_procesamiento.py`).
* **Nombres de funciones:** Deben empezar por `test_` (ej. `test_calculo_tasas()`).
* **Ubicación:** Todos los tests residen en la carpeta `/tests` en la raíz del proyecto.
* **Importante:** Los scripts a probar **no deben empezar con números** (usa `paso1_crear_csv.py` en lugar de `1_crear_csv.py`) para permitir la importación como módulos.

#### a) Veamos como ejemplo  la función `build_valid_mask`.

Es un caso relativamente puro, sencillo y no requiere *mocks* de datos complejos.

  * Esta función está desarrollada en: `scripts/headless_r2py/s1_crear_csv_reg_tifs.py`. 
  * La prueba está implementada en:    `tests/test_crear_csv.py` 

##### Anatomía de la prueba:

Para concebir una prueba, seguimos este razonamiento mental utilizando el ejemplo de la función `build_valid_mask`:

1.  **Identificar:** ¿Qué hace la función? En este caso, toma un array con datos y una máscara, y debe devolvernos una máscara booleana de los píxeles útiles.
2.  **Producir datos:** Creamos un array pequeño (2x2) "de juguete" donde obviamente conocemos de antemano el resultado.
3.  **Alimentar:** Pasamos esos datos a la función (es lo que hace `from s1_crear_csv_reg_tifs import build_valid_mask`.
4.  **Verificar:** Usamos `assert` para comparar lo que la función entregó contra lo que sabemos debe entregar.

##### Así se ve todo esto en el script de prueba:

```python
def test_build_valid_mask():
    # --- 1. PRODUCIR DATOS DE PRUEBA (Arrange) ---
    # Creamos un escenario controlado: 4 píxeles, uno de ellos marcado como "malo" (True en la máscara)
    data = np.array([[1, 2], [3, 4]])
    mask = np.array([[False, False], [True, False]]) # El píxel (1,0) no es válido
    malla_arr = np.ma.masked_array(data, mask=mask)

    # --- 2. ALIMENTAR A LA FUNCIÓN (Act) ---
    # Ejecutamos la lógica que queremos poner a prueba
    resultado = build_valid_mask(malla_arr, nodata=None)

    # --- 3. VERIFICAR RESULTADOS (Assert) ---
    # Comprobamos que el píxel (0,0) sea True (Válido)
    assert resultado[0, 0] == True 
    # Comprobamos que el píxel (1,0) sea False (Inválido, tal como lo definimos)
    assert resultado[1, 0] == False
```
 

En el proceso de integración del producto final seguimos una lógica secuencial que queda muy bien descrita en esta [pirámide del testing](https://sketchingdev.co.uk/sketchnotes/testing-pyramid.html). Nos sugiere que conviene hacer muchas pruebas de los componentes elementales y progresivamente menos de los que integran partes y muchos menos del comportamiento total del script o del workflow completo .

<img src="https://sketchingdev.co.uk/assets/images/sketchnotes/2021-07-12-testing-pyramid/testing-pyramid.jpg" width="300" fig-align="center">


### 2. El Patrón AAA (Arrange, Act, Assert)

Cada test debe seguir esta estructura lógica para ser legible:

1.  **Arrange (Organizar):** Preparar los datos de entrada y mocks (ej. crear un array de NumPy).
2.  **Act (Actuar):** Ejecutar la función que queremos probar.
3.  **Assert (Afirmar):** Verificar que el resultado es el esperado.

```python
def test_suma_simple():
    # Arrange
    a, b = 1, 2
    # Act
    resultado = suma(a, b)
    # Assert
    assert resultado == 3
```




### 3. Uso de Mocks (Simulación de Datos)

Dado que trabajamos con archivos pesados (Rasters/TIFFs), **nunca** usaremos archivos reales en los tests unitarios. Usaremos `unittest.mock`.

* **¿Por qué?** Los tests deben ser instantáneos y no depender de que existan carpetas de datos en cada PC.
* **Regla de Oro:** Si la función usa `rasterio.open`, usa `@patch("rasterio.open")` para simular el archivo.

### 4. Fixtures: Reutilización de Configuración
Si varios tests necesitan el mismo objeto (como una matriz de transformación `Affine`), usamos una `fixture`:

```python
@pytest.fixture
def transform_estandar():
    return Affine(1.0, 0.0, 500.0, 0.0, -1.0, 1000.0)

def test_un_proceso(transform_estandar):
    # Ya puedes usar transform_estandar aquí
    ...
```

### 5. Comandos Imprescindibles (Terminal)
Ejecuta estos comandos desde la raíz del proyecto:

| Comando | Para qué sirve |
| :--- | :--- |
| `python -m pytest` | Corre todos los tests del proyecto. |
| `pytest -v` | Muestra qué test específico está pasando o fallando. |
| `pytest --lf` | Corre solo los tests que fallaron la última vez (*last failed*). |
| `pytest -x` | Se detiene en el primer error que encuentre. |


### 6. ¿Por qué importa diseñar un kit de pruebas? (Filosofía del Testing)

Si eres nuevo en esto, es normal pensar: *"Si ya corrí el script y generó el CSV, ¿para qué necesito un test?"*. La respuesta no es solo verificar que el código "funciona", sino asegurar que **seguirá funcionando mañana**.

#### a) ¿Qué es lo que realmente pone a prueba Pytest?

No ponemos a prueba la "buena voluntad" del programador, sino los **contratos lógicos** de nuestro código:

* **La Resistencia al Cambio (Refactorización):** Imagina que el próximo mes actualizamos la versión de `rasterio` o cambiamos la forma en que se calcula un índice. ¿Cómo sabemos que no rompimos nada en los 10 scripts anteriores? `Pytest` lo verifica en 3 segundos.
* **El Manejo de Casos Borde (Edge Cases):** ¿Qué pasa si una malla no tiene píxeles válidos? ¿Qué pasa si un Raster tiene un NoData inesperado? Los tests fuerzan estas situaciones para que el código no explote en producción.
* **La Documentación Viva:** Un test es el mejor manual de uso. Si quieres saber qué formato de entrada espera una función, mira su test. Ahí verás un ejemplo real de qué entra y qué debe salir.

#### b) Pytest como ayuda para *Dormir Tranquilo*

Programar sin tests es como construir un edificio y esperar que no se caiga porque "se ve firme". Programar con tests es ponerle sensores de movimiento a cada viga.
  
> **Regla de oro para el equipo:**

> "Un bug que aparece es un test que faltó. Cuando arregles un error, escribe un test que cubra ese caso para que **ese mismo error** no vuelva a nacer nunca más."

#### c) El concepto de "Unidad"

En nuestro flujo de trabajo, Pytest pone a prueba **unidades mínimas de verdad** (es la colección de `assert` en módulo de prueba):

* No probamos "todo el workflow" de una vez (eso es muy pesado).
* Probamos si la función que genera la máscara lo hace bien.
* Probamos si la función que lee el ID de la malla extrae el número correcto.
* 
Si todas las piezas pequeñas son sólidas, el workflow completo será indestructible.


#### 4. ¿Cómo profundizar? (Ruta de aprendizaje)

**Pytest** es un ecosistema profundo. No esperamos que lo domines hoy, pero estos recursos son el mapa para cuando necesites escalar tus pruebas:

* **Integración con PyCharm (si te decidiste a usarlo):** PyCharm facilita el *testing* enormemente. 
    * Ve a *Settings > Tools > Python Integrated Tools* y selecciona **pytest** como el "Default test runner". 
    * Esto te permitirá ver iconos de "Play" verdes al lado de cada función `test_`. Al hacer clic, verás los resultados en una ventana organizada en la parte inferior.
* **Documentación Oficial ([docs.pytest.org](https://docs.pytest.org/)):** Es la fuente definitiva. Si tienes duda sobre cómo usar una función específica de `pytest`, busca aquí primero.
* **Libro "Python Testing with pytest" (Brian Okken):** Es la referencia más clara que existe sobre el tema. Explica desde lo más básico hasta cómo manejar bases de datos en los tests.
* **Canal de YouTube "ArjanCodes":** Tiene vídeos excelentes sobre cómo estructurar código para que sea fácil de probar (arquitectura de software).


#### 5. Consejos para quién está iniciando:

1.  **No le tengas miedo al rojo:** Ver un `FAILED` en la terminal no es un fracaso, es Pytest avisándote de un error *antes* de que lo vea el cliente o el jefe. El rojo es tu amigo.
2.  **Escribe el test mientras programas:** No lo dejes para el final. Si escribes la prueba al mismo tiempo que la función, diseñarás código más limpio y modular (porque el código "enredado" es muy difícil de testear).
3.  **Simular no es engañar:** Usar Mocks es necesario. No queremos procesar 2GB de datos para saber si una suma funciona. Nos ayuda a ser eficientes y prepararnos para enfrentar los daros reales.


##### Visualiza el flujo conceptual

* **Test Unitario:** Prueba un tornillo (una función).
* **Test de Integración:** Prueba que dos piezas encajen (como el test para probar `process_one_malla` de `s1_crear_csv_reg_tifs.py`).
* **Workflow:** Es el motor completo funcionando.

##### Tips para aspectos geoespaciales

* **Validación de coordenadas:** Usa `np.isclose()` en lugar de `==` para comparar coordenadas (evita conflicros por decimales del punto flotante).
* **Tipos de datos:** Si una librería (como `Rasterio`) pide un tipo específico, asegúrate de que tu Mock devuelva un objeto real de esa misma y exacta  clase.
