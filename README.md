# Cisco Catalyst SD-WAN LifeCycle Evaluation Report

A Python tool that connects to **Cisco Catalyst SD-WAN Manager (vManage)** via REST APIs, evaluates a customer's SD-WAN deployment against the **Cisco SD-WAN Lifecycle phases**, and produces a color-coded maturity report (printed to the console and saved to a timestamped text file).

---

## Table of Contents
- [Overview](#overview)
- [Lifecycle Phases Evaluated](#lifecycle-phases-evaluated)
- [Features](#features)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Output](#output)
- [Status Legend](#status-legend)
- [Notes & Limitations](#notes--limitations)
- [License](#license)
- [Author](#author)

---

## Overview

This script automates the assessment of a Cisco Catalyst SD-WAN overlay by querying the SD-WAN Manager (vManage) data service APIs. It analyzes controllers, WAN Edge devices, feature templates, localized policies, and centralized (vSmart) policies, then maps the results to a series of **exit criteria checks** organized by lifecycle phase.

The result is a human-readable report that highlights what is **COMPLETED**, **INCOMPLETE**, or **NOT ASSESSED**, along with supplementary deployment, controller, device, policy, and operational information.

---

## Lifecycle Phases Evaluated

| Phase | Focus |
|-------|-------|
| **On-Board** | Smart/Virtual Account, Organization Name |
| **Implement** | Controller installation, templates, local & centralized policy, initial sites/devices |
| **Use** | Additional sites/devices, Application-Aware Routing, Manager connectivity (25%) |
| **Engage** | Operationalize at scale, Syslog/SNMP/AAA/NTP, Manager connectivity (70%) |
| **Adopt** | Advanced optimization features, active policy, Manager connectivity (95%) |
| **Optimize** | SLA-based routing optimization, vAnalytics |

---

## Features

- Retrieves and analyzes:
  - WAN Edge routers and SD-WAN controllers (vManage, vSmart, vBond)
  - Feature templates (AAA, Syslog, SNMP, NTP — controller and edge)
  - Localized and Centralized (vSmart) policies
  - Organization name and software version
- Validates device health: active state, control connections, template mode, sync status, service VPN, interface status.
- Evaluates centralized policy types: Control, cFlowd, Data, VPN Membership, App Route.
- **Parallel API processing** via `ThreadPoolExecutor` (capped at 30 workers) for faster execution.
- Generates a **color-coded console report** and a **timestamped text file**.

---

## Requirements

- **Python 3.6+**
- Network reachability to the Catalyst SD-WAN Manager (vManage) instance.
- Valid vManage credentials with read access to the data service APIs.
- A terminal that supports **ANSI color codes** (for the colored output).
- A companion module: **`vAPI.py`** — must expose a `main()` function that returns a session object with a `getDataResponse(url)` method. *(This module handles authentication and the HTTP session and is not included in this script.)*

> **Standard library modules used:** `concurrent.futures`, `json`, `datetime`, `pprint`.

---

## Project Structure

```
.
├── sdwan_evaluation.py      # This script (main evaluation logic)
├── vAPI.py                  # Session/authentication helper (must provide main() and getDataResponse())
└── report-DDMMYYYY-HHMMSS.txt  # Generated report (created at runtime)
```

---

## Installation

1. Clone or copy the project files into a working directory.

   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. (Recommended) Create and activate a virtual environment.

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. Ensure `vAPI.py` is present and configured for your environment.

---

## Configuration

Authentication and connection details (host, username, password/token) are handled inside **`vAPI.py`**. Configure that module according to your environment before running the script.

> ⚠️ **Do not hard-code credentials in source files committed to version control.** Use environment variables or a secrets manager.

The `max_workers` value in the `parellel()` function is intentionally set to **30**. Per the in-code guidance, **do not increase this value**, as a higher concurrency may impact vManage performance.

---

## Usage

Run the script directly:

```bash
python sdwan_evaluation.py
```

The script will:
1. Establish a session via `vAPI.main()`.
2. Query the SD-WAN Manager APIs.
3. Analyze the data.
4. Print the report to the console and save it to a timestamped `.txt` file.

---

## How It Works

The core logic lives in the `Report` class. The `runReport()` method orchestrates the workflow:

| Step | Method | Purpose |
|------|--------|---------|
| 1 | `runApi()` | Pulls devices, controllers, templates, policies, version, org name |
| 2 | `get_device_info()` | Counts active/reachable/managed devices, sites, service VPNs, control connectivity |
| 3 | `get_controller_info()` | Counts vManage, vSmart, vBond nodes |
| 4 | `checkCentralizedPolicy()` | Detects active centralized policy and its definition types |
| 5 | `analyzeFeatureTemplates()` | Tallies AAA/Syslog/SNMP/NTP usage on controllers and edges |
| 6 | `reportchecks()` | Evaluates all exit criteria and assigns COMPLETED/INCOMPLETE/NOT ASSESSED |
| 7 | `generateReport()` | Formats, prints, and writes the report to file |

### Key API Endpoints Queried
| Endpoint | Data Retrieved |
|----------|----------------|
| `/dataservice/system/device/vedges` | WAN Edge routers |
| `/dataservice/system/device/controllers` | SD-WAN controllers |
| `/dataservice/template/feature` | Feature templates |
| `/dataservice/template/policy/vedge` | Localized policy |
| `/dataservice/template/policy/vsmart` | Centralized policy |
| `/dataservice/device/action/install/devices/vmanage` | Software version |
| `/dataservice/settings/configuration/organization` | Organization name |
| `/dataservice/device/interface/synced?deviceId=...` | Per-device interface / service VPN |
| `/dataservice/device/counters?deviceId=...` | Control connection counters |

---

## Output

The script produces two sections:

1. **LifeCycle Evaluation Report** — Each lifecycle phase with its required/recommended checks and a status indicator.
2. **Additional Information** — Deployment, controller, device, device health, policy, and operational details.

A file named `report-DDMMYYYY-HHMMSS.txt` is written to the working directory containing the full report.

---

## Status Legend

| Indicator | Meaning |
|-----------|---------|
| **COMPLETED!** (green) | The criterion is met |
| **INCOMPLETE!** (red) | The criterion is not met |
| **NOT ASSESSED!** (black) | The check is not evaluated by the script (manual verification required) |

> **Not Assessed items** include: Smart/Virtual Account verification, FEC, Packet Duplication, TCP Optimization, IPS/IDS, Firewall, Cloud OnRamp for SaaS, vAnalytics, Umbrella, SD-AVC Cloud, deployment type, Smart Account integration, and telemetry.

---

## Notes & Limitations

- The script is **read-only** — it does not modify the SD-WAN configuration.
- Several advanced/security feature checks are flagged **NOT ASSESSED** and require manual verification.
- Some customers may prefer not to run scripts in their environment; in those cases, a corresponding **maturity questionnaire** can be used to gather the same insights.
- Output relies on ANSI color codes; on terminals without ANSI support, raw escape sequences may appear. The saved text file will also contain these codes.
- Ensure the account used has sufficient API read permissions, or some queries may fail.

---

## License

Licensed under the **Cisco Sample Code License, Version 1.1**.
See: https://developer.cisco.com/docs/licenses

Software is provided **"AS IS"**, without warranties or conditions of any kind, either express or implied.

---

## Author

**Hussein Omar** — CSS, EMEA
📧 husseino@cisco.com

*Copyright (c) Cisco and/or its affiliates.*
