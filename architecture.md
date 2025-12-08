# ARES Architecture

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Class Structure](#3-class-structure)
   - 3.1 [Orchestration Layer](#31-orchestration-layer)
   - 3.2 [Plugin Layer](#32-plugin-layer)
   - 3.3 [Interface Layer](#33-interface-layer)
   - 3.4 [Base Types](#34-base-types)
4. [Key Design Decisions](#4-key-design-decisions)

---

## 1. Overview

ARES (Automated Rapid Embedded Simulation) is structured in four main layers:
1. **Orchestration** - Pipeline and workflow execution
2. **Base Types** - Core data structures (signal, parameter)
3. **Interfaces** - File I/O and data management
4. **Plugins** - Processing and transformation logic

---

## 2. System Architecture

```mermaid
architecture-beta
    group ares_orchestration(server)[Orchestration Layer]
    service pipeline(server)[Pipeline] in ares_orchestration
    service workflow(disk)[Workflow] in ares_orchestration

    group ares_base(server)[Base Layer]
    service data_element(disk)[Signal] in ares_base
    service parameter_element(disk)[Parameter] in ares_base

    group ares_interface(server)[Interface Layer]
    service data_interface(server)[Data Handler] in ares_interface
    service parameter_interface(server)[Parameter Handler] in ares_interface

    group ares_plugin(server)[Plugin Layer]
    service sim_unit(database)[SimUnit] in ares_plugin
    service custom_plugins(database)[Custom Plugins] in ares_plugin

    pipeline:L -- R:workflow
    pipeline:T -- B:parameter_interface
    pipeline:T -- B:data_interface
    pipeline:T -- B:sim_unit
    data_interface:L -- R:data_element
    parameter_interface:L -- R:parameter_element
    sim_unit:T -- B:data_interface
    sim_unit:T -- B:parameter_interface
```

**Legend:**
- 🖥️ **server**: Processing components
- 💾 **disk**: Data storage/files
- 🗄️ **database**: Executable plugins

**Architecture Layers:**
1. **Orchestration**: Pipeline executes workflow definitions
2. **Plugin**: Processes data using loaded interfaces
3. **Interface**: Manages I/O with flyweight caching
4. **Base**: Fundamental data structures

---

## 3. Class Structure

### 3.1 Orchestration Layer

```mermaid
---
title: Orchestration Layer
---
classDiagram
    class Pipeline{
        <<function>>
        +execute(str wf_path, str output_dir, Dict meta_data)
    }

    class Workflow{
        +str file_path
        +Dict workflow
        +List~str~ workflow_sinks
        +load(str file_path) Dict
        +save(str output_dir)
    }

    Pipeline --> Workflow : loads & executes
    Pipeline --> AresParamInterface : orchestrates
    Pipeline --> AresDataInterface : orchestrates
    Pipeline --> AresPluginInterface : calls
```

**Orchestration Flow:**
1. Pipeline loads Workflow from JSON file
2. Identifies workflow sinks (end points)
3. Iterates through workflow elements in dependency order
4. Dispatches to appropriate handlers (parameter, data, plugin)
5. Tracks hash-based dependencies for caching
6. Saves updated workflow with execution metadata

### 3.2 Plugin Layer

```mermaid
---
title: Plugin Layer
---
classDiagram
    class AresPluginInterface{
        <<function>>
        +execute(Dict plugin_input)
    }

    class SimUnit{
        +str element_name
        +str file_path
        +str dd_path
        +DataDictionaryModel _dd
        +CDLL _library
        +Dict _dll_interface
        +CFUNCTYPE _sim_function
        +run_simulation(List~AresSignal~ data, List~AresParameter~ parameter) Dict
        -_load_and_validate_dd(str dd_path) DataDictionaryModel
        -_load_library() CDLL
        -_setup_c_interface() Dict
        -_setup_sim_function() CFUNCTYPE
        -_map_sim_input(Dict input, int time_steps) Dict
        -_write_dll_interface(Dict input, int time_step_idx)
        -_read_dll_interface() Dict
    }

    class ares_plugin{
        <<entrypoint>>
        +execute(Dict plugin_input)
    }

    class CustomPlugin{
        <<future>>
    }

    note for CustomPlugin "Additional plugins can be\nadded by implementing\nthe ares_plugin(plugin_input)\nentrypoint function"

    AresPluginInterface --> ares_plugin : loads & calls
    ares_plugin --> SimUnit : uses
    ares_plugin --> AresDataInterface : uses
    ares_plugin --> AresParamInterface : uses
```

**Plugin Architecture:**
- **AresPluginInterface**: Dynamic plugin loader function using `importlib`
- **Plugin Entrypoint**: Each plugin module must provide `ares_plugin(plugin_input)` function
- **SimUnit**: Built-in plugin for C/C++ simulation unit execution via ctypes
- **Extensibility**: Custom plugins can be added without modifying core code

**Plugin Workflow:**
1. AresPluginInterface loads plugin module from file path
2. Calls plugin's `ares_plugin(plugin_input)` entrypoint
3. Plugin receives data/parameter interfaces via `plugin_input` dict
4. Plugin processes data and optionally creates new interface instances
5. Results are cached in interface flyweight pattern

### 3.3 Interface Layer

```mermaid
---
title: Interface Layer
---
classDiagram
    class ares_data_interface{
        <<interface>>
        +create(str file_path)$
        +get() list~ares_signal~*
        +add(list~ares_signal~)*
        +save(str output_path)*
    }

    class ares_parameter_interface{
        <<interface>>
        +Dict~str, ares_parameter_interface~ cache$
        +Dict~str, type~ _handlers$
        +create(str file_path)$
        +register(str extension, type handler)$
        +wf_element_handler(str element_name, ParameterElement element_value)$
        +get() list~ares_parameter~*
        +add(list~ares_parameter~)*
        +save(str output_path)*
    }

    class dcm_handler
    class json_handler
    class mf4_handler

    ares_parameter_interface <|.. dcm_handler : implements
    ares_parameter_interface <|.. json_handler : implements
    ares_data_interface <|.. mf4_handler : implements
    ares_parameter_interface o-- ares_parameter : manages
    ares_data_interface o-- ares_signal : manages
```

**Design Patterns:**
- **Factory Pattern**: `create()` method selects handler by file extension
- **Flyweight Pattern**: Shared instances via content hash (parameters only)
- **Strategy Pattern**: Pluggable file format handlers

### 3.4 Base Types

```mermaid
---
title: Core Data Types
---
classDiagram
    class ares_signal{
        <<base type>>
        +String label
        +Array~float~ timestamps
        +Array~Any~ values
        +String unit
        +resample(int step_size_ms)
    }

    class ares_parameter{
        <<base type>>
        +String label
        +String description
        +String unit
        +Array~Any~ value
    }
```

---

## 4. Key Design Decisions

### 4.1 Interface Abstraction
All file I/O operations go through interfaces, enabling:
- Format-agnostic processing
- Easy addition of new file formats
- Consistent caching and validation

### 4.2 Immutable Data Flow
- Interfaces use flyweight pattern (parameters)
- Hash-based caching prevents duplicate data
- Workflow steps reference data by hash

### 4.3 Plugin Architecture
- Plugins are self-contained processing units
- Standard `execute()` interface enables composition
- Easy to add custom plugins without modifying core
