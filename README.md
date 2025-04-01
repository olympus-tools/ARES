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

Reading and writing measurements in different file formats (currently only mf4 is implemented)

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

    DS1(Dataset 1) --> SWU1(SW Unit 1)
    DS1 --> SWU2(SW Unit 2)
    MEAS1(Measurement 1) --> SWU1
    SWU1 --> SWU2
    SWU1 --> PL1(Plot 1)
    SWU2 --> MEAS2(Measurement 2)
    SWU2 --> TS1(Testspecifiaction 1)

    DS2(Dataset 2) --> SWU3(SW Unit 3)
    DS2 --> SWU4(SW Unit 4)
    DS2 --> SWU5(SW Unit 5)
    MEAS1(Measurement 1) --> SWU3
    SWU3 --> SWU4
    SWU3 --> TS1
    SWU4 --> MEAS2
    SWU4 --> SWU5

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class DS1 Dataset;
    class DS2 Dataset;
    class MEAS1 Measurement;
    class MEAS2 Measurement;
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

    DS3(Dataset 3) --> SWU6(SW Unit 6)
    DS3 --> OPT1(Optimization 1)
    MEAS3(Measurement 3) --> SWU6
    SWU6 --> OPT1
    OPT1 --> SWU7(SW Unit 7)
    SWU7 --> OPT1

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class DS3 Dataset;
    class MEAS3 Measurement;
    class SWU6 SW_Unit;
    class SWU7 SW_Unit;
    class OPT1 Optimization;

```

```mermaid
flowchart LR
    
    MEAS4(Measurement 4) --> OPT2(Optimization 2)
    DS4(Dataset 4) --> OPT2
    OPT2 --> SWU8(SW Unit 8)
    DS4 --> SWU9(SW Unit 9)
    DS4 --> SWU8
    SWU8 --> SWU9
    SWU9 --> OPT2

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class DS4 Dataset;
    class MEAS4 Measurement;
    class SWU8 SW_Unit;
    class SWU9 SW_Unit;
    class OPT2 Optimization;

```

```mermaid
flowchart LR

    MEAS5(Measurement 5) --> OPT3(Optimization 3)
    DS5(Dataset 5) --> OPT3
    OPT3 --> SWU10(SW Unit 10)
    DS5 --> SWU10
    SWU10 --> OPT3
    OPT3 --> MEAS6(Measurement 6)

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;
    classDef Optimization      color:#e5d300, stroke:#e5d300;

    class DS5 Dataset;
    class MEAS5 Measurement;
    class MEAS6 Measurement;
    class SWU10 SW_Unit;
    class OPT3 Optimization;

```

#### Closed-Loop Simulation

```mermaid
flowchart LR
    
    MEAS7(Measurement 7) --> SWU11(SW Unit 11)
    SWU11 --> SWU12(SW Unit 12)
    SWU12 --> SWU13(SW Unit 13)
    SWU13 --> SWU11
    DS6(Dataset 6) --> SWU11
    DS6 --> SWU12
    DS6 --> SWU13
    SWU11 --> MEAS8(Measurement 8)

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;

    class DS6 Dataset;
    class MEAS7 Measurement;
    class MEAS8 Measurement;
    class SWU11 SW_Unit;
    class SWU12 SW_Unit;
    class SWU13 SW_Unit;

```    

```mermaid
flowchart LR
    
    MEAS9(Measurement 9) --> SWU14(SW Unit 14)
    SWU14 --> SWU15(SW Unit 15)
    SWU15 --> SWU16(SW Unit 16)
    SWU16 --> SWU14
    DS7(Dataset 7) --> SWU14
    DS7 --> SWU15
    DS7 --> SWU16

    classDef Dataset           color:#a44300, stroke:#a44300;
    classDef Measurement        color:#1e9bec, stroke:#1e9bec;
    classDef SW_Unit           color:#d30000, stroke:#d30000;
    classDef Test              color:#2eb400, stroke:#2eb400;
    classDef Plot              color:#ad00d0, stroke:#ad00d0;

    class DS7 Dataset;
    class MEAS9 Measurement;
    class SWU14 SW_Unit;
    class SWU15 SW_Unit;
    class SWU16 SW_Unit;

```
