# AI Agent Guide: Cobot Glue Dispensing System

## Architecture Overview

This is a PyQt6-based industrial robot control system for glue dispensing and painting operations. The codebase uses a **layered architecture** with clear separation of concerns:

```
Frontend (PyQt6 UI)
    ↓
Communication Layer (RequestHandler/MessageBroker)
    ↓
Applications (Glue Dispensing, Painting, Test)
    ↓
Core (State Management, Factories, Interfaces)
    ↓
Modules (Robot, Vision, Modbus, Settings)
    ↓
Libraries (Shared utilities, patterns)
```

**Entry Point**: `src/main.py` → initializes `ApplicationContext` → creates application via `ApplicationFactory` → loads plugins → starts Qt event loop

**Key Design Decision**: The system supports multiple robot vendors (Fairino, ZeroError) through abstraction (`IRobot` interface), multiple applications (glue dispensing, painting) through factory pattern, and extensible UI through plugin system.

## Critical Design Patterns

### 1. Three-Layer State Management
All state flows through this hierarchy:

- **Layer 1 - Operations** (`IOperation`): Individual tasks (INITIALIZING → STARTING → PAUSED → COMPLETED/STOPPED/ERROR)
- **Layer 2 - Application** (`ApplicationStateManager`): Aggregates operation states
- **Layer 3 - System** (`SystemStateManager`): Priority-based aggregation (ERROR=4 > STOPPED=3 > PAUSED=2 > STARTED=1 > IDLE=0)

State changes propagate via `MessageBroker` pub/sub topics. See `src/core/operation_state_management.py` and `src/modules/state_management/`.

### 2. Pause/Resume Pattern
Critical for industrial safety. Operations must implement 5 pause scenarios:

1. Pause during execution (preserve context)
2. Resume from pause
3. Stop during pause (cleanup)
4. Pause during initialization
5. Error during pause

See `tests/glue_process/test_pause_resume.py` for 55 test cases. Use `CancellationToken` for thread-safe cancellation.

**Implementation Template**:
```python
class MyOperation(IOperation):
    def _do_pause(self) -> OperationResult:
        self._save_context()  # Preserve state
        return OperationResult.success()
    
    def _do_resume(self) -> OperationResult:
        self._restore_context()  # Resume from saved state
        return OperationResult.success()
```

### 3. Application Context Singleton
**CRITICAL**: Always call `ApplicationContext.set_current_application(app_instance)` before initializing services. Services retrieve settings paths from the current application.

Settings are stored per-application: `applications/{app_type}/storage/settings/`

### 4. Plugin System
Plugins are discovered by scanning `src/plugins/core/` for `plugin.json` metadata files.

**Plugin Lifecycle**:
1. Discovery: `PluginManager.discover_plugins()`
2. Filtering: Match `ApplicationMetadata.required_plugin_categories` with `plugin.json` category
3. Loading: Category-ordered (CORE → FEATURE → TOOL → EXTENSION)
4. Initialization: `plugin.initialize(controller_service)` → `plugin.create_widget(parent)`

See `src/plugins/base/plugin_manager.py` and existing plugins in `src/plugins/core/`.

### 5. Factory Pattern for Multi-Robot Support
`ApplicationFactory` creates applications based on `ApplicationType` enum. `RobotFactory` creates robot instances based on `RobotManufacturer` enum.

Applications declare robot compatibility via `ApplicationMetadata.robot_type`.

## Communication Patterns

### Request/Response Flow
UI → `DomesticRequestSender` → `RequestHandler` → Dispatcher (e.g., `RobotDispatch`) → Controller → Service

**Adding New Endpoints**:
1. Define endpoint in `src/communication_layer/api_gateway/api/v1/endpoints/{domain}.py`
2. Create dispatcher in `src/communication_layer/api_gateway/dispatch/`
3. Register in `main_router.py`

### Pub/Sub Messaging
`MessageBroker` uses **weak references** for automatic cleanup. Topics defined in:
- `SystemTopics`, `RobotTopics`, `VisionTopics`, `GlueSprayServiceTopics`

**Usage**:
```python
MessageBroker.publish(RobotTopics.ROBOT_STATE_CHANGED, new_state)
MessageBroker.subscribe(RobotTopics.ROBOT_STATE_CHANGED, callback, subscriber_id)
```

## State Machine: ExecutableStateMachine

The glue dispensing process uses a 23-state machine defined in `src/applications/glue_dispensing/state_machine/`. States include:
- WAIT_FOR_WORKPIECE → CAPTURE_FRAME → PROCESS_FRAME → MATCH_CONTOURS → MOVE_TO_START → SPRAY_GLUE → ...

**Key Files**:
- `src/applications/glue_dispensing/state_machine/glue_dispensing_state_machine.py` - state definitions
- `src/applications/glue_dispensing/state_machine/state_handlers/` - individual state handlers
- `src/applications/glue_dispensing/state_machine/state_context.py` - shared context

**Modifying States**: Update transition rules in state machine, implement handler in `state_handlers/`, ensure pause/resume compatibility.

## Vision System

**Pipeline**: Frame Capture → Contour Detection → Matching → Transformation

**Matching Strategies** (Strategy Pattern):
- `GeometricContourMatcher` - distance-based matching
- `MLContourMatcher` - ML model (scikit-learn Random Forest)

Trained models stored in `src/saved_models/`. See `src/modules/vision/contour_matching/`.

## Developer Workflows

### Running the Application
```bash
source .venv/bin/activate  # Activate venv
python src/main.py         # Run main application
```

Switch applications by editing `APPLICATION_TYPE` in `main.py`:
- `ApplicationType.GLUE_DISPENSING`
- `ApplicationType.PAINT_APPLICATION`
- `ApplicationType.TEST_APPLICATION`

### Testing
```bash
pytest                     # Run all tests
pytest -m unit            # Unit tests only
pytest -m integration     # Integration tests
pytest -m pause_resume    # Pause/resume scenario tests
```

Test organization mirrors `src/` structure. Key test suites:
- `tests/glue_process/test_pause_resume.py` - 55 pause/resume scenarios
- `tests/plugins/test_plugin_manager.py` - plugin lifecycle
- `tests/vision_system/` - vision pipeline tests

### PyCharm Integration
Use PyCharm's built-in tools:
- **Run Configurations**: Create for `src/main.py` with working directory set to project root
- **Test Runner**: Right-click test files → Run with pytest
- **Debugger**: Set breakpoints in state handlers, operation lifecycle methods

## Adding New Components

### New Application
1. Extend `BaseRobotApplication` in `src/applications/{app_name}/`
2. Implement `get_metadata()` returning `ApplicationMetadata` with robot type and plugin dependencies
3. Register in `ApplicationFactory.register_application(ApplicationType.YOUR_APP, YourAppClass)`
4. Create settings folder: `applications/{app_name}/storage/settings/`

### New Plugin
1. Create folder: `src/plugins/core/{plugin_name}/`
2. Add `plugin.json` with metadata (name, version, category, description)
3. Implement `IPlugin` interface: `initialize(controller_service)`, `create_widget(parent)`
4. Plugin auto-discovered on startup if category matches application requirements

### New Robot Type
1. Implement `IRobot` interface in `src/modules/robot/vendors/{vendor_name}/`
2. Register in `RobotFactory._create_robot_instance()`
3. Add vendor-specific configuration in settings

### New Settings Category
1. Create repository class implementing `ISettingsRepository` in `src/modules/settings/repositories/`
2. Register in `ServiceRegistry` for state aggregation
3. Settings auto-persist to application-specific folders

## Common Pitfalls

1. **Forgetting ApplicationContext**: Services fail if `ApplicationContext.set_current_application()` not called first
2. **Blocking UI Thread**: Long operations must run in separate threads with `CancellationToken`
3. **Strong References in MessageBroker**: Use weak references to avoid memory leaks
4. **Pause/Resume Context**: Must save/restore all necessary state (positions, flags, indices)
5. **Plugin Dependencies**: Ensure `plugin.json` category matches application's `required_plugin_categories`

## Key Dependencies

- **GUI**: PyQt6 (6.6.0+)
- **Vision**: opencv-python (4.9.0+), scikit-image (0.22.0+)
- **Industrial**: minimalmodbus (2.1.0+) for Modbus RTU communication
- **ML**: scikit-learn (1.3.0+) for contour matching
- **CAD**: ezdxf (1.1.0+) for DXF file parsing
- **Data**: numpy (1.26.0+), pandas (2.1.0+)

See `requirements.txt` for complete list.

## Project-Specific Conventions

1. **Import Organization**: Group by layer (stdlib → third-party → core → modules → applications)
2. **Naming**: Operations end with "Operation", services with "Service", repositories with "Repository"
3. **Error Handling**: Return `OperationResult` objects, don't raise exceptions in operation lifecycle methods
4. **Threading**: Use `QThread` for UI-related concurrency, standard threads for backend
5. **Settings Keys**: Use SCREAMING_SNAKE_CASE, defined as constants in repository classes
6. **State Transitions**: Always publish via `MessageBroker`, never modify state directly

## Debugging State Transitions

Enable state machine logging in `ExecutableStateMachine` to trace transitions:
```python
# See logs in console for state changes
# Format: [STATE_MACHINE] CURRENT_STATE -> EVENT -> NEXT_STATE
```

Debug pause/resume issues by checking:
1. Context preservation in `_do_pause()`
2. Context restoration in `_do_resume()`
3. Cleanup in `_do_stop()`
4. Thread cancellation via `CancellationToken.is_cancelled()`

## Contour Editor: Standalone & Pluggable Architecture

The `src/frontend/contour_editor` package is designed to be **standalone** and **backend-agnostic** using dependency injection.

### Clean Import Pattern

The package uses a comprehensive `__init__.py` to enable clean, short imports:

**From outside the package (e.g., plugins):**
```python
from frontend.contour_editor import (
    # Main widget
    MainApplicationFrame,
    
    # Data models
    ContourEditorData, Segment, Layer,
    
    # Providers
    DialogProvider, WidgetProvider, IconProvider,
    WorkpieceFormProvider, SegmentManagerProvider, SettingsProviderRegistry,
    
    # Adapters
    WorkpieceAdapter,
    
    # Model
    WorkpieceFactory, BaseWorkpiece
)
```

**Inside the package (relative imports):**
```python
from ..interfaces import Segment, Layer
from ..providers import DialogProvider
from ..model import WorkpieceFactory
```

### Core Providers (Dependency Injection)

All external dependencies are injected via provider singletons in `src/frontend/contour_editor/providers/`:

1. **DialogProvider** - Dialogs for user feedback (default: QMessageBox)
   ```python
   from frontend.contour_editor import DialogProvider
   DialogProvider.get().show_error(parent, "Title", "Message", "Info")
   DialogProvider.get().show_warning(parent, "Title", "Message") # Returns bool
   ```

2. **WidgetProvider** - Custom input widgets (default: QDoubleSpinBox, QSpinBox, QLineEdit)
   ```python
   from frontend.contour_editor import WidgetProvider
   spinbox = WidgetProvider.get().create_double_spinbox(parent)
   lineedit = WidgetProvider.get().create_lineedit(parent)
   ```
   **Note**: Plugin registers VirtualKeyboard widgets (FocusDoubleSpinBox, FocusSpinBox, FocusLineEdit) for touch-screen support.

3. **IconProvider** - Icon resources (default: loads from `contour_editor/icons/`)
   ```python
   from frontend.contour_editor import IconProvider
   icon = IconProvider.get().get_icon('pickup_point')
   ```

4. **WorkpieceFormProvider** - Workpiece creation form (default: None, must be injected)
   ```python
   from frontend.contour_editor import WorkpieceFormProvider
   form = WorkpieceFormProvider.get().create_form(parent)
   ```

5. **SegmentManagerProvider** - Backend for segment/curve management (default: BezierSegmentManager)
   ```python
   from frontend.contour_editor import SegmentManagerProvider
   manager = SegmentManagerProvider.get_instance().create_manager()
   ```

6. **SettingsProviderRegistry** - Settings definitions (must be registered by application)
   ```python
   from frontend.contour_editor import SettingsProviderRegistry
   SettingsProviderRegistry.get_instance().set_provider(my_settings_provider)
   ```

### Integration Pattern for Plugins

When integrating contour_editor in a plugin, register custom providers during plugin initialization:

```python
# In plugin initialize() method:
from frontend.contour_editor import (
    DialogProvider, WidgetProvider, IconProvider, WorkpieceFormProvider,
    SegmentManagerProvider, SettingsProviderRegistry
)

# CRITICAL: Register SegmentManagerProvider FIRST - required before creating ContourEditor
from plugins.core.contour_editor.adapters.BezierSegmentAdapter import BezierSegmentManagerAdapter
SegmentManagerProvider.get_instance().set_manager_class(BezierSegmentManagerAdapter)

# Custom dialog with styled UI
from frontend.dialogs.CustomFeedbackDialog import CustomFeedbackDialog, DialogType

class CustomDialogProvider:
    def show_warning(self, parent, title, message, info_text=""):
        dialog = CustomFeedbackDialog(parent, title, message, info_text, DialogType.WARNING)
        return dialog.exec() == QDialog.DialogCode.Accepted
    # ... implement other methods

DialogProvider.get().set_custom_provider(CustomDialogProvider())

# Virtual keyboard widgets for touch screens
from frontend.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox, FocusSpinBox, FocusLineEdit

class VirtualKeyboardWidgetFactory:
    def create_double_spinbox(self, parent=None):
        return FocusDoubleSpinBox(parent)
    def create_spinbox(self, parent=None):
        return FocusSpinBox(parent)
    def create_lineedit(self, parent=None):
        return FocusLineEdit(parent)

WidgetProvider.get().set_custom_factory(VirtualKeyboardWidgetFactory())

# Workpiece creation form
from frontend.forms.CreateWorkpieceForm import CreateWorkpieceForm

class GlueWorkpieceFormFactory:
    def create_form(self, parent=None):
        form = CreateWorkpieceForm(parent=parent)
        return form

WorkpieceFormProvider.get().set_factory(GlueWorkpieceFormFactory())

# Custom segment backend (e.g., for different curve types)
SegmentManagerProvider.get_instance().set_manager_class(MyCustomSegmentManager)

# Application-specific settings
SettingsProviderRegistry.get_instance().set_provider(GlueSettingsProvider())
```

### Standalone Usage

For standalone demo/testing without application integration, use defaults:

```python
from PyQt6.QtWidgets import QApplication
from frontend.contour_editor import MainApplicationFrame

app = QApplication([])
editor = MainApplicationFrame()  # Uses all default providers
editor.show()
app.exec()
```

### Data Types

Core data types are defined in `src/frontend/contour_editor/interfaces/`:
- **Segment** - Individual curve/line with control points
- **Layer** - Collection of segments (Workpiece, Contour, Fill)
- **ISegmentManager** - Interface all backends must implement

## Architecture Documentation

For deeper understanding, see:
- `CLAUDE.md` - Extended architectural notes (legacy, will be consolidated)
- `src/core/` - Core interfaces and abstractions
- `src/modules/` - Domain-specific implementations
- Test files - Best examples of usage patterns

