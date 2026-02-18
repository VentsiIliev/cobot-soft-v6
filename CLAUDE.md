# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PyQt6-based robotic glue dispensing system with support for multiple robot types (Fairino, ZeroError) and applications. The system features computer vision-based workpiece detection, contour matching, automated glue dispensing, and pick-and-place operations.

## Commands

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run main application (default: Glue Dispensing)
python src/main.py

# Change application by editing src/main.py:
# - APPLICATION_TYPE = ApplicationType.GLUE_DISPENSING  (uses Fairino robot)
# - APPLICATION_TYPE = ApplicationType.PAINT_APPLICATION  (uses ZeroError robot)
# - APPLICATION_TYPE = ApplicationType.TEST_APPLICATION  (uses test robot)
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m e2e            # End-to-end tests only
pytest -m pause_resume   # Pause/resume functionality tests
pytest -m multi_path     # Multi-path operation tests

# Run tests for a specific module
pytest tests/glue_process/

# Run a single test file
pytest tests/glue_process/integration/test_pause_resume_scenarios.py -v

# Run with verbose output and stop on first failure
pytest -v -x

# Show slowest tests
pytest --durations=10
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Main dependencies:
# - PyQt6: GUI framework
# - opencv-python: Computer vision
# - numpy, pandas: Data processing
# - ezdxf: DXF file handling
# - flask: REST API
# - minimalmodbus: Industrial communication
# - matplotlib, pyqtgraph, seaborn: Visualization
# - scikit-learn, scikit-image: ML and image processing
```

## High-Level Architecture

### Architectural Layers

The codebase follows a **layered architecture** with clear separation of concerns:

```
Frontend (PyQt6 GUI + Plugins)
    ↓
Communication Layer (API Gateway)
    ↓
Applications (Glue, Paint, Test)
    ↓
Core Services (Robot, Vision, Settings, State Management)
    ↓
Modules (Vision System, Contour Matching, Calibration)
    ↓
Libraries (Robot SDKs, PLVision)
```

### Key Directories

- **`src/frontend/`** - Qt6 GUI, main window, plugins, widgets, contour editor
- **`src/applications/`** - Application implementations (glue_dispensing_application, edge_painting_application, test_application)
- **`src/communication_layer/`** - API gateway with request dispatcher and REST endpoints
- **`src/core/`** - Core services: robot service, vision service, settings service, state management, application factory
- **`src/modules/`** - Domain modules: vision system, contour matching, robot calibration, shape matching training, modbus communication
- **`src/plugins/`** - Plugin system with plugin manager, loader, and registry
- **`src/libs/`** - External libraries: Fairino robot SDK, PLVision library

## Application Factory Pattern

The system uses a **factory pattern** to create and manage different applications:

- **ApplicationContext** (`src/core/application/ApplicationContext.py`) - Singleton that provides global application context
- **ApplicationFactory** (`src/core/application_factory.py`) - Creates robot services and applications based on metadata
- **Application Types** are defined in `BaseRobotApplication.ApplicationType` enum
- Each application declares its **robot type**, **dependencies**, and **required plugins** in metadata

Applications are switched dynamically via `application_factory.switch_application(app_type)`, which:
1. Creates/retrieves application instance
2. Creates robot service based on application metadata (Fairino, ZeroError, or Test robot)
3. Loads required plugins for the application

## Plugin Architecture

### How Plugins Work

The plugin system allows extending the UI without modifying core code:

1. **Discovery**: `PluginManager` scans `src/plugins/core/` for `plugin.json` metadata files
2. **Loading**: Plugins are loaded by category (CORE → FEATURE → TOOL → EXTENSION) to resolve dependencies
3. **Initialization**: Each plugin implements `IPlugin` interface with `initialize()` and `create_widget()` methods
4. **Registration**: Loaded plugins are registered in `PluginRegistry` for lifecycle management

### Plugin Interface

Every plugin must implement (`src/plugins/base/plugin_interface.py`):
- `metadata: PluginMetadata` - Name, version, dependencies, permissions
- `initialize(controller_service)` - Setup with backend services
- `create_widget(parent)` - Create main UI widget
- `cleanup()` - Resource cleanup

### Available Plugins

Core plugins include:
- Dashboard - Main operation view
- Settings - System configuration
- Gallery - Workpiece library
- Contour Editor - Path editing
- Calibration - Robot/camera calibration
- User Management - User authentication
- Glue Cell Settings - Glue configuration
- Modbus Settings - PLC communication

## State Management System

The system uses a **three-layer state hierarchy** for coordinating complex operations:

### Layer 1: Operation State
**Location**: `src/core/operation_state_management.py`

Operations (`IOperation` base class) follow a lifecycle:
```
INITIALIZING → STARTING → (PAUSED) → COMPLETED/STOPPED/ERROR
```

Concrete implementations:
- `GlueDispensingOperation` - Glue spraying workflow with state machine
- `PickAndPlaceOperation` - Workpiece nesting/placement workflow

### Layer 2: Application State
**Location**: `src/core/application_state_management.py`

`ApplicationStateManager` aggregates operation and system states:
```
INITIALIZING → IDLE ↔ STARTED ↔ PAUSED → ERROR/STOPPED
```

Rules:
- Any ERROR → ApplicationState.ERROR
- Operation PAUSED → ApplicationState.PAUSED
- Operation COMPLETED/STOPPED → ApplicationState.IDLE
- Default → ApplicationState.STARTED

### Layer 3: System State
**Location**: `src/core/system_state_management.py`

`SystemStateManager` aggregates service states using priority:
```
Priority: ERROR(4) > STOPPED(3) > PAUSED(2) > STARTED(1) > IDLE(0)
```

Services register their state (e.g., RobotService, VisionService), and system state is computed from highest priority service state.

### Message Broker

**Location**: `src/modules/shared/MessageBroker.py`

All state changes are published via **topic-based pub/sub** using `MessageBroker` singleton:
- `SystemTopics.OPERATION_STATE` - Operation state changes
- `SystemTopics.APPLICATION_STATE` - Application state changes
- `SystemTopics.SYSTEM_STATE` - System state changes
- `RobotTopics.*` - Robot service events
- `VisionTopics.*` - Vision service events

Components subscribe to topics via `SubscriptionManager` which handles automatic cleanup.

## Communication Layer

### API Gateway Architecture

**Location**: `src/communication_layer/api_gateway/`

Request flow:
```
UIController → DomesticRequestSender → RequestHandler → Controllers → Services
```

- **RequestHandler** (`dispatch/main_router.py`) - Central dispatcher routing requests to controllers
- **Controllers** - Handle specific domains (Robot, Camera, Workpiece, Settings)
- **Endpoints** - REST-like endpoint definitions in `api/v1/endpoints/`

### Available Endpoints

Key endpoint categories (`src/communication_layer/api/v1/endpoints/`):
- `operations_endpoints.py` - Start, stop, pause, resume, calibrate, clean
- `robot_endpoints.py` - Movement, position, status
- `camera_endpoints.py` - Camera control, capture, calibration
- `settings_endpoints.py` - Settings get/update
- `workpiece_endpoints.py` - Workpiece CRUD
- `glue_endpoints.py` - Glue-specific operations
- `modbus_endpoints.py` - PLC communication

## Glue Dispensing Process

### State Machine

**Location**: `src/applications/glue_dispensing_application/glue_process/`

The glue process uses an `ExecutableStateMachine` with 23 states:

```
IDLE → STARTING → MOVING_TO_FIRST_POINT → EXECUTING_PATH
    → PUMP_INITIAL_BOOST
    → STARTING_PUMP_ADJUSTMENT_THREAD
    → SENDING_PATH_POINTS
    → WAIT_FOR_PATH_COMPLETION
    → TRANSITION_BETWEEN_PATHS
    → [loop or] COMPLETED

PAUSED ↔ Any pausable state
ERROR ← Any state (on failure)
```

### Key Components

- **`GlueDispensingOperation`** - Main operation class implementing `IOperation`
- **`ExecutionContext`** - Holds operation state (paths, settings, current position, pump thread)
- **`PumpController`** - Controls motor speed with ramp-up/ramp-down
- **`dynamicPumpSpeedAdjustment`** - Background thread for real-time pump speed adjustment
- **State Handlers** (`state_handlers/`) - 11 handler modules for state transitions

### Pause/Resume System

The system supports **5 pause scenarios** with context preservation:

1. **MOVING_TO_FIRST_POINT** - Save state, retry movement on resume
2. **EXECUTING_PATH** - Save current point index, continue from that point
3. **WAIT_FOR_PATH_COMPLETION** - Capture pump thread progress
4. **SENDING_PATH_POINTS** - Save point being sent
5. **TRANSITION_BETWEEN_PATHS** - Skip to next path on resume

### Configuration

Key settings (`ExecutionContext` and glue settings):
- `USE_SEGMENT_SETTINGS` - Use per-segment settings vs. global
- `TURN_OFF_PUMP_BETWEEN_PATHS` - Turn pump off/on between paths
- `ADJUST_PUMP_SPEED_WHILE_SPRAY` - Dynamic pump speed adjustment
- `MOTOR_SPEED`, `FORWARD_RAMP_STEPS`, `INITIAL_RAMP_SPEED` - Motor control parameters

## Vision System & Contour Matching

### Vision Service

**Location**: `src/core/services/vision/VisionService.py`

The `VisionService` extends `VisionSystem` base class and provides:
- Camera frame capture and queue management
- Contour detection via OpenCV
- Workpiece filtering by area
- ArUco marker detection
- QR code scanning
- Camera-to-robot coordinate transformation

Key managers:
- **CameraInitializer** - Camera setup with retry logic
- **DataManager** - Load calibration data
- **BrightnessManager** - Auto brightness adjustment (PID control)
- **StateManager** - Publish vision service state

### Contour Matching

**Location**: `src/modules/contour_matching/CompareContours.py`

The contour matching pipeline:
1. Select matching strategy (Geometric or ML-based)
2. Match detected contours to known workpieces
3. Align contours geometrically
4. Return `MatchInfo` objects with workpiece-contour pairs

**Strategies**:
- **GeometricMatchingStrategy** - Shape similarity using OpenCV contour matching
- **MLMatchingStrategy** - Trained neural network on shape features

### Calibration Data

Calibration files stored in `applications/{app}/storage/data/calibration/`:
- `camera_matrix.json` - Camera intrinsic matrix
- `distortion_coefficients.json` - Lens distortion
- `camera_to_robot_matrix.json` - Hand-eye transformation
- `work_area.json` - Workspace boundaries

## Settings System

### Settings Service

**Location**: `src/core/services/settings/SettingsService.py`

The settings system uses **Repository Pattern** with type-specific strategies:

- **Repositories** - Implement `ISettingsRepository` for persistence (camera, robot_config, robot_calibration, custom)
- **Update Strategies** - Type-specific validation and update logic
- **Settings Registry** - `ApplicationSettingsRegistry` for custom application settings

### Settings Storage

Per-application settings structure:
```
src/applications/{app_name}/storage/
├── settings/
│   ├── camera_settings.json
│   ├── robot_config.json
│   ├── robot_calibration_settings.json
│   ├── modbus_config.json
│   ├── glue_cell_config.json
│   └── contour_matching_settings.json
├── data/
│   ├── workpieces/
│   ├── calibration/
│   └── users/
└── logs/
```

### Adding Custom Settings

1. Create settings class (JSON-serializable)
2. Implement `ISettingsRepository` for persistence
3. Register repository in `SettingsRepositoryRegistry`
4. Optionally create update strategy extending `SettingsUpdateStrategy`
5. Register settings type in `ApplicationSettingsRegistry`

## Robot Service Architecture

### Robot Service

**Location**: `src/core/services/robot_service/impl/base_robot_service.py`

The `RobotService` wraps vendor-specific robot APIs:

```
RobotService (base implementation)
    ├── robot: IRobot (vendor-specific wrapper)
    ├── robot_state_manager: monitors robot state
    ├── message_publisher: publishes state changes
    ├── state_manager: service state management
    ├── tool_manager: gripper/vacuum/laser control
    └── subscription_manager: event subscriptions
```

### Robot Types

**Location**: `src/core/model/robot/robot_factory.py`

- **Fairino** - Chinese industrial robot (Glue Dispensing app) - SDK in `src/libs/fairino/`
- **ZeroError** - Precision robot (Paint app)
- **Test** - Simulated robot (Test app)

### Key Operations

- Movement: `moveToStartPosition()`, `moveCartesian()`, `moveLinear()`
- Tool control: `pickupGripper()`, `releaseGripper()`, `controlVacuum()`
- State: `get_current_position()`, `get_current_velocity()`, `stop_motion()`
- Cancellation: `CancellationToken` for operation control

## Design Patterns

### Key Patterns Used

1. **Singleton** - MessageBroker, ApplicationContext, VisionService, service registries
2. **Factory** - ApplicationFactory, RobotFactory, PluginManager
3. **Strategy** - SettingsUpdateStrategy, MatchingStrategy (Geometric vs ML)
4. **Observer/Pub-Sub** - MessageBroker with topic-based communication
5. **Template Method** - IOperation base class defines operation lifecycle
6. **State Machine** - ExecutableStateMachine for glue/pick-and-place processes
7. **Repository** - ISettingsRepository for settings persistence
8. **Adapter** - RobotService adapts different robot types to common interface
9. **Registry** - PluginRegistry, SettingsRepositoryRegistry, ApplicationSettingsRegistry

## Important Notes

### Application Context

`ApplicationContext` is a singleton that MUST be set before initializing services:
```python
ApplicationContext.set_current_application(ApplicationType.GLUE_DISPENSING)
```

This determines:
- Which application is active
- Settings file paths (app-specific)
- Storage locations
- Required plugins to load

### Threading Considerations

- Vision service runs camera in background thread with frame queue
- Glue process can spawn pump adjustment thread (`dynamicPumpSpeedAdjustment`)
- Always use `CancellationToken` for safe operation cancellation
- State changes are thread-safe via MessageBroker

### Error Handling

- State machines transition to ERROR state on exceptions
- Services publish ERROR service state when failing
- SystemStateManager aggregates errors to system level
- Always stop robot motion and turn off pump/generator on error

### Modbus Communication

**Location**: `src/modules/modbusCommunication/`

The system can communicate with PLCs via Modbus RTU:
- Glue types mapped to Modbus coil addresses
- Motor speed control via registers
- Configuration in `modbus_config.json`

### Testing Guidelines

- Tests are organized in `tests/` with markers: `unit`, `integration`, `e2e`, `pause_resume`, `multi_path`
- Mock all external services (RobotService, GlueSprayService, MessageBroker) in tests
- Use pytest fixtures from `conftest.py` for test data
- Aim for 85%+ code coverage
- Run specific markers: `pytest -m pause_resume` for pause/resume tests

## Common Tasks

### Adding a New Application

1. Create `src/applications/new_app/` directory
2. Implement `BaseRobotApplication` subclass
3. Define `get_metadata()` returning `ApplicationMetadata` with robot type and plugin dependencies
4. Implement `operation` property and `_on_operation_start()` method
5. Register in `ApplicationFactory`: `application_factory.register_application(app_type, app_class)`

### Adding a New Plugin

1. Create plugin folder in `src/plugins/core/new_plugin/`
2. Create `plugin.json` with metadata (name, category, dependencies)
3. Implement `IPlugin` interface
4. Implement `initialize(controller_service)` to inject backend dependencies
5. Implement `create_widget(parent)` to return main UI widget
6. PluginManager will auto-discover it on next launch

### Adding a New Robot Type

1. Implement `IRobot` interface wrapping vendor SDK
2. Add robot wrapper to `src/core/model/robot/`
3. Register in `RobotFactory` (`robot_factory.py`)
4. Update application metadata to reference new `RobotType`
5. ApplicationFactory will create appropriate robot service

### Modifying State Machine Logic

When modifying glue process states:
1. Update `GlueProcessState` enum if adding states
2. Add/modify state handler in `state_handlers/`
3. Update transition rules in state machine
4. **CRITICAL**: Update pause/resume logic if state is pausable
5. Add tests in `tests/glue_process/`
6. Test all 5 pause scenarios remain functional

### Debugging State Transitions

Enable debug logging for state machines:
1. Set `debug=True` in `ExecutableStateMachine` constructor
2. Check `ExecutionContext.to_debug_dict()` for context state
3. Debug files are saved in `glue_process/debug/` (JSON format with timestamps)
4. Subscribe to state topics via MessageBroker to observe transitions
5. Check `tests/glue_process/` for integration tests demonstrating expected flow