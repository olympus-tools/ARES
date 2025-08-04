# ARES
Automated Rapid Embedded Simulation

* [Installation](#installation)
    * [Windows](#windows)
    * [Linux](#linux)
* [Bug & Feature Report](#send-us-an-issue)
    * [Bug Report](#bug-report)
    * [Feature Request](#feature-request)
* [Workflows](#workflows)
    * [General Workflow Rules](#general-workflow-rules)
    * [Function Blocks](#function-blocks)
    * [Example Workflows](#example-workflows)

## Installation

Windows:
- execute [install.bat](install.bat)

Linux:
- execute [install.sh](install.sh)

## Send us an issue

Use this templates to report us your tasks:
- [Bug_Report](https://github.com/AndraeCarotta/ARES/issues/new?template=bug_report.md)
- [Feature_Request](https://github.com/AndraeCarotta/ARES/issues/new?template=feature_request.md)

## Workflows

### General Workflow Rules

TODO: Workflows have to be implemented like...

### Workflow Elements

#### data_source

TODO: Reading and writing data sources in different file formats (currently only mf4 is implemented)

#### parameters

TODO: Reading and wrtiging datasets in different file formats (currently onfly dcm is implemented)

#### sim_unit

TODO: Simulation unit of some software. Could be a executable, fmu,...

#### custom

TODO: e.g. Optimization, Plotting, Testing

### Example Workflows

#### Open-Loop Simulation

```mermaid
flowchart LR

    PARAM1(Parameters 1) --> SWU1(SW Unit 1)
    PARAM1 --> SWU2(SW Unit 2)
    MEAS1(DataSource 1) --> SWU1
    SWU1 --> SWU2
    SWU1 --> PL1(Plot 1)
    SWU2 --> MEAS2(DataSource 2)
    SWU2 --> TS1(Testspecifiaction 1)

    PARAM2(Parameters 2) --> SWU3(SW Unit 3)
    PARAM2 --> SWU4(SW Unit 4)
    PARAM2 --> SWU5(SW Unit 5)
    MEAS1(DataSource 1) --> SWU3
    SWU3 --> SWU4
    SWU3 --> TS1
    SWU4 --> MEAS2
    SWU4 --> SWU5

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class PARAM1 Parameters;
    class PARAM2 Parameters;
    class MEAS1 DataSource;
    class MEAS2 DataSource;
    class SWU1 SW_Unit;
    class SWU2 SW_Unit;
    class SWU3 SW_Unit;
    class SWU4 SW_Unit;
    class SWU5 SW_Unit;
    class TS1 Test;
    class PL1 Plot;

```
