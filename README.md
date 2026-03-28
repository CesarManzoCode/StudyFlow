# StudyFlow

StudyFlow es una aplicación web local que te ayuda a convertir tareas de Moodle en un plan de trabajo claro y manejable.

En lugar de estar saltando entre Moodle, fechas de entrega, descripciones de tareas y herramientas de chat con IA, StudyFlow pone todo en un flujo simple:

1. sincronizar tus tareas pendientes desde Moodle
2. abrir una tarea
3. pedir ayuda a la IA
4. obtener una checklist estructurada que realmente puedas seguir

Este proyecto está pensado para usuarios finales que quieren menos fricción al organizar trabajo académico, no para equipos que gestionan integraciones empresariales con LMS.

## Qué Problema Resuelve

Moodle es útil, pero en el uso diario suele crear un problema muy específico:

- las tareas están dispersas entre cursos
- es fácil perder de vista las fechas límite
- las descripciones de actividades suelen ser largas o poco claras
- todavía tienes que traducir manualmente "lo que dice Moodle" a "lo que debo hacer ahora"
- si usas IA por separado, tienes que copiar y pegar contexto cada vez

StudyFlow resuelve eso conectándose directamente con Moodle, listando tus tareas pendientes y generando ayuda específica para cada actividad a partir de la propia tarea.

## Por Qué Usar StudyFlow

StudyFlow es útil si quieres:

- un solo lugar para ver tareas pendientes
- una forma más rápida de entender qué está pidiendo cada actividad
- una checklist práctica en lugar de una respuesta vaga de IA
- un flujo local donde tu configuración se queda en tu propia máquina
- una herramienta ligera enfocada en ejecutar tareas como estudiante, no en sobrecarga de gestión de proyectos

## Qué Puedes Hacer Con Él

- cargar tus tareas pendientes de Moodle
- revisar cada tarea en una vista de detalle más limpia
- pedir ayuda a la IA sobre una tarea específica
- obtener una respuesta con:
  - resumen
  - entregable
  - pasos
  - advertencias
  - preguntas por aclarar
  - checklist final
- guardar tu configuración de Moodle y del proveedor de IA desde el navegador

## Para Quién Es

StudyFlow está diseñado para:

- estudiantes que usan Moodle activamente
- personas a las que les cuesta convertir el texto de una actividad en un plan de acción
- usuarios que quieren ayuda de IA sin tener que volver a explicar la tarea manualmente cada vez

Es especialmente útil cuando tienes varias actividades pendientes y quieres un flujo más guiado que simplemente revisar Moodle directamente.

## Para Quién No Es

StudyFlow probablemente no es la mejor opción si:

- no usas Moodle
- quieres funciones colaborativas para equipos
- quieres sincronización con calendario, recordatorios o notificaciones móviles
- necesitas un panel en la nube compartido entre varios usuarios
- quieres que la IA haga el trabajo por ti en lugar de ayudarte a entenderlo y ejecutarlo

## Idea Principal

StudyFlow no intenta reemplazar Moodle.

Resuelve la distancia entre:

- "la tarea existe en Moodle"
- y
- "sé exactamente qué hacer después"

Ese es el valor central del programa.

## Guía de Instalación

Esta sección está escrita para usuarios finales, no para desarrolladores.

Si vas a instalar StudyFlow por primera vez, sigue los pasos exactamente en orden.

### Antes de Empezar

Necesitas:

- una cuenta de Moodle
- conexión a internet
- Python instalado en tu computadora
- Git instalado en tu computadora
- una cuenta de proveedor de IA si quieres usar ayuda en la nube

Si quieres una configuración de IA más local, puedes usar Ollama en lugar de un proveedor en la nube.

## Instalación en Windows

### 1. Instalar Python

- Ve al sitio oficial de Python
- Descarga Python 3.12 o una versión más nueva
- Durante la instalación, asegúrate de marcar **Add Python to PATH**

### 2. Instalar Git

- Ve al sitio oficial de Git
- Descarga e instala Git para Windows

### 3. Clonar el proyecto

Abre **Command Prompt** o **PowerShell** y ejecuta:

```powershell
git clone https://github.com/CesarManzoCode/StudyFlow.git
cd StudyFlow
```

### 4. Crear el entorno local de Python

Ejecuta:

```powershell
py -m venv .venv
```

### 5. Activar el entorno

Ejecuta:

```powershell
.venv\Scripts\activate
```

Después de esto, tu terminal debería mostrar algo como `(.venv)` al inicio de la línea.

### 6. Instalar las dependencias de la aplicación

Ejecuta:

```powershell
pip install -e .
```

### 7. Instalar el navegador usado para sincronizar Moodle

Ejecuta:

```powershell
playwright install chromium
```

Si `playwright` no es reconocido, ejecuta:

```powershell
.venv\Scripts\playwright install chromium
```

### 8. Crear tu archivo `.env`

Ejecuta:

```powershell
copy .env.example .env
```

Esto crea tu archivo personal de configuración.

### 9. Editar tu archivo `.env`

Abre `.env` con Notepad o con otro editor de texto y llena tus valores reales:

```env
# --- Moodle ---
MOODLE_BASE_URL=https://your-moodle-site.example
MOODLE_USERNAME=your_username
MOODLE_PASSWORD=your_password
MOODLE_HEADLESS=true

# --- LLM ---
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
LLM_LANGUAGE=Spanish
LLM_BASE_URL=
LLM_API_KEY=your_api_key_here

# --- App ---
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=false
```

Si usas Ollama en lugar de OpenAI, una configuración típica se ve así:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:latest
LLM_LANGUAGE=Spanish
LLM_BASE_URL=http://localhost:11434
LLM_API_KEY=
```

### 10. Iniciar la aplicación

Ejecuta:

```powershell
python scripts/run.py
```

### 11. Abrir la aplicación en tu navegador

Abre:

```text
http://127.0.0.1:8000
```

## Instalación en Linux

### 1. Asegúrate de que Python y Git estén instalados

En muchos sistemas Linux ya vienen instalados.

Si no los tienes, instálalos con el gestor de paquetes de tu distribución.

Ejemplos:

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install git python3 python3-venv
```

Arch Linux:

```bash
sudo pacman -S git python
```

### 2. Clonar el proyecto

Abre una terminal y ejecuta:

```bash
git clone https://github.com/CesarManzoCode/StudyFlow.git
cd StudyFlow
```

### 3. Crear el entorno local de Python

Ejecuta:

```bash
python -m venv .venv
```

### 4. Activar el entorno

Ejecuta:

```bash
source .venv/bin/activate
```

Después de esto, tu terminal debería mostrar algo como `(.venv)`.

### 5. Instalar las dependencias de la aplicación

Ejecuta:

```bash
pip install -e .
```

### 6. Instalar el navegador usado para sincronizar Moodle

Ejecuta:

```bash
playwright install chromium
```

Si hace falta, también puedes ejecutar:

```bash
.venv/bin/playwright install chromium
```

### 7. Crear tu archivo `.env`

Ejecuta:

```bash
cp .env.example .env
```

### 8. Editar tu archivo `.env`

Abre `.env` en un editor de texto y reemplaza los valores de ejemplo con tus valores reales.

Puedes usar:

```bash
nano .env
```

o

```bash
code .env
```

Si usas OpenAI, un `.env` típico se ve así:

```env
# --- Moodle ---
MOODLE_BASE_URL=https://your-moodle-site.example
MOODLE_USERNAME=your_username
MOODLE_PASSWORD=your_password
MOODLE_HEADLESS=true

# --- LLM ---
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
LLM_LANGUAGE=Spanish
LLM_BASE_URL=
LLM_API_KEY=your_api_key_here

# --- App ---
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=false
```

Si usas Ollama:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:latest
LLM_LANGUAGE=Spanish
LLM_BASE_URL=http://localhost:11434
LLM_API_KEY=
```

### 9. Iniciar la aplicación

Ejecuta:

```bash
python scripts/run.py
```

### 10. Abrir la aplicación en tu navegador

Abre:

```text
http://127.0.0.1:8000
```

## Primer Uso Después de la Instalación

Una vez que la aplicación esté abierta:

1. ve al dashboard
2. haz clic en **Refresh tasks**
3. espera a que termine la sincronización con Moodle
4. haz clic en una de tus tareas
5. pide ayuda a la IA si la necesitas

## Uso Diario

StudyFlow sigue un flujo simple para el uso cotidiano:

### 1. Abrir la aplicación

Inicia la aplicación con:

```bash
python scripts/run.py
```

Después abre:

```text
http://127.0.0.1:8000
```

### 2. Sincronizar tus tareas

En el dashboard, haz clic en **Refresh tasks**.

StudyFlow iniciará sesión en Moodle y cargará tus actividades pendientes en el dashboard.

### 3. Abrir una tarea

Haz clic en cualquier tarjeta de tarea para abrir la vista de detalle.

Verás:

- nombre del curso
- estado de la tarea
- fecha de entrega
- descripción de la tarea

### 4. Pedir ayuda a la IA

Dentro de la página de la tarea, opcionalmente escribe una pregunta personalizada como:

- "dame un plan corto"
- "explícame qué tengo que entregar"
- "divide esto en pasos pequeños"
- "qué debería aclarar con el profesor?"

Luego haz clic en **Generate checklist**.

### 5. Usar la checklist para trabajar

La salida de la IA está estructurada para que puedas pasar de la confusión a la ejecución rápidamente.

## Proveedores de IA Compatibles

StudyFlow soporta:

- OpenAI
- Groq
- Ollama
- Anthropic

El modelo exacto y las credenciales dependen del proveedor que elijas.

## Por Qué Esto Es Mejor Que Usar Solo Moodle

Moodle te dice qué existe.

StudyFlow te ayuda a actuar sobre ello.

La diferencia importa cuando:

- estás saturado
- hay varias tareas pendientes al mismo tiempo
- las instrucciones de la actividad son ambiguas
- quieres interpretación rápida, no solo almacenamiento

## Por Qué Esto Es Mejor Que Usar un Chat de IA Genérico por Separado

Con un chat de IA normal, normalmente tienes que:

- abrir Moodle
- copiar el texto de la actividad
- pegarlo en una herramienta de IA
- explicar el contexto
- repetir ese proceso para cada tarea

StudyFlow reduce esa fricción porque el contexto de la tarea ya viene desde Moodle.

## Compensaciones

StudyFlow es intencionalmente simple, y esa simplicidad trae compensaciones.

### Beneficios de este enfoque

- flujo enfocado
- configuración local
- muy poca configuración dentro de la interfaz
- resuelve un dolor real del estudiante
- la ayuda de IA está ligada a una tarea específica, no a un chat vacío genérico

### Limitaciones de este enfoque

- depende de la estructura de páginas de Moodle
- si Moodle cambia su HTML, la sincronización puede necesitar ajustes
- es de usuario único y local-first
- no reemplaza tu criterio sobre los requisitos de una actividad
- las respuestas de IA pueden ayudar a interpretar una tarea, pero aún pueden estar incompletas o ser incorrectas

## Expectativas Importantes

StudyFlow te ayuda a entender y organizar tu trabajo.

No garantiza que:

- el texto de la tarea en Moodle esté completo
- la IA entienda por completo expectativas ocultas del profesor
- una checklist generada sea suficiente sin leer la actividad original

La mejor forma de usarlo es:

1. sincronizar tareas
2. leer la actividad
3. usar la checklist de IA para organizar tu enfoque
4. verificar los detalles importantes en Moodle antes de entregar

## Privacidad y Uso Local

StudyFlow está diseñado como una herramienta local-first.

- tu configuración se guarda localmente en tu máquina
- accedes a la aplicación desde tu propio navegador
- las credenciales de Moodle se usan para que la aplicación pueda iniciar sesión y obtener tus tareas

Si usas un proveedor de IA en la nube como OpenAI, Groq o Anthropic, el contenido de la tarea enviado para pedir ayuda puede salir de tu máquina y ser procesado por ese proveedor.

Si quieres un flujo más local, usa Ollama con un modelo local.

## Mejores Casos de Uso

StudyFlow funciona especialmente bien para:

- revisión semanal de actividades
- planificación antes de empezar tarea
- aclarar entregables
- dividir actividades grandes en acciones más pequeñas
- decidir qué hacer primero cuando varias tareas están pendientes

## Ejemplo de Flujo Diario

1. Abre StudyFlow.
2. Haz clic en **Refresh tasks**.
3. Revisa la lista de pendientes.
4. Abre la tarea más urgente.
5. Pregunta: "Dame un plan práctico paso a paso."
6. Sigue la checklist generada mientras completas la actividad.

## Si Algo No Funciona

Los problemas más comunes son:

- las credenciales de Moodle son incorrectas
- los navegadores de Playwright no están instalados
- al proveedor de IA seleccionado le faltan credenciales
- Moodle cambió su estructura de páginas

Si la sincronización funciona pero la ayuda de IA falla, el problema normalmente es la configuración del proveedor.

Si el dashboard carga pero las tareas no aparecen después de refrescar, el problema normalmente es acceso a Moodle o scraping.

## Resumen Final

StudyFlow no es una suite general de productividad.

Es una herramienta enfocada en un problema muy específico:

convertir tareas de Moodle en un plan accionable con la menor fricción posible.

Si tu problema real no es "necesito un lugar para guardar tareas", sino "necesito ayuda para entender qué hacer después", ahí es exactamente donde StudyFlow resulta útil.