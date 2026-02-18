# Workpiece Editor Tests
Comprehensive test suite for the workpiece_editor package.
## Test Structure
```
tests/workpiece_editor/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_workpiece_adapter.py      # WorkpieceAdapter tests (11 tests)
├── test_workpiece_manager.py      # WorkpieceManager tests (10 tests)
├── test_workpiece_builder.py      # WorkpieceEditorBuilder tests (12 tests)
├── test_workpiece_models.py       # Model tests (12 tests)
├── test_handlers.py               # Handler tests (8 tests)
└── test_integration.py            # Integration tests (4 tests)
```
## Coverage
### WorkpieceAdapter Tests (test_workpiece_adapter.py)
- ✅ Layer constants validation
- ✅ from_workpiece() basic conversion
- ✅ from_workpiece() with spray patterns
- ✅ to_workpiece_data() basic conversion
- ✅ to_workpiece_data() empty data handling
- ✅ to_workpiece_data() with spray patterns
- ✅ normalize_layer_data() functionality
- ✅ segment_to_contour_array() conversion
- ✅ print_summary() output
### WorkpieceManager Tests (test_workpiece_manager.py)
- ✅ Initialization
- ✅ load_workpiece() functionality
- ✅ export_editor_data()
- ✅ export_workpiece_data()
- ✅ init_contour() with single/multiple layers
- ✅ clear_workpiece()
- ✅ set_current_workpiece()
### WorkpieceEditorBuilder Tests (test_workpiece_builder.py)
- ✅ Initialization
- ✅ Fluent API (with_parent, with_segment_manager, etc.)
- ✅ build() creates workpiece manager
- ✅ build() creates handlers
- ✅ load_workpiece() before/after build
- ✅ Error handling
### Model Tests (test_workpiece_models.py)
- ✅ WorkpieceField creation
- ✅ BaseWorkpiece abstract class
- ✅ GenericWorkpiece CRUD operations
- ✅ GenericWorkpiece get methods (contour, settings, patterns)
- ✅ WorkpieceFactory.create_workpiece()
### Handler Tests (test_handlers.py)
- ✅ load_workpiece() basic functionality
- ✅ StartHandler initialization and handling
- ✅ CaptureHandler initialization and handling
- ✅ Data validation
### Integration Tests (test_integration.py)
- ✅ Full workflow: build -> load -> export
- ✅ Adapter roundtrip conversion
- ✅ WorkpieceManager workflow
- ✅ Layer name compatibility
## Running Tests
```bash
# Run all workpiece_editor tests
python3 -m pytest tests/workpiece_editor/ -v
# Run specific test file
python3 -m pytest tests/workpiece_editor/test_workpiece_adapter.py -v
# Run with coverage
python3 -m pytest tests/workpiece_editor/ --cov=src/workpiece_editor --cov-report=html
# Run integration tests only
python3 -m pytest tests/workpiece_editor/test_integration.py -v
```
## Test Statistics
- **Total Tests**: 57
- **Coverage Areas**:
  - adapters/ (WorkpieceAdapter)
  - managers/ (WorkpieceManager)
  - builders/ (WorkpieceEditorBuilder)
  - models/ (BaseWorkpiece, GenericWorkpiece, WorkpieceFactory, WorkpieceField)
  - handlers/ (load_workpiece, StartHandler, CaptureHandler)
## Architecture Validation
Tests verify that:
1. ✅ workpiece_editor correctly builds on top of contour_editor
2. ✅ WorkpieceAdapter properly converts between formats
3. ✅ Builder pattern correctly injects workpiece functionality
4. ✅ Layer names are properly handled (Workpiece/Main compatibility)
5. ✅ No circular dependencies
