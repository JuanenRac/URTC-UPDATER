<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | 🇪🇸 <b>Español</b> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 Detecta, instala y actualiza a mano todo el ecosistema URTC

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **Modo visual de escritorio:** la interfaz de escritorio por defecto usa
> **Qt Quick / QML** mediante el runtime GUI opcional `PySide6`. El núcleo del
> actualizador y el modo `--cli` siguen siendo solo libreria estandar para una CM5 sin pantalla.
>
> **Inicio Windows y evidencia de actualizacion:** abre `run-gui.vbs` (o usa
> `run.bat` sin argumentos) para el cliente grafico sin consola. El panel de
> actualizacion muestra checkpoints reales de precomprobacion, origen,
> manifiesto, build-test y finalizacion con evidencia capturada; `run.bat --cli ...`
> conserva la terminal para diagnosticos.
> Instalar solo se activa si falta el checkout y Actualizar solo si GitHub es
> superior. Durante una accion aprobada, los checkpoints sustituyen los
> controles del proyecto seleccionado; otra seleccion los restaura.
> **Instalar todos los faltantes** y **Actualizar todos los desfasados** son
> acciones de lote secuenciales, confirmadas por separado y basadas en el mismo
> estado real y flujo de seguridad.

**Comprobación de honestidad - lo que realmente funciona hoy:** **Madurez: establecido.** Este proyecto adapta el diseño ya probado de HYDRA-UMC-UPDATER (el mismo descubrimiento por manifiesto, la instalación/actualización con clon temporal verificado de forma atómica y el registro de evidencias) solo a los repositorios del ecosistema URTC. Se ejecutó de extremo a extremo contra GitHub en un espacio de trabajo aislado: una instalación limpia y una actualización posterior de un repositorio real se clonaron, compilaron y promovieron correctamente, conservando la copia anterior como respaldo. La lógica de descubrimiento y de versiones (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), el cliente de contenido raw de GitHub con reintento/backoff y listado de repositorios en caché (`github_client.py`), la comparación por commit (`commits.py`) y el pipeline de clonar-preparar-verificar-promover (`install.py`) están cubiertos por tests (`python -m pytest`), incluido un servidor HTTP de fixture local y repositorios git temporales reales con un remoto bare local. La lógica propia del puente Qt se ejecuta sin pantalla en los tests; las pantallas QML en sí no tienen un test automatizado. La cobertura de 8 idiomas de `i18n.py` se comprueba por test en cuanto a claves y marcadores, no en cuanto a calidad de la traducción. Consulta `CHANGELOG.md` para ver exactamente qué se ha entregado hasta ahora.

---

## 📋 De un vistazo

| | |
|---|---|
| Versión | `0.1.3` |
| Madurez | Establecido |
| Tecnología | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Destino | El PC de quien lo usa |
| En hardware real | No aplica: nada de esto se ejecuta en hardware |

## 1. 🛠️ VISIÓN TÉCNICA

URTC-UPDATER es una pequeña herramienta - GUI con ventana por
defecto, CLI completa con `--cli` - pensada para ejecutarse tanto en la
CM5 real como en la propia máquina Windows/Linux/macOS de un
desarrollador (cualquier workspace con el mismo tipo de checkout) que
responde a tres preguntas sobre cada otro proyecto real que descubre a
través del propio manifiesto `urtc.project.json` de cada checkout
vecino - el número en sí nunca está fijado aquí, ya que crece con el
propio ecosistema:

1. **¿Qué hay instalado aquí de verdad, y en qué versión?**
2. **¿Cuál es la última versión publicada en GitHub?**
3. **Si GitHub tiene una versión más nueva, déjame elegir un proyecto o un lote secuencial confirmado.**

Ese último punto es deliberado y no negociable: esta herramienta nunca cambia
un proyecto por iniciativa propia. Una acción sobre un proyecto seleccionado
siempre exige confirmación explícita. La GUI también puede ofrecer **Instalar
todos los faltantes** o **Actualizar todos los desfasados**; ambos son lotes
secuenciales confirmados por separado y sujetos a las mismas puertas de
manifiesto, versión y seguridad. Nunca existe actualización automática nocturna
sin una persona aprobando la acción exacta.

Tampoco todo proyecto descubierto pertenece a la CM5 en sí - la mayoría de los
repos con prefijo URTC y algunos de HYDRA-UMC son herramientas que un
desarrollador ejecuta desde su propio PC (el firmware se compila y se
flashea DESDE un puesto de trabajo, no se compila EN la célula), o apps
que se instalan en un móvil/reloj. El propio campo `deploy` de
`registry.py` registra cuál es cuál (ver sección 3), y la tabla de
proyectos de la GUI filtra por él - por defecto muestra "solo CM5" cuando
detecta que se ejecuta en Linux (el propio SO de la CM5 real), y "mostrar
todo" en Windows/macOS.

Ejemplo ilustrativo (el número exacto de proyectos y cada número de
versión de abajo están inventados para mostrar la forma de la salida,
no son una ejecución realmente capturada - el número real es siempre
el que `registry.py` descubre hoy, nunca una cifra fija en este
documento):

```
$ urtc-updater --cli status
Workspace root: /home/user/GitHub
PROJECT       MATURITY     ROLE      STACK       LOCAL     GITHUB    STATE
-------------------------------------------------------------------------------
URTC          production   firmware  firmware-c  0.3.0     0.3.1     OUTDATED
URTC-FLASHER  functional   tool      python-qt   0.2.1     0.2.1     up to date
URTC-TESTER   functional   tool      python-qt   0.2.2     0.2.2     NEW COMMITS

3/3 installed, 1 outdated, 1 with new commits at the same version
Run `urtc-updater update <project>` to update one by hand - never automatic, see this tool's own README.

$ urtc-updater --cli update URTC
Updating URTC into /home/user/GitHub ...
OK  Updated /home/user/GitHub/URTC to v0.3.1 (commit 1a2b3c4d5e6f) after a verified build; previous installation kept at /home/user/GitHub/URTC.backup-1a2b3c4d
```

Ejecutar `urtc-updater` sin argumentos (o hacer doble clic) abre la
misma información en una ventana - una tabla de proyectos, un filtro por
destino de despliegue, y botones de Instalar/Actualizar para la fila
seleccionada.

## 2. 🔄 CÓMO FUNCIONA REALMENTE UNA COMPROBACIÓN/ACTUALIZACIÓN

- **Origen de la versión**: la convención "cuentakilómetros" de
  auto-incremento de este ecosistema (cada build real incrementa un
  número de versión que vive DENTRO de un archivo fuente -
  `pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`,
  `version.properties`, `pubspec.yaml`, o un `#define` de firmware, según
  el stack del proyecto) nunca ha creado un tag de git ni un GitHub
  Release para ese incremento. Por eso esta herramienta lee el MISMO
  archivo que el propio `bump_version.py`/script de build de cada
  proyecto ya escribe, directamente desde la rama por defecto del repo
  vía el servidor de contenido raw de GitHub - no la API de Releases, que
  reportaría que todos los proyectos no tienen ningún release.
- **Detección local**: para cada proyecto descubierto,
  comprueba si existe un directorio con ese nombre exacto bajo la raíz
  del workspace (la disposición estándar del ecosistema - cada proyecto
  como directorio hermano, lo mismo que ya asumen build-frontend.sh y el
  propio descubrimiento de HYDRA-UMC-SUITE), y si existe, lee su propia
  copia local de ese mismo archivo de versión.
- **Una sola implementación de parseo** (`version_parse.py`) se comparte
  entre la lectura local y la descarga de GitHub, así que un checkout
  local y una descarga de GitHub nunca se interpretan con dos regex que
  puedan desincronizarse de forma independiente.
- **Instalar/actualizar**: `git clone` (instalar) compila después como
  un paso aparte. Actualizar un checkout YA EXISTENTE es atómico por
  verificación en su lugar: el candidato se clona, se fusiona con
  fast-forward (nunca un reset forzado, así que los cambios locales
  reales fallan de forma visible en vez de descartarse), y se compila/
  verifica en un clon de staging completamente independiente PRIMERO -
  la instalación real solo se toca (mediante dos renombrados de
  directorio consecutivos, conservando la instalación anterior en
  `<nombre>.backup-xxxxxxxx`, sin borrarla) si esa compilación de staging
  realmente tiene éxito. Un fallo de compilación, un checkout divergente/
  sucio, un corte de luz o un disco lleno en cualquier momento antes de
  esa promoción final dejan la instalación anterior completamente
  intacta y operativa - ver el propio docstring de `clone_or_pull` en
  `install.py`. El propio remoto git del clon de staging se restaura al
  origen real de GitHub justo después de crearse (un clon local simple
  lo dejaría apuntando a la ruta de instalación antigua, terminando en
  silencio con todas las actualizaciones futuras una vez promovido), y
  los datos locales reales del checkout instalado (todo lo que git
  considera sin seguimiento o ignorado - `data/settings.json` y
  similares, excluyendo artefactos de build regenerables) se trasladan
  al clon de staging antes de compilar, de modo que el estado operativo
  real de un proyecto sobrevive a una actualización en vez de quedar
  varado en el checkout `.backup-xxxxxxxx` conservado. En cualquier caso esto ejecuta el `build-test.sh`/
  `build-test.bat` propio de ese proyecto (la comprobación no-versionada
  - ver sección 3) si lo tiene. Esta herramienta nunca reimplementa los
  pasos de build propios de un proyecto.

**Commits firmados (avisar por defecto, exigir si se pide):** una revisión sin firma válida (`git verify-commit`: llavero GPG, o SSH con `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) se instala igualmente, y los pasos de la ventana y de la línea de comandos dicen que no está firmada. Con `"signature_policy": "require"` en `~/.urtc_updater_settings.json` (o `URTC_UPDATER_REQUIRE_SIGNED=1`; el antiguo `"require_signed_commits": true` significa lo mismo) el candidato - el `HEAD` de un clon nuevo o el `FETCH_HEAD` descargado de una actualización - debe pasar `git verify-commit` antes de leer su manifiesto o construir nada, y un candidato rechazado deja intacto el checkout instalado.

## 3. 🧱 ARQUITECTURA Y DECISIONES DE DISEÑO

- **GUI Qt Quick por defecto, `--cli` para headless.** `main.py` comprueba
  `--cli` antes de importar el runtime opcional PySide6. La CLI funciona en
  una CM5 sin pantalla ni dependencia de escritorio; sin argumentos inicia
  QML cuando esta disponible y Tkinter queda solo como fallback temporal.
- **La GUI con ventana es real y habla 8 idiomas (`i18n.py`) - `--cli` a propósito no.** Cada widget, y el texto de cada checkpoint y de cada fallo de una instalación o actualización, se muestra en el idioma elegido en un selector (en/es/fr/it/de/zh/ja/pt, portugués de Portugal para pt), tomado de una preferencia guardada o de la configuración regional del sistema. Los pasos de instalación y actualización viajan como códigos de mensaje más parámetros y solo la ventana los convierte en texto, así que un cambio de idioma los vuelve a dibujar. Los nombres de proyecto y de familia y los textos `notes`/`tech` de cada proyecto no se traducen: el manifiesto es su única fuente de verdad. La salida de `--cli` se queda en inglés a propósito, porque está pensada para scripts y tuberías.
- **`deploy` es una clasificación, no una restricción.** Tratar todo
  proyecto descubierto como "algo que pertenece a la CM5" era un error - los repos
  de firmware se compilan y se flashean DESDE un PC (la CM5 solo necesita
  el binario resultante vía CAN-OTA, nunca el código fuente de este repo),
  y varias herramientas (URTC-FLASHER, HYDRA-UMC-SUITE,
  HYDRA-UMC-TOOL-CLI, ...) están pensadas para correr en el propio puesto
  de trabajo de un operador, no dentro de la célula misma. El campo
  `deploy` de `registry.py` ("cm5" / "user-pc" / "mobile" / "wearable" / "dev-server")
  registra eso, y el filtro de la GUI lo usa como punto de partida
  razonable - nunca como una restricción dura, ya que esta misma
  herramienta también está pensada para correr en el PC de un
  desarrollador, donde todo proyecto descubierto es igual de válido de inspeccionar.
- **Sin lógica de build por stack en esta herramienta.** El ecosistema abarca varias toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, firmware ARM). Reimplementar aquí el build de cada proyecto crearía un segundo lugar que dice saber compilarlo, condenado a desviarse del script del propio proyecto. `install.py` ejecuta en su lugar el `build-test.sh` sin versionado del propio proyecto (`build-test.bat` en Windows) y falla de forma segura si una copia no lo tiene. Los scripts de build que suben la versión (`build.sh` y similares) esta herramienta nunca los ejecuta.
- **Contenido raw de GitHub, no la API de Releases.** Ver sección 2 - la
  convención de versionado de este ecosistema nunca crea un tag/release,
  así que la API de Releases sería activamente incorrecta aquí, no solo
  menos conveniente.
- **Un fallo de red transitorio recibe un reintento real; una respuesta
  definitiva nunca.** Cada petición real a GitHub (`_urlopen_with_retries`
  de `github_client.py`) reintenta hasta 3 veces con backoff, pero solo
  cuando la conexión nunca llegó a obtener respuesta alguna (DNS/timeout/
  reset). Un estado HTTP real que GitHub sí devolvió - 404, 403, 500 -
  nunca se reintenta: GitHub ya respondió, y volver a golpearlo solo
  gastaría más límite de peticiones para el mismo resultado.
- **Un catálogo remoto malformado falla de forma ruidosa; un proyecto
  malformado no.** Si el propio listado de repositorios de GitHub es
  inalcanzable o no se puede parsear, `discover_remote_projects()` lanza
  una excepción - tanto `gui.py` como `main.py` ya la capturan y caen de
  vuelta a la lista de proyectos descubierta localmente en vez de mostrar
  un escaneo roto o vacío. El manifiesto malformado de un solo
  repositorio, en cambio, se aísla en la propia lista `errors` de ese
  escaneo y nunca aborta el descubrimiento del resto - una prueba real
  con servidor de fixtures (`tests/test_github_client.py`) demuestra
  ambos caminos.
- **La CLI es explícita; los lotes de la GUI se confirman.** Los comandos
  `install`/`update` de CLI reciben un nombre de proyecto. La GUI puede ejecutar
  **Instalar todos los faltantes** o **Actualizar todos los desfasados**, pero
  solo tras una confirmación independiente y de forma secuencial a través de
  las mismas puertas de seguridad. No existe actualización automática sin
  supervisión.
- **Solo librería estándar.** `urllib` para las descargas de GitHub
  (`github_client.py`), `subprocess` para las llamadas a git/scripts de
  build (`install.py`), nada más - que una herramienta responsable de
  mantener sanas las dependencias de TODOS los demás proyectos se quede
  sin dependencias propias es deliberado.
- **Simplificación conocida:** un repositorio formado por varios binarios con versión independiente (URTC tiene cuatro: principal y esclavo, aplicación y bootloader) se sigue con UNA sola versión, la que su propio `urtc.project.json` declara en `native_version`. Eso responde a "¿está este repositorio más o menos al día?", no sustituye la comprobación de versión por componente de un flasheo.

## 📂 ESTRUCTURA DE DIRECTORIOS

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - sin catálogo estático; se construye en tiempo de descubrimiento desde el manifiesto propio de cada repo
│   ├── project_manifest.py # Lee/valida un urtc.project.json propio de cada repositorio
│   ├── version_parse.py   # UNA implementación de extracción por regex, local+GitHub
│   ├── detect.py          # Escanea una raíz de workspace para ver qué está instalado
│   ├── github_client.py   # Descarga concurrente del contenido raw + reintento/backoff real ante errores de red transitorios
│   ├── install.py         # git clone/pull + delega en el script de build propio
│   ├── signature.py       # Política opcional de commits firmados (git verify-commit antes de compilar)
│   ├── commits.py          # Compara una copia con su remoto por commit (git ls-remote)
│   ├── messages.py         # Mensajes de instalación/actualización como códigos más parámetros
│   ├── evidence.py         # Registro encadenado por hash de cada intento
│   ├── settings.py         # Preferencias recordadas (idioma, espacio de trabajo, retención, perfiles)
│   ├── profiles.py         # Perfiles de estación con nombre
│   ├── notify.py           # Notificación de escritorio para la comprobación de solo aviso
│   ├── logs.py             # Rotación de los archivos de registro de la ventana
│   ├── i18n.py             # Traducciones reales y completas de la GUI (8 idiomas)
│   ├── qt_gui.py           # Puente Qt Quick hacia los servicios reales de descubrimiento/actualizacion
│   ├── qml/Main.qml        # Shell de escritorio con tema, checkpoints y About
│   ├── gui.py              # Fallback Tkinter si PySide6 no esta disponible
│   └── main.py             # Despacho: GUI por defecto, --cli para status/install/update
├── tests/                  # Tests reales de cada módulo (`python -m pytest`)
├── docs/
│   ├── CLI_REFERENCE.md     # Referencia de comandos
│   └── QML_DESKTOP_GUI.md   # Arquitectura de la GUI Qt Quick
├── images/                 # Medios, iconos de app y capturas de la interfaz
├── tools/
│   ├── build_test.py        # Comprobación de compilación sin versionado
│   ├── ci_validate.py       # Validación de manifiesto/CHANGELOG/docs usada por CI
│   ├── generate_app_icon.py # Renderiza el SVG público de HYDRA-UMC al icono que consume Windows
│   ├── migrate_project_manifests.py  # Audita un workspace tras la migración de manifiestos de un solo uso
│   └── validate_project_manifests.py # Valida manifiestos propios de cada repo + versiones nativas de build
├── .env.example            # Plantilla de variables de entorno
├── build.sh / build.bat    # venv + instalación editable + compile-check
├── run.sh / run.bat        # GUI por defecto / entrada CLI
├── run-gui.vbs             # Lanzador grafico Windows sin ventana de consola
├── bump_version.py         # Incremento "cuentakilómetros" del ecosistema (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Sincroniza la versión de urtc.project.json con la nativa (--sync)
```

## ⚙️ COMPILACIÓN Y EJECUCIÓN

```bash
chmod +x build.sh   # una sola vez
./build.sh          # crea .venv, pip install -e ., compile-check de todo
./run.sh                                # GUI con ventana (por defecto)
./run.sh --cli status                   # qué está instalado, versión local vs. GitHub
./run.sh --cli status --offline         # lo mismo, sin comprobar GitHub
./run.sh --cli install <NOMBRE-PROYECTO> # clona + compila un proyecto aún no instalado
./run.sh --cli update  <NOMBRE-PROYECTO> # actualiza + recompila un proyecto ya instalado
```

En Windows: `build.bat`, y luego `run.bat` (GUI) / `run.bat --cli status`
/ `run.bat --cli install <nombre>` / `run.bat --cli update <nombre>`.

La GUI preferida necesita el runtime Qt opcional (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` ya lo instalan). `--cli` no tiene dependencia grafica y
es la entrada correcta para una CM5 headless. Si Qt no esta disponible, la
antigua ventana Tkinter es solo un fallback de compatibilidad.

**Solución de problemas**

- `status` muestra `?` en la versión de GitHub de un proyecto: no se pudo leer GitHub para él. La columna STATE dice por qué (por ejemplo `installed, GitHub unknown (HTTP 404)` o un aviso de límite de peticiones).
- `status` muestra `-` en GitHub sin ningún error: ejecuta `status` (sin
  `--offline`) - `-` solo aparece cuando la comprobación de GitHub se
  omitió por completo.
- `install`/`update` falla con "No non-versioning build-test.sh/.bat found": esa copia no tiene `build-test.sh` (`build-test.bat` en Windows). Actualiza el propio proyecto o verifícalo a mano; esta herramienta nunca ejecuta en su lugar un script de build que suba la versión.
- `git pull --ff-only` falla: el checkout local tiene cambios sin
  commitear o el historial ha divergido - resuélvelo a mano (`git
  status` dentro del propio directorio del proyecto) antes de reintentar
  `update`. Esta herramienta nunca fuerza un reset de un checkout.

## 🧹 MANTENIMIENTO Y COMANDOS DE ESTACIÓN

- **Instalaciones anteriores conservadas.** Cada actualización conserva la instalación que reemplazó en `<nombre>.backup-xxxxxxxx`. Se guardan las 2 más recientes por proyecto (`"backups_to_keep"` en `~/.urtc_updater_settings.json` cambia el número) y las más antiguas se eliminan tras una actualización correcta. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` las elimina a demanda, junto con cualquier carpeta temporal oculta que haya dejado una ejecución interrumpida.
- **Restaurar una.** `urtc-updater --cli restore-backup <PROYECTO> [--backup CARPETA] [--list]` devuelve una instalación conservada a su sitio. La instalación que se reemplaza también se conserva, así que el cambio se puede deshacer.
- **Misma versión, commits nuevos.** La versión solo cambia en un build de publicación, así que `status` también compara el commit de cada proyecto instalado con el remoto (`git ls-remote`) y muestra `NEW COMMITS` cuando GitHub tiene trabajo que la copia no tiene. La ventana muestra el mismo estado y ofrece Actualizar.
- **Mirar antes de aprobar.** `urtc-updater --cli update <PROYECTO> --preview` descarga el candidato y muestra su commit, autor, versión, estado de firma y los archivos de build o de herramientas que cambia, sin tocar la copia.
- **Solo avisar.** `urtc-updater --cli check [--notify] [--quiet]` lista lo que se podría actualizar y no cambia nada. Termina con código 10 cuando hay algo que actualizar, para que una tarea programada avise a una persona; `--notify` además muestra una notificación de escritorio.
- **Evidencias.** Cada instalación, actualización y restauración se registra con hora, equipo y usuario en `.urtc-updater/evidence.jsonl`, con cada línea encadenada a la anterior por hash. `urtc-updater --cli evidence [--export ARCHIVO]` verifica la cadena y puede exportarla como un único documento JSON.
- **Perfiles de estación.** `"profiles"` en el archivo de ajustes nombra los proyectos con los que trabaja una máquina y si se permiten lotes; `--profile NOMBRE` (o `"profile"` en los ajustes) limita `status`, `check`, `install` y `update` a él, y la ventana sigue el mismo perfil.

## 🚀 HOJA DE RUTA

- Un ejecutable de GUI independiente empaquetado (PyInstaller, siguiendo
  la propia convención `build_exe.bat`/`.sh` de HYDRA-UMC-SUITE) para una
  instalación con doble clic sin ningún paso de `pip`/venv - hoy la GUI
  todavía necesita `./build.sh` primero, igual que la CLI.
- Comprobación previa opcional de dependencias por proyecto (avisar de
  toolchains faltantes - sin Rust/Go/SDK de Android/Flutter instalado -
  antes de que un `install` falle a mitad de camino).
- Seguimiento por componente para el firmware multi-binario propio de
  HYDRA-UMC/URTC (ver la "simplificación conocida" de la sección 3), en
  cuanto haya una necesidad real más allá del único componente
  representativo que se sigue hoy.

## 🔗 Proyectos Relacionados

**URTC** (Universal Robot Tool Controller) es una plataforma física real de cambio de herramientas para robots, del mismo autor (JuanenRac / Electro Hobby 3D). Cada repositorio tiene su propia versión, sus propias pruebas y su propio README; esta es toda la familia:

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware del PCB físico Universal Robot Tool Controller, 25+ perfiles de herramienta sobre bus CAN
* **[URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS)** - La arquitectura, las interfaces, la base de seguridad, la matriz de capacidades y el catalogo de proyectos generado del ecosistema, mas las herramientas que comparan todos los repositorios
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Herramienta de escritorio para flashear placas URTC, CAN-OTA más SWD/JTAG de chip completo
* **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** - Firmware para un rack de montaje de herramientas con decodificacion real de ID y precalentamiento Smart Idle
* **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** - Herramienta de diagnostico CAN en vivo para placas URTC, un panel por perfil de herramienta
* **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** - Firmware mas un companero de vision real en Python para un cabezal de inspeccion termica/RGB
* **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** - Alternativa basada en navegador a URTC-TESTER via la Web Serial API, sin instalacion local
* **URTC-UPDATER** (este repositorio) - Detecta, instala y actualiza los propios repositorios del ecosistema

El diseno de esta herramienta (descubrimiento por manifiesto, instalacion/actualizacion atomica-por-verificacion, registro de evidencia) se comparte con **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** y **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - los propios actualizadores del mismo autor para los ecosistemas HYDRA-UMC y A.R.M.O.R., cada uno limitado solo a sus propios repositorios.

## 📚 Documentacion y Comunidad

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — cada subcomando de `--cli`, salida real capturada de una instalacion real, y el contrato de codigos de salida.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — como esta estructurado el cliente de escritorio Qt Quick/QML, y como sigue siendo una superficie de control real sobre el mismo backend que usa `--cli`, no una segunda implementacion.
* **[Historial de cambios de este repositorio](CHANGELOG.md)**
* Preguntas, ideas e informes: electrohobby3d@gmail.com

## 👤 AUTOR
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENCIA

GPL-3.0-or-later - ver [LICENSE](LICENSE).
