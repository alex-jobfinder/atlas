# Ideal DearPyGUI Architecture

This document outlines a recommended architecture for a new GUI application built on [Dear PyGui](https://github.com/hoffstadt/DearPyGui). The goal is to provide a reusable and modular scaffold that cleanly separates presentation from business logic and promotes extensibility.

## Guiding Principles

- **Model–View–Controller (or View‑Model)**: isolate state and behavior from rendering so that logic can be unit‑tested without a running GUI.
- **Reusability**: encapsulate widgets into small, composable view components.
- **Plugin-friendly**: expose clear extension points for new tabs, tools, or data providers.
- **Scoped event dispatch**: avoid global singletons by routing signals through explicit controllers or view‑models.

## Layered Design

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│   Models   │ ←→ │ Controllers│ ←→ │    Views   │
└────────────┘    └────────────┘    └────────────┘
```

- **Models** hold domain data (projects, data sets, analysis results).
- **Controllers/View‑Models** mediate between models and Dear PyGui views, implementing business rules and emitting signals.
- **Views** are thin wrappers around Dear PyGui widgets that bind to controller state.

## ProgramWindow

The top‑level application frame is created by a `ProgramWindow` controller:

- owns the main Dear PyGui context and event loop
- assembles reusable view components: `MenuBar`, `ProjectTabBar`, dialogs
- delegates project management to a `ProjectManager` service that operates purely on models

```python
class ProgramWindow(Controller):
    def __init__(self, project_manager: ProjectManager):
        self.pm = project_manager
        self.view = ProgramWindowView(self)
```

The corresponding `ProgramWindowView` contains only Dear PyGui calls.

## ProjectTab

A `ProjectTab` controller represents an open project workspace:

- keeps a reference to a `Project` model
- exposes signals such as `data_loaded`, `analysis_updated`
- loads sub‑tabs through a plugin registry

Sub‑tabs implement a small `Tab` protocol with `controller` and `view` objects. Controllers register themselves via entry points so third‑party tabs can hook into the application without touching core code.

## Event System

Signals are dispatched through controller‑scoped emitters. A lightweight dispatcher supports chaining and middleware:

```python
dispatcher = Dispatcher()
dispatcher.add_middleware(log_events)
```

This avoids hidden global state and improves debuggability.

## Component Library

Common widgets (tables, combo boxes, dialogs) live in a shared `components` package. Each component exposes:

- a pure view class that declares Dear PyGui elements
- a companion controller that manages interaction and validation

Reuse keeps the codebase small and encourages composition.

## Plugin Architecture

- `registry.py` defines a `TabSpec` data class and a `Registry` service
- core tabs register themselves statically; external plugins register via `entry_points`
- controllers can be unregistered dynamically for test isolation

## Testing Strategy

- Models and controllers are unit‑tested with pytest
- Views are covered by lightweight smoke tests using Dear PyGui's headless mode
- Integration tests spin up a minimal ProgramWindow and simulate user actions

## Benefits

- deterministic, testable core logic
- clear boundaries enable reuse across projects
- third‑party developers can contribute new tabs or components without modifying existing code

## init_new_gui_subdir

Use the following shell function to bootstrap the folder structure and placeholder files for the architecture described above:

```bash
init_new_gui_subdir() {
  mkdir -p gui/{models,controllers,views/components,views/tabs}
  touch gui/__init__.py
  touch gui/models/__init__.py
  touch gui/controllers/{__init__.py,program_window.py,project_tab.py,registry.py}
  touch gui/views/__init__.py
  touch gui/views/components/__init__.py
  touch gui/views/tabs/__init__.py
}
```

Invoke the function once to create the directories:

```bash
init_new_gui_subdir
```
