# Changelog
## [0.13.11] - 2026-01-17
### Fixed
- Canvas: al editar señales con doble click ya no se cierra la aplicación. Se evita llamar a super().mouseDoubleClickEvent() después de abrir un editor que reconstruye la escena (y puede destruir el item).

## [0.13.8] - 2026-01-16
### Added
- Canvas: línea base entre equipo y chip (IN/OUT) para soportar decoraciones aun cuando no existan enclavamientos.

### Fixed
- Editar señal (doble click / menú "Editar señal"): ahora permite activar/desactivar Block de pruebas (B.P.) cuando se edita desde una salida (OUT).
- Canvas: el Block de pruebas ahora se representa gráficamente en la salida (símbolo en serie + texto fijo "B.P.").

### Changed
- Canvas: se aumentó la separación entre el equipo y los chips (IN/OUT) para dar espacio a B.P./enclavamientos.

## [0.13.7] - 2026-01-16
### Added
- Renombrar bahía desde el árbol (menú contextual).
- Renombrar equipo desde el árbol y desde el canvas (menú contextual). Al renombrar un equipo se actualizan automáticamente las referencias en textos "hacia/desde <equipo>" en todo el proyecto.

### Fixed
- Replicar bahía: ProjectController ahora llama correctamente a replication_service.replicate_bay (parámetro src_bay_id).

### Changed
- Chips: block de pruebas se indica como "B.P." (texto fijo).

## [0.13.6] - 2026-01-16
### Added
- Editor de "Block de pruebas" y "Enclavamientos" desde el menú contextual del chip.
- Persistencia estructurada de enclavamientos (mode + items con relay_tag).

### Changed
- Enclavamientos pasan a ser un atributo de ENTRADAS (IN) y el block de pruebas un atributo de SALIDAS (OUT).

### Fixed
- Exportación Excel: columna de enclavamientos ahora refleja entradas (IN) y el block de pruebas sólo salidas (OUT).

## [0.13.5] - 2026-01-15
### Fixed
- Replicación por subequivalencia: cada SignalID lógico de la bahía fuente se mapea a un único SignalID en la bahía replicada, preservando pares IN/OUT y evitando duplicados.
- Reconocer una salida (OUT) ahora confirma/actualiza también la entrada (IN) espejo si ya existe (incluyendo casos donde estaba PENDING).

## [0.5.1] - 2026-01-14
### Fixed
- Mantiene posiciones del canvas al agregar señales/equipos (no se “montan” encima).
- ID de equipos ahora es interno/autogenerado (no se solicita al usuario).
- Selección visible de señales (chips), edición por doble click y eliminación por tecla Supr con confirmación.
- Se elimina el popup molesto al abrir “biblioteca global”; se usa barra de estado.

## [0.5.0] - 2026-01-14
### Added
- Gestión de bahías y equipos desde la UI (crear bahía, crear equipo, eliminar equipo).
- Biblioteca de señales GLOBAL (archivo JSON independiente) editable incluso sin proyecto abierto.
- Con proyecto abierto: biblioteca por-proyecto (plantillas en JSON del proyecto) + acción para importar desde la biblioteca global.
- Pantalla inicial: crear proyecto / abrir proyecto / editar biblioteca global.

## [0.4.0] - 2026-01-14
- Biblioteca de señales editable por proyecto (CRUD) y drag & drop con metadatos.


## [0.6.0] - 2026-01-14
### Added
- Replicar bahía completa (equipos + layout + señales internas) con renombrado y offset de layout.
- Señales con destino fuera de la bahía quedan como PENDIENTES (EXTERNO) para reconocimiento posterior.
- Generación de Signal ID globalmente único a nivel de proyecto (evita colisiones entre bahías).



## [0.7.0] - 2026-01-14
### Added
- Replicado inteligente por paño: reemplazo de token (ej. H1→H2) en nombres de equipos, textos y nombres de señales.
- En señales externas: aplica reemplazo si corresponde y deja estado PENDING para confirmación/edición del usuario.


## [0.7.1] - 2026-01-14
- se corrige anidación de funciones en main_window.py

## [0.8.0] - 2026-01-14
### Added
- Biblioteca global: diálogo dedicado para gestionar (ver/editar/guardar/cargar) plantillas globales; menú ahora abre el diálogo.
- Bahías: ID interno autogenerado (BAY-001, BAY-002, ...). El usuario sólo ingresa el nombre.
- Señales: soporte para "Block de pruebas" en salidas (flag persistente) y dibujo como "X" en el chip de salida.
- Señales: soporte básico de enclavamientos (lista de etiquetas) y dibujo como contacto NC + contador en el chip; edición desde diálogo/contextual.


## [0.9.2] - 2026-01-14
### Fixed
- MainWindow: restaurados métodos add_device y flujo de creación de equipos; corregida referencia en menú.
- MainWindow: saneada estructura/indentación alrededor de métodos del árbol.


## [0.9.3] - 2026-01-14
### Fixed
- MainWindow: agregado método _generate_device_id_for_bay para IDs internos de equipos.
- MainWindow: add_device robusto (captura excepciones y muestra QMessageBox en vez de cerrar la app).


## [0.10.0] - 2026-01-14
### Changed
- Reescritura completa de ui/main_window.py (sin parches): consolidación de menús, navegación y flujos de proyecto/bahía/equipo.
### Fixed
- Errores de indentación y métodos fuera de clase que causaban AttributeError (add_device/import_global_to_project, etc.).


## [0.10.1] - 2026-01-14
### Fixed
- TemplateLibraryDock: agregado método set_scene (compatibilidad) para evitar crash al crear bahías/canvas.


## [0.10.2] - 2026-01-14
### Fixed
- AddDeviceDialog: firma consistente con el uso en MainWindow (bay_choices + default_bay_id).
- MainWindow: creación de equipos ya no crashea por parámetros incorrectos.


## [0.10.3] - 2026-01-14
### Fixed
- CanvasScene: agregado select_device_item() requerido por el árbol de navegación (seleccionar y centrar nodo).


## [0.10.4] - 2026-01-14
### Fixed
- CanvasScene.select_device_item(): corregida indentación (estaba fuera de la clase, por eso no existía en runtime).


## [0.12.0] - 2026-01-14
### Added
- Bandeja global de señales pendientes (dock): filtrar/buscar, saltar al equipo, reconocer, editar y eliminar a nivel de proyecto.


## [0.12.1] - 2026-01-14
### Added
- Bandeja de pendientes: selección múltiple y eliminación masiva.
### Fixed
- Bandeja de pendientes: emite eventos de mutación para refrescar canvas/árbol automáticamente.


## [0.12.2] - 2026-01-14
### Added
- Bandeja de pendientes: botón “Siguiente pendiente” para avanzar rápidamente (reconoce automáticamente si es OUT).
### Changed
- Exportación Excel: hoja por bahía, filas agrupadas por equipo, incluye naturaleza (ANALOG/DIGITAL), IN/OUT, estado, block de pruebas y enclavamientos.


## [0.12.3] - 2026-01-14
### Added
- Árbol de navegación: contador de señales pendientes por bahía y por equipo.
- Exportación Excel: hoja “Resumen” con conteos por bahía y detalle por equipo.


## [0.12.4] - 2026-01-14
### Added
- Canvas: indicador visual de señales pendientes por equipo (badge P:x + borde resaltado).
- Exportación PNG: cabecera con proyecto/bahía, fecha y versión.


## [0.12.5] - 2026-01-14
### Fixed
- MainWindow: método _on_project_mutated ahora forma parte de la clase (evita crash al iniciar).
### Added
- ui/widgets/canvas_host.py: contenedor dedicado para CanvasView.


## [0.12.6] - 2026-01-14
### Fixed
- ProjectController: firma de __init__ alineada con MainWindow (sin argumento 'parent'); app_dir opcional.


## [0.12.7] - 2026-01-14
### Fixed
- StartPage: botones ahora están conectados (Nuevo/Abrir/Biblioteca global).
- MainWindow ↔ ProjectController: llamadas alineadas con API real (add_bay/add_device/replicate_bay/open_global_library).
### Changed
- Dock “Pendientes”: ahora se puede mostrar/ocultar desde menú Ver (por defecto oculto).


## [0.12.8] - 2026-01-14
### Fixed
- ProjectController: add_bay ahora retorna bay_id para refrescar navegación.
- ProjectController/MainWindow: API coherente para agregar equipos; se valida existencia de bahías.


## [0.12.9] - 2026-01-15
### Fixed
- Canvas: al abrir una bahía se reemplaza completamente la vista previa (StartPage ya no queda visible).
- Biblioteca de señales: se reconstruye TemplateLibraryDock (sin '...'); se carga biblioteca global por defecto.
### Changed
- Replicar bahía: el usuario ya no introduce ID interno; se autogenera BAY-### y se valida origen por ID real.


## [0.13.0] - 2026-01-15
### Fixed
- Biblioteca de señales: SignalTemplate usa 'label' (no 'name'); dock y store alineados al modelo.
- Plantillas globales: se crean/recuperan defaults y se asegura compatibilidad con archivos antiguos.


## [0.13.1] - 2026-01-15
### Fixed
- Canvas: chips IN/OUT reposicionados debajo del header/captions y ajuste de alto de tarjeta para evitar montajes.


## [0.13.2] - 2026-01-15
### Added
- Canvas: auto-resize de nodos según cantidad de chips (hasta tope) + scroll interno con rueda del mouse y scrollbar.


## [0.13.3] - 2026-01-15
### Changed
- Canvas: chips IN vuelven a posicionarse al lado izquierdo (fuera de la tarjeta) como en versiones tempranas; OUT queda a la derecha (columna media), mejor legibilidad.
