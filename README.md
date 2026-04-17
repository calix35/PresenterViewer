# Presenter Viewer

**Manual de uso y preparación de presentaciones**

Presenter Viewer es un visor de presentaciones para el expositor, pensado para trabajar con PDFs académicos o profesionales, incluyendo soporte para *notes* de Beamer, *pnotes*, paneles configurables y herramientas interactivas en vivo.

---

## Índice

- [1. Visión general](#1-visión-general)
  - [¿Qué es Presenter Viewer?](#qué-es-presenter-viewer)
  - [¿Para qué sirve?](#para-qué-sirve)
  - [Flujo de trabajo general](#flujo-de-trabajo-general)
- [2. Instalación y ejecución](#2-instalación-y-ejecución)
  - [Requisitos](#requisitos)
  - [Clonar el repositorio](#clonar-el-repositorio)
  - [Crear y activar un entorno virtual](#crear-y-activar-un-entorno-virtual)
  - [Instalar dependencias desde `requirements.txt`](#instalar-dependencias-desde-requirementstxt)
  - [Instalación del proyecto en modo editable](#instalación-del-proyecto-en-modo-editable)
  - [Ejecución de la aplicación](#ejecución-de-la-aplicación)
  - [Comportamiento al iniciar](#comportamiento-al-iniciar)
  - [Abrir un PDF manualmente](#abrir-un-pdf-manualmente)
  - [Soporte de drag & drop](#soporte-de-drag--drop)
- [3. Uso básico del visor](#3-uso-básico-del-visor)
  - [Interfaz principal](#interfaz-principal)
  - [Barra de herramientas](#barra-de-herramientas)
  - [Distribución de paneles](#distribución-de-paneles)
  - [Etiquetas de panel](#etiquetas-de-panel)
  - [Abrir un PDF](#abrir-un-pdf)
  - [Navegación básica](#navegación-básica)
  - [Configuración de paneles](#configuración-de-paneles)
  - [Persistencia del layout](#persistencia-del-layout)
  - [Selección de panel](#selección-de-panel)
  - [Control del proyector](#control-del-proyector)
- [4. Teclas y herramientas](#4-teclas-y-herramientas)
  - [Navegación con teclado](#navegación-con-teclado)
  - [Tipos de panel](#tipos-de-panel)
  - [Uso de paneles duplicados](#uso-de-paneles-duplicados)
  - [Atajos para paneles](#atajos-para-paneles)
  - [Personalización del layout](#personalización-del-layout)
  - [Modos principales](#modos-principales)
  - [Uso del puntero](#uso-del-puntero)
  - [Dibujo sobre la presentación](#dibujo-sobre-la-presentación)
  - [Uso del borrador](#uso-del-borrador)
  - [Spotlight](#spotlight)
  - [Selección y zoom](#selección-y-zoom)
  - [Cronómetro](#cronómetro)
  - [Control del proyector desde teclado](#control-del-proyector-desde-teclado)
  - [Interfaz y control general](#interfaz-y-control-general)
  - [Resumen de atajos clave](#resumen-de-atajos-clave)
- [5. Preparación del PDF](#5-preparación-del-pdf)
  - [Preparación desde LaTeX](#preparación-desde-latex)
  - [Configuración mínima recomendada](#configuración-mínima-recomendada)
  - [Uso de `\note{}`](#uso-de-note)
  - [Agregar `\pnote`](#agregar-pnote)
  - [Notes vs Pnotes](#notes-vs-pnotes)
  - [PDFs sin panel de notas](#pdfs-sin-panel-de-notas)
  - [Buenas prácticas](#buenas-prácticas)
- [6. Buenas prácticas de exposición](#6-buenas-prácticas-de-exposición)
  - [Diseño](#diseño)
  - [Uso del visor](#uso-del-visor)
  - [Preparación antes de exponer](#preparación-antes-de-exponer)
  - [Checklist antes de iniciar](#checklist-antes-de-iniciar)
- [7. Flujo recomendado](#7-flujo-recomendado)
  - [Flujo completo](#flujo-completo)
  - [Flujo paso a paso](#flujo-paso-a-paso)
  - [Errores comunes](#errores-comunes)
  - [Cierre](#cierre)
  - [Referencia de inspiración](#referencia-de-inspiración)

---

# 1. Visión general

## ¿Qué es Presenter Viewer?

Presenter Viewer es un **visor de presentaciones para el expositor** diseñado para trabajar cómodamente con PDFs académicos o profesionales, mostrando en una sola interfaz la información que el ponente necesita durante la exposición.

Sus objetivos principales son:

- visualizar la **filmina actual**;
- consultar la **siguiente filmina**;
- mostrar **notes** exportadas desde Beamer;
- integrar **pnotes** como apoyo breve y táctico;
- ofrecer herramientas interactivas para presentar en vivo.

> **Idea clave:** no es solo un lector de PDF. Busca ofrecer **control total de la presentación** sin que el público vea la lógica interna del expositor.

## ¿Para qué sirve?

Presenter Viewer puede utilizarse en distintos contextos:

### Clases
Permite exponer con notes, cronómetro, navegación visual y apoyo privado.  
Es útil en cursos, laboratorios, demostraciones y sesiones híbridas.

### Conferencias
Facilita mantener ritmo, foco visual y separación limpia entre presentador y proyector.  
Es especialmente valioso cuando hay dos pantallas o proyector externo.

### Defensas
Ayuda a resaltar detalles, controlar tiempos y conservar recordatorios discretos.  
Resulta muy útil en tesis, coloquios, seminarios y presentaciones técnicas.

### Ensayos
Sirve como entorno realista de práctica antes de la exposición formal.  
Permite validar flujo, herramientas, layout y tiempo de intervención.

## Flujo de trabajo general

El flujo recomendado de uso es:

**LaTeX → PDF → Presenter Viewer → Configurar paneles → Presentar**

En términos prácticos:

1. Crear la presentación en Beamer.
2. Exportar el PDF final.
3. Abrirlo en Presenter Viewer.
4. Ajustar paneles y herramientas.
5. Conectar el proyector o segunda pantalla.
6. Exponer con control del flujo.

> **Objetivo:** separar claramente la **vista del presentador** de la **salida del público**.

---

# 2. Instalación y ejecución

## Requisitos

Antes de ejecutar Presenter Viewer, conviene contar con:

- Python 3.x
- dependencias del proyecto instaladas
- un entorno gráfico compatible con PyQt
- un archivo PDF listo para abrir

> **Recomendación:** trabaja dentro de un entorno virtual para mantener las dependencias aisladas y evitar conflictos con otras instalaciones de Python.

## Clonar el repositorio

```bash
git clone https://github.com/calix35/PresenterViewer.git
cd presenter_viewer
```

> **Buena práctica:** mantén el proyecto en una carpeta dedicada para ubicar fácilmente `samples`, `images` y los archivos PDF de prueba.

## Crear y activar un entorno virtual

### Crear el entorno

```bash
python -m venv .venv
```

### Activar en Windows

```bash
.venv\Scripts\activate
```

### Activar en Linux/macOS

```bash
source .venv/bin/activate
```

> Conviene activar el entorno antes de instalar dependencias o ejecutar la aplicación.

## Instalar dependencias desde `requirements.txt`

```bash
python -m pip install -r requirements.txt
```

Entre las dependencias debe encontrarse **PyQt** o la variante de Qt usada por el proyecto, ya que la interfaz gráfica depende de ella.

### ¿Por qué usar `requirements.txt`?

Porque permite reproducir el entorno exacto necesario para ejecutar Presenter Viewer en otra computadora.

## Instalación del proyecto en modo editable

La forma recomendada para trabajar durante desarrollo es:

```bash
python -m pip install -e .
```

Esto ofrece varias ventajas:

- registra el comando `presenter-viewer`;
- facilita ejecutar la aplicación como programa;
- permite modificar el código sin reinstalar todo cada vez.

## Ejecución de la aplicación

### Comando principal

```bash
presenter-viewer
```

### Abrir un PDF directamente

```bash
presenter-viewer archivo.pdf
```

### Alternativa

```bash
python -m presenter_viewer.main
```

> Conviene iniciar primero con un PDF de prueba para verificar la detección de notes y paneles.

## Comportamiento al iniciar

Los escenarios habituales son:

- si se pasa un PDF al iniciar, la aplicación lo abre automáticamente;
- si no se pasa PDF, puede intentar cargar un archivo de ejemplo;
- si no existe un ejemplo, la ventana queda lista para abrir un archivo manualmente.

> **Recomendación:** antes de una exposición real, abre explícitamente el PDF final y confirma que cargó correctamente.

## Aplicación iniciada sin PDF

![Aplicación iniciada sin PDF](samples/images/startup-empty.png)

Cuando la aplicación se abre sin archivo cargado, normalmente debería verse:

- ventana principal activa;
- paneles vacíos o en espera;
- controles disponibles;
- opción clara para abrir un archivo.

Esto indica que la aplicación está lista para trabajar, aunque todavía no se haya cargado ningún PDF.

## Aplicación iniciada con PDF cargado

![Aplicación iniciada con PDF cargado](samples/images/startup-loaded.png)

Cuando ya se abrió un documento, conviene verificar que aparezcan correctamente:

- la filmina actual;
- los paneles auxiliares;
- las notas, si el PDF las incluye;
- la interfaz lista para presentar.

> **Verificación rápida:** revisa de inmediato si el archivo fue detectado como PDF normal o como PDF con notes.

## Abrir un PDF manualmente

Hay varias formas de abrir un PDF:

- desde el botón o menú de abrir archivo;
- con atajo de teclado;
- arrastrando el archivo PDF a la ventana.

### Atajo sugerido

- **Ctrl+O** en Windows y Linux
- **Cmd+O** en macOS

Esto permite abrir rápidamente un PDF incluso aunque la aplicación haya iniciado sin archivo.

## Soporte de drag & drop

Presenter Viewer también puede admitir arrastrar y soltar archivos PDF directamente sobre la ventana.

### Ventajas

- agiliza la apertura;
- evita navegar por cuadros de diálogo;
- hace más natural el uso en escritorio.

> El archivo debe ser un PDF válido y conviene verificar de inmediato si se detectó como PDF normal o como PDF con notes.

---

# 3. Uso básico del visor

## Interfaz principal

![Interfaz principal](samples/images/presenter-view.png)

La ventana principal del presentador concentra varios elementos importantes:

- panel principal con la filmina actual;
- paneles auxiliares;
- barra inferior de estado;
- herramientas activas;
- cronómetro y controles.

> **Idea clave:** el presentador ve múltiples elementos, pero el público solo ve la filmina.

## Barra de herramientas

![Barra de herramientas](samples/images/toolbar.png)

La barra superior reúne varias acciones frecuentes, por ejemplo:

- abrir PDF;
- navegación básica;
- modos de interacción;
- acceso rápido a funciones clave.

Su objetivo es concentrar las acciones más usadas durante la presentación.

## Distribución de paneles

Una distribución recomendada es la siguiente:

- panel grande: filmina actual;
- panel superior derecho: siguiente;
- panel medio derecho: notas actuales;
- panel inferior derecho: notas siguientes.

Esto no es obligatorio, pero sí suele ser el layout más natural para presentar.

## Etiquetas de panel

![Etiquetas de panel](samples/images/presenter-labels.png)

Las etiquetas de panel ayudan a:

- identificar cada panel;
- validar configuración;
- evitar errores antes de exponer.

> **Recomendación:** actívalas al inicio y desactívalas antes de presentar.

## Abrir un PDF

![Abrir un PDF](samples/images/open-pdf.png)

Al abrir un documento, normalmente ocurre lo siguiente:

- se carga el documento;
- se asignan paneles automáticamente;
- se detectan notes si existen;
- se habilita la navegación.

> **Importante:** verifica si el PDF fue interpretado correctamente, con o sin notes.

## Navegación básica

La navegación debe sentirse **rápida, natural y sin distracciones**.  
En la práctica, esto implica:

- avanzar y retroceder entre páginas;
- revisar la siguiente filmina;
- saltar al inicio o final;
- mantener el ritmo de exposición.

## Configuración de paneles

![Configuración de paneles](samples/images/panel-context-menu.png)

Los paneles pueden configurarse para mostrar distintos tipos de contenido:

- filmina actual;
- siguiente;
- notas actuales;
- notas siguientes.

Esto permite adaptar el entorno al estilo de trabajo del expositor.

## Persistencia del layout

Presenter Viewer guarda automáticamente la distribución de paneles en un archivo de configuración:

```text
layout.json
```

Este archivo:

- almacena la configuración de paneles;
- guarda posiciones y contenidos;
- permite restaurar el layout al reiniciar.

### Ubicación típica

Usualmente se crea en el directorio de trabajo del usuario o en la carpeta del proyecto:

```text
./layout.json
```

### Consejos útiles

- se genera automáticamente;
- se sobrescribe al cambiar el layout;
- puede eliminarse para reiniciar la configuración.

> Si algo se rompe visualmente, eliminar este archivo puede restaurar el comportamiento por defecto.

## Selección de panel

El sistema permite trabajar con un **panel seleccionado** para aplicar acciones específicas.

Esto sirve para:

- cambiar contenido de un panel;
- ajustar layout;
- trabajar con teclado de forma precisa.

## Control del proyector

![Vista del presentador y proyector](samples/images/open-pdf.png)
![Salida del proyector](samples/images/projector-view.png)

El concepto clave es que el presentador y la audiencia ven cosas distintas.

- el presentador conserva paneles, notes y herramientas;
- el público solo debe ver la salida limpia del proyector.

> **Importante:** el público nunca debe ver notas ni paneles auxiliares.

---

# 4. Teclas y herramientas

## Navegación con teclado

### Avanzar
`Right` · `Space` · `Down` · `PageDown`

### Retroceder
`Left` · `Backspace` · `Up` · `PageUp`

### Inicio y final
`Home` · `End`

Este es el mínimo indispensable para controlar una presentación sin usar el mouse.

## Tipos de panel

![Tipos de panel](samples/images/presenter-labels.png)

Los paneles disponibles son:

- filmina actual;
- siguiente filmina;
- notas actuales;
- notas siguientes.

Cada panel puede mostrar contenido diferente al mismo tiempo.

## Uso de paneles duplicados

El visor permite asignar el mismo tipo de contenido a múltiples paneles.

Ejemplos:

- ver varias copias de la filmina actual;
- mostrar notes en más de un panel;
- crear layouts personalizados;
- adaptar el entorno al estilo del expositor.

## Atajos para paneles

### Seleccionar panel
`Ctrl/Cmd + 1` · `Ctrl/Cmd + 2` · `Ctrl/Cmd + 3` · `Ctrl/Cmd + 4`

### Asignar contenido
`Alt/Option + 1` · `Alt/Option + 2` · `Alt/Option + 3` · `Alt/Option + 4`

Flujo típico:

**Seleccionar panel → Asignar contenido**

## Personalización del layout

### Modo customize
`Shift + C`

### Mostrar etiquetas
`L`

Esto permite:

- reorganizar paneles;
- visualizar etiquetas;
- ajustar el entorno de trabajo.

> **Recomendación:** configura el layout antes de la presentación, no durante.

## Modos principales

### Cambiar de modo
`1` normal · `2` pointer · `3` pen · `4` eraser · `5` spotlight

### Qué hace cada modo

- **Normal:** navegación general
- **Pointer:** señalar elementos
- **Pen:** dibujar
- **Eraser:** borrar trazos
- **Spotlight:** enfocar una zona

## Uso del puntero

![Uso del puntero](samples/images/pointer.png)

El puntero sirve para:

- señalar elementos;
- guiar la atención;
- enfatizar detalles.

> **Evitar:** movimiento constante sin intención.

## Dibujo sobre la presentación

![Dibujo sobre la presentación](samples/images/drawing-tools.png)

El modo **pen** puede utilizarse para:

- subrayar;
- explicar;
- resolver en vivo.

### Controles principales

- `3` → activar pen
- `+` / `-` → aumentar o disminuir el grosor del trazo
- `C` → limpiar todo
- `D` → mostrar u ocultar dibujos

## Uso del borrador

![Uso del borrador](samples/images/eraser.png)

El modo **eraser** permite:

- eliminar trazos;
- hacer correcciones;
- limpiar zonas específicas.

### Diferencia importante

- **Eraser** borra parcialmente
- `C` limpia todo

### Controles principales

- `4` → activar eraser
- `+` / `-` → aumentar o disminuir el tamaño del borrador

## Spotlight

El spotlight enfoca una zona y oscurece el resto.

Se recomienda para:

- explicar una región concreta;
- guiar la atención;
- mejorar claridad visual.

> Úsalo solo cuando sea necesario.

## Selección y zoom

![Selección y zoom](samples/images/zoom-selection.png)

Flujo típico:

1. Seleccionar un área
2. Aplicar zoom
3. Salir con `Esc`

### Atajo de zoom
Seleccionar → `Z` → aplicar → `Esc`

## Cronómetro

### Controles
- `T` → iniciar o pausar
- `Shift + T` → reiniciar

### Para qué sirve
- controlar tiempo;
- ajustar ritmo;
- evitar excederse.

> **Consejo:** ensaya con cronómetro activo.

## Control del proyector desde teclado

### Black
`B`

### Freeze
`F`

Permite:

- ocultar pantalla;
- congelar imagen;
- controlar atención.

## Interfaz y control general

- `H` → ayuda
- `W` → fullscreen
- `P` → pnotes
- `Esc` → salir o cancelar acciones

## Resumen de atajos clave

Conviene memorizar al menos esto:

`← →` · `1-5` · `+/-` · `T` · `B` · `F` · `Esc`

> **Idea final:** puedes presentar completamente sin usar el mouse.

---

# 5. Preparación del PDF

## Preparación desde LaTeX

Para aprovechar completamente Presenter Viewer, el PDF debe prepararse correctamente desde LaTeX.

Esto implica:

- usar Beamer;
- separar contenido y notas;
- mantener compatibilidad con notes y pnotes;
- exportar el PDF adecuadamente.

> El visor funciona mejor cuando el PDF fue diseñado pensando en el presentador.

## Configuración mínima recomendada

```latex
\documentclass[aspectratio=169]{beamer}
\usepackage{pdfcomment}
\setbeameroption{show notes on second screen=left}
```

### ¿Qué logra esta configuración?

- activa exportación de notes;
- genera un layout compatible con el visor;
- separa slide y notas en el PDF.

> **Importante:** sin esta configuración, las notes no aparecerán como panel separado.

## ¿Qué hace esta configuración?

El PDF generado normalmente queda con esta lógica:

- lado izquierdo: notes;
- lado derecho: filmina;
- layout ancho tipo presentador.

Eso permite que el visor separe automáticamente ambas partes.

## Uso de `\note{}`

Ejemplo:

```latex
\begin{frame}{Mi filmina}
Contenido visible para el publico.
\note{Esta nota solo la ve el presentador.}
\end{frame}
```

### Ventajas

- no se muestra al público;
- aparece en el panel de notes;
- sirve como guía del expositor.

## Ejemplo con notes

Una filmina pública puede mostrar solo el contenido esencial, mientras que las notes complementan con:

- recordatorios;
- estructura del discurso;
- respuestas sugeridas;
- puntos de transición.

El público ve solo la filmina, pero el expositor conserva el apoyo privado.

## Agregar `\pnote`

Definición sugerida:

```latex
\newcommand{\pnote}[1]{%
  \pdfcomment[
    icon=Note,
    open=false,
    subject={Presenter Note},
    color={1 1 0},
    opacity=0
  ]{#1}%
}
```

> Debe agregarse en el preámbulo del archivo.

## Uso de `\pnote{}`

Ejemplo:

```latex
Explicación importante.
\pnote{Recordar dar ejemplo practico.}
```

### Cuándo conviene

- recordatorios breves;
- notas tácticas;
- apoyo rápido durante exposición.

> `\pnote` complementa a `\note`, no lo reemplaza.

## Notes vs Pnotes

| Método | Ventajas | Uso |
|---|---|---|
| `\note` | Integración completa con Beamer | Notas amplias y estructuradas |
| `\pnote` | Ligero y flexible | Recordatorios breves |

### Recomendación
Usar ambos en conjunto.

## PDFs sin panel de notas

Si el PDF no tiene notes, el visor debe mostrar la página completa.

Esto implica:

- no recortar contenido;
- mostrar PDF normal;
- seguir permitiendo pnotes.

> **Importante:** no todos los PDFs requieren notes.

## Buenas prácticas

- una idea por diapositiva;
- evitar saturar texto;
- usar notes como apoyo;
- priorizar claridad visual;
- ensayar con el visor.

> Un buen PDF es tan importante como el visor.

---

# 6. Buenas prácticas de exposición

## Diseño

- una idea principal por diapositiva;
- texto mínimo y bien espaciado;
- contraste adecuado;
- prioridad a lo visual;
- evitar saturar la slide.

> **Regla simple:** si una diapositiva tiene demasiado texto, probablemente debe dividirse.

## Uso del visor

- usar pointer solo cuando sea necesario;
- usar spotlight para guiar la atención;
- evitar cambiar constantemente de modo;
- limpiar dibujos cuando ya no se necesiten;
- mantener consistencia en el layout.

> El visor debe apoyar la exposición, no distraer.

## Preparación antes de exponer

- ensayar con el PDF final;
- validar notes y pnotes;
- configurar paneles;
- probar herramientas;
- verificar el proyector.

> **Consejo:** no pruebes cosas nuevas en vivo.

## Checklist antes de iniciar

Antes de comenzar, verifica lo siguiente:

- PDF listo
- Presenter Viewer abierto
- paneles configurados
- proyector funcionando
- notes visibles correctamente
- cronómetro listo

> Haz esta revisión antes de estar frente al público.

---

# 7. Flujo recomendado

## Flujo completo

**LaTeX → PDF → Presenter Viewer → Configurar → Presentar**

Resumen práctico:

- crear la presentación en Beamer;
- exportar a PDF;
- abrir en Presenter Viewer;
- configurar paneles y herramientas;
- realizar la exposición.

## Flujo paso a paso

1. Crear la presentación en LaTeX con Beamer.
2. Agregar `\note{}` para notas extensas.
3. Agregar la macro `\pnote{}` al preámbulo.
4. Insertar pnotes donde hagan falta recordatorios rápidos.
5. Compilar el PDF final.
6. Abrir el archivo en Presenter Viewer.
7. Configurar layout y paneles.
8. Probar herramientas como pointer, pen y zoom.
9. Ensayar la presentación completa.

> **Consejo práctico:** haz al menos un ensayo completo antes de la presentación real.

## Errores comunes

- no probar el PDF antes de exponer;
- depender solo de memoria y no usar notes;
- saturar slides con demasiado texto;
- abusar de herramientas visuales;
- no verificar el proyector o segunda pantalla;
- improvisar configuración en vivo.

> La mayoría de errores no son técnicos, sino de preparación.

## Cierre

Presenter Viewer es una herramienta que puede mejorar significativamente la calidad de una exposición cuando se usa correctamente.

Sus principales fortalezas son:

- mejora el control del expositor;
- separa contenido público y privado;
- facilita el uso de herramientas visuales;
- ayuda a mantener ritmo y claridad.

> La herramienta no reemplaza una buena presentación, pero sí la potencia.

## Referencia de inspiración

La organización funcional de esta herramienta toma inspiración de soluciones como `pdfpc`, especialmente en:

- vista del presentador;
- manejo de notas;
- pointer y spotlight;
- herramientas de dibujo;
- cronómetro;
- control del proyector.

La intención aquí es ofrecer una versión moderna, extensible y adaptada a flujos actuales.
