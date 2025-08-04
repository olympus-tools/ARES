# ARES
Automated Rapid Embedded Simulation

* [Installation](#installation)
    * [Windows](#windows)
    * [Linux](#linux)
* [Bug & Feature Report](#send-us-an-issue)
    * [Bug Report](#bug-report)
    * [Feature Request](#feature-request)
* [Workflows](#workflows)
    * [Function Blocks](#function-blocks)
    * [General Workflow Rules](#general-workflow-rules)
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

### Function Blocks

#### measurement

Reading and writing data sources in different file formats (currently only mf4 is implemented)

#### dataset

Reading and wrtiging datasets in different file formats (currently onfly dcm is implemented)

#### sim_unit

Simulation unit of some software. Could be a executable, fmu,...

#### custom

e.g. Optimization, Plotting, Testing

### General Workflow Rules

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

#### Open-Loop Simulation with Parameter Optimization

```mermaid
flowchart LR

    PARAM3(Parameters 3) --> SWU6(SW Unit 6)
    PARAM3 --> OPT1(Optimization 1)
    MEAS3(DataSource 3) --> SWU6
    SWU6 --> OPT1
    OPT1 --> SWU7(SW Unit 7)
    SWU7 --> OPT1

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class PARAM3 Parameters;
    class MEAS3 DataSource;
    class SWU6 SW_Unit;
    class SWU7 SW_Unit;
    class OPT1 Optimization;

```

```mermaid
flowchart LR
    
    MEAS4(DataSource 4) --> OPT2(Optimization 2)
    PARAM4(Parameters 4) --> OPT2
    OPT2 --> SWU8(SW Unit 8)
    PARAM4 --> SWU9(SW Unit 9)
    PARAM4 --> SWU8
    SWU8 --> SWU9
    SWU9 --> OPT2

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class PARAM4 Parameters;
    class MEAS4 DataSource;
    class SWU8 SW_Unit;
    class SWU9 SW_Unit;
    class OPT2 Optimization;

```

```mermaid
flowchart LR

    MEAS5(DataSource 5) --> OPT3(Optimization 3)
    PARAM5(Parameters 5) --> OPT3
    OPT3 --> SWU10(SW Unit 10)
    PARAM5 --> SWU10
    SWU10 --> OPT3
    OPT3 --> MEAS6(DataSource 6)

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class PARAM5 Parameters;
    class MEAS5 DataSource;
    class MEAS6 DataSource;
    class SWU10 SW_Unit;
    class OPT3 Optimization;

```

#### Closed-Loop Simulation

```mermaid
flowchart LR
    
    MEAS7(DataSource 7) --> SWU11(SW Unit 11)
    SWU11 --> SWU12(SW Unit 12)
    SWU12 --> SWU13(SW Unit 13)
    SWU13 --> SWU11
    PARAM6(Parameters 6) --> SWU11
    PARAM6 --> SWU12
    PARAM6 --> SWU13
    SWU11 --> MEAS8(DataSource 8)

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;

    class PARAM6 Parameters;
    class MEAS7 DataSource;
    class MEAS8 DataSource;
    class SWU11 SW_Unit;
    class SWU12 SW_Unit;
    class SWU13 SW_Unit;

```    

```mermaid
flowchart LR
    
    MEAS9(DataSource 9) --> SWU14(SW Unit 14)
    SWU14 --> SWU15(SW Unit 15)
    SWU15 --> SWU16(SW Unit 16)
    SWU16 --> SWU14
    PARAM7(Parameters 7) --> SWU14
    PARAM7 --> SWU15
    PARAM7 --> SWU16

    classDef Parameters        color:#a44300, stroke:#a44300;
    classDef DataSource        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;

    class PARAM7 Parameters;
    class MEAS9 DataSource;
    class SWU14 SW_Unit;
    class SWU15 SW_Unit;
    class SWU16 SW_Unit;


```
