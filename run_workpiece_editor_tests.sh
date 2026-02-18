#!/bin/bash
# Test runner for workpiece_editor package
echo "🔧 Workpiece Editor Test Runner"
echo "================================"
echo ""

# Setup paths
PROJECT_ROOT="/home/ilv/cobot-soft/cobot-soft-v5.1/cobot-soft-v5/cobot-glue-dispensing-v5"
TEST_DIR="tests/plugins/workpiece_editor"

# Ensure dependencies
pip install pytest pytest-cov pytest-qt >/dev/null 2>&1

# Change to project root
cd "$PROJECT_ROOT"

# Set source path for workpiece_editor module
SRC_PATH="$PROJECT_ROOT/src/plugins/core/contour_editor"
SRC_ROOT="$PROJECT_ROOT/src"
if [ -d "$SRC_PATH/workpiece_editor" ]; then
    echo "📁 Found workpiece_editor in src/plugins/core/contour_editor/"
    echo ""
else
    echo "❌ Error: Cannot find workpiece_editor module"
    echo "   Expected at: $SRC_PATH/workpiece_editor"
    exit 1
fi

# Remove __init__.py from test directory to avoid import conflicts
if [ -f "$TEST_DIR/__init__.py" ]; then
    echo "🔧 Removing conflicting __init__.py from test directory..."
    rm "$TEST_DIR/__init__.py"
fi
if [ -f "$TEST_DIR/config/__init__.py" ]; then
    rm "$TEST_DIR/config/__init__.py"
fi
if [ -f "$TEST_DIR/handlers/__init__.py" ]; then
    rm "$TEST_DIR/handlers/__init__.py"
fi
if [ -f "$TEST_DIR/ui/__init__.py" ]; then
    rm "$TEST_DIR/ui/__init__.py"
fi

# Clear Python cache to avoid stale bytecode
echo "🧹 Clearing Python cache..."
find "$SRC_PATH/workpiece_editor" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SRC_PATH/workpiece_editor" -name "*.pyc" -delete 2>/dev/null || true

echo ""

# Disable ROS pytest plugins to avoid collection errors
PYTEST_DISABLE_ROS="-p no:launch_pytest -p no:launch_testing -p no:launch_testing_ros -p no:roslaunch"

# Common pytest command with isolated environment
run_pytest() {
    PYTHONPATH="$SRC_PATH:$SRC_ROOT" PYTHONNOUSERSITE=1 python -m pytest "$@" $PYTEST_DISABLE_ROS
}

# Run all workpiece_editor tests
if [ "$1" == "all" ]; then
    echo "Running all workpiece_editor tests..."
    run_pytest "$TEST_DIR/" -v

# Run adapter tests
elif [ "$1" == "adapter" ]; then
    echo "Running WorkpieceAdapter tests..."
    run_pytest "$TEST_DIR/test_workpiece_adapter.py" -v

# Run manager tests
elif [ "$1" == "manager" ]; then
    echo "Running WorkpieceManager tests..."
    run_pytest "$TEST_DIR/test_workpiece_manager.py" -v

# Run builder tests
elif [ "$1" == "builder" ]; then
    echo "Running WorkpieceEditorBuilder tests..."
    run_pytest "$TEST_DIR/test_workpiece_builder.py" -v

# Run model tests
elif [ "$1" == "models" ]; then
    echo "Running model tests..."
    run_pytest "$TEST_DIR/test_workpiece_models.py" -v

# Run handler tests
elif [ "$1" == "handlers" ]; then
    echo "Running handler tests..."
    run_pytest "$TEST_DIR/handlers/" -v

# Run config tests
elif [ "$1" == "config" ]; then
    echo "Running config tests..."
    run_pytest "$TEST_DIR/config/" -v

# Run UI tests
elif [ "$1" == "ui" ]; then
    echo "Running UI tests..."
    run_pytest "$TEST_DIR/ui/" -v

# Run integration tests
elif [ "$1" == "integration" ]; then
    echo "Running integration tests..."
    run_pytest "$TEST_DIR/test_integration.py" -v

# Run with coverage
elif [ "$1" == "coverage" ]; then
    echo "Running workpiece_editor tests with coverage..."
    run_pytest "$TEST_DIR/" -v \
        --cov=workpiece_editor \
        --cov-report=html:htmlcov/workpiece_editor \
        --cov-report=term-missing
    echo ""
    echo "📊 Coverage report generated in htmlcov/workpiece_editor/index.html"

# Run quick smoke test
elif [ "$1" == "quick" ]; then
    echo "Running quick smoke tests..."
    run_pytest "$TEST_DIR/test_integration.py" -v -k "test_" --maxfail=1

# Run specific test file
elif [ -n "$1" ]; then
    echo "Running test file: $1"
    run_pytest "$1" -v

# Show help
else
    echo "Usage:"
    echo "  ./run_workpiece_editor_tests.sh all         - Run all workpiece_editor tests"
    echo "  ./run_workpiece_editor_tests.sh adapter     - Run WorkpieceAdapter tests"
    echo "  ./run_workpiece_editor_tests.sh manager     - Run WorkpieceManager tests"
    echo "  ./run_workpiece_editor_tests.sh builder     - Run WorkpieceEditorBuilder tests"
    echo "  ./run_workpiece_editor_tests.sh models      - Run model tests"
    echo "  ./run_workpiece_editor_tests.sh handlers    - Run handler tests"
    echo "  ./run_workpiece_editor_tests.sh config      - Run config tests"
    echo "  ./run_workpiece_editor_tests.sh ui          - Run UI tests"
    echo "  ./run_workpiece_editor_tests.sh integration - Run integration tests"
    echo "  ./run_workpiece_editor_tests.sh coverage    - Run with coverage report"
    echo "  ./run_workpiece_editor_tests.sh quick       - Run quick smoke test"
    echo "  ./run_workpiece_editor_tests.sh <file>      - Run specific test file"
    echo ""
    echo "Examples:"
    echo "  ./run_workpiece_editor_tests.sh all"
    echo "  ./run_workpiece_editor_tests.sh adapter"
    echo "  ./run_workpiece_editor_tests.sh coverage"
    echo "  ./run_workpiece_editor_tests.sh tests/plugins/workpiece_editor/test_workpiece_adapter.py"
    echo ""
    echo "📦 Test Coverage:"
    echo "   - Adapters, managers, builders, models, handlers, config, UI"
    echo ""
    echo "Note: ROS pytest plugins are automatically disabled"
fi

