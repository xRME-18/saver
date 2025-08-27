# Saver - Context-Aware Text Capture System

![Tests](https://img.shields.io/badge/tests-199%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-99.4%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.11+-blue)

A Python application that automatically captures and organizes your typing across different applications, designed to help you save frequently used text for LLM interactions and productivity workflows.

## Features

- **Per-Application Text Capture**: Automatically separates text by the application you're typing in
- **Automatic Saving**: Saves captured text every 5 minutes and on exit
- **Smart App Detection**: Uses macOS Quartz API for accurate active window detection
- **Configurable Filtering**: Include/exclude specific applications from capture
- **SQLite Storage**: Local database storage with statistics and search capabilities
- **Privacy-First**: All data stored locally, with built-in security exclusions
- **Cross-Platform**: Supports macOS, Windows, and Linux

## Installation

### Requirements

- Python 3.11 or higher
- uv package manager

### Setup

```bash
# Clone or navigate to the project directory
cd saver

# Install dependencies
uv sync

# Run the application
uv run python -m saver
```

## Usage

### Start Capturing

```bash
uv run python -m saver
```

This will start monitoring your keystrokes across applications. Press `Ctrl+C` to stop.

### Check Statistics

```bash
uv run python -m saver status
```

Shows total captures, character counts, word counts, and top applications.

### Help

```bash
uv run python -m saver help
```

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
capture:
  save_interval_seconds: 300  # 5 minutes
  min_chars_threshold: 10     # Minimum characters to save
  enabled: true

apps:
  mode: "exclude"  # "include" or "exclude"
  include_list: []
  exclude_list:
    - "1Password"
    - "Keychain Access"
    - "System Preferences"
    - "Calculator"

storage:
  database_path: "data/captures.db"
  auto_cleanup_days: 30
```

### App Filtering Modes

- **Include Mode**: Only capture from apps in `include_list`
- **Exclude Mode**: Capture from all apps except those in `exclude_list`

## Example Output

When you stop the application, you'll see what was captured:

```
=== Captured Content by App ===

Safari:
  Characters: 45
  Words: 8
  Content: 'now I\'m testing it by typing this sentence im in Safari'

Notion:
  Characters: 67
  Words: 12
  Content: 'taking notes about the new feature I want to implement'

Terminal:
  Characters: 23
  Words: 4
  Content: 'uv run python -m saver'
```

## Privacy & Security

- **Local Storage Only**: All data stays on your machine
- **Smart Exclusions**: Automatically excludes password managers and system apps
- **Configurable**: Full control over which applications to monitor
- **Minimum Thresholds**: Only saves content above configurable character limits

## Common Use Cases

- **LLM Context Management**: Save frequently used prompts and context information
- **Documentation**: Capture notes and ideas as you work across different applications
- **Research**: Organize information gathered from various sources
- **Productivity Tracking**: Understand your typing patterns across applications

## Permissions

On macOS, you'll need to grant **Accessibility** permissions when first running the application. This allows the system to:

- Detect active applications
- Capture keyboard input
- Monitor window changes

## Troubleshooting

### App Detection Issues

If app switching isn't detected properly, the system uses multiple detection methods:

1. Quartz API (primary method for macOS)
2. NSWorkspace API (fallback)
3. Platform-specific alternatives for Windows/Linux

### No Text Captured

Check that:

1. The application is in your include list (or not in exclude list)
2. You've typed more than the minimum character threshold
3. Accessibility permissions are granted

## Development

### Project Structure

```
saver/
├── src/saver/
│   ├── key_listener.py     # Keyboard capture
│   ├── app_monitor.py      # Active app detection
│   ├── buffer_manager.py   # Per-app text buffers
│   ├── storage_handler.py  # SQLite database operations
│   ├── config.py          # Configuration management
│   └── main.py            # Main application controller
├── data/
│   └── captures.db        # SQLite database
├── config.yaml            # User configuration
└── pyproject.toml         # Python project configuration
```

### Dependencies

- `pynput`: Cross-platform keyboard/mouse input monitoring
- `pyobjc-framework-cocoa`: macOS app detection
- `pyyaml`: Configuration file parsing

## Testing & Development Guidelines

### 🧪 Running Tests

**⚠️ IMPORTANT: Always run tests before committing any changes!**

#### Quick Test Commands
```bash
# Run all tests (recommended before every commit)
uv run pytest

# Run tests with coverage report
uv run pytest --cov=src/saver --cov-report=term-missing

# Run tests verbosely to see detailed output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/core/test_buffer_manager.py

# Stop on first failure (useful during development)
uv run pytest -x
```

#### Coverage Requirements
This project maintains **99.4% test coverage**. New code should include comprehensive tests:

```bash
# Check coverage and ensure it stays above 95%
uv run pytest --cov=src/saver --cov-report=term-missing --cov-fail-under=95

# Generate detailed HTML coverage report
uv run pytest --cov=src/saver --cov-report=html
# Open htmlcov/index.html to see detailed coverage
```

### 📋 Pre-Commit Checklist

**Before committing ANY changes, ensure:**

1. **✅ All tests pass**:
   ```bash
   uv run pytest
   ```

2. **✅ Coverage remains high** (>95%):
   ```bash
   uv run pytest --cov=src/saver --cov-report=term-missing
   ```

3. **✅ No syntax or import errors**:
   ```bash
   # Test import of main modules
   uv run python -c "from src.saver.core.capture import CaptureEngine; print('✅ Imports OK')"
   ```

4. **✅ New features have tests**: If you add new functionality, include corresponding tests

### 🎯 Test Structure

The project has comprehensive unit tests covering:

```
tests/
├── conftest.py              # Shared test fixtures
├── unit/
│   ├── core/
│   │   ├── test_buffer_manager.py    (22 tests)
│   │   ├── test_capture.py           (28 tests) 
│   │   └── test_config.py            (18 tests)
│   ├── storage/
│   │   ├── test_models.py            (12 tests)
│   │   └── test_sqlite_handler.py    (22 tests)
│   ├── monitors/
│   │   ├── test_key_listener.py      (33 tests)
│   │   └── test_app_monitor.py       (24 tests)
│   ├── utils/
│   │   └── test_platform.py          (25 tests)
│   └── test_cli.py                   (15 tests)
└── pytest.ini                       # Test configuration
```

**Total: 199 tests with 99.41% coverage** 🏆

### 🔧 Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with corresponding tests

3. **Run tests frequently during development**:
   ```bash
   # Quick test run
   uv run pytest -x -q
   
   # Test specific module you're working on
   uv run pytest tests/unit/core/test_buffer_manager.py -v
   ```

4. **Before committing, run full test suite**:
   ```bash
   # Full test run with coverage
   uv run pytest --cov=src/saver --cov-report=term-missing
   ```

5. **Commit only when all tests pass**:
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

### 🚨 Common Issues & Solutions

#### Tests Failing After Changes
```bash
# Run with detailed output to see what failed
uv run pytest -vvv --tb=long

# Run specific failing test
uv run pytest tests/unit/core/test_buffer_manager.py::TestBufferManager::test_specific_method -v
```

#### Coverage Drops Below 95%
```bash
# See which lines aren't covered
uv run pytest --cov=src/saver --cov-report=term-missing

# Generate HTML report for detailed analysis
uv run pytest --cov=src/saver --cov-report=html
# Open htmlcov/index.html
```

#### Platform-Specific Test Issues
The test suite includes mocks for all platforms (macOS, Windows, Linux). If you see platform-specific failures:

```bash
# Run tests with platform debugging
uv run pytest tests/unit/utils/test_platform.py -v -s
```

### 📝 Writing New Tests

When adding new features, follow these patterns:

```python
# Example test structure
class TestYourNewFeature:
    def setup_method(self):
        """Setup for each test"""
        self.feature = YourNewFeature()
    
    def test_normal_case(self):
        """Test the expected behavior"""
        result = self.feature.do_something("input")
        assert result == "expected_output"
    
    def test_edge_case_empty_input(self):
        """Test edge cases"""
        result = self.feature.do_something("")
        assert result is None
    
    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ValueError, match="Invalid input"):
            self.feature.do_something("invalid")
```

### ⚡ Performance Testing

```bash
# Run tests with timing information
uv run pytest --durations=10

# Profile slow tests
uv run pytest --profile
```

Remember: **Tests are documentation**. They show how your code should work and prevent regressions. Quality tests make the codebase maintainable and reliable! 🎯

## License

This project is designed for personal productivity use. Please use responsibly and in compliance with your local privacy laws.

---

**Note**: This tool is designed for legitimate productivity and context management purposes. Always ensure you have appropriate permissions before monitoring text input, especially in shared or professional environments.