# Dashboard Design

**Version:** 0.4  
**Owner:** Project0  
**Last Updated:** 2026-08-06

---

# 1. Purpose

## Objective

Define the design of the Project0 Dashboard, which serves as the primary user interface for the Project0 platform.

## Scope

Describe the dashboard architecture, navigation, layout, user interaction model, dashboard widgets, integration with Project0 services, and future expansion. This document defines the platform user experience rather than implementation details.

---

# 2. Design Philosophy

* Browser-based, local-first operation.
* Dashboard represents the Project0 platform rather than a single AI agent.
* Human-in-the-loop workflows.
* Documentation-first development.
* Consistent user experience across all agents.
* Cross-platform operation.
* Reuse existing platform services through the Platform Dispatcher.
* Keep presentation separate from business logic.
* The Dashboard Framework owns only platform-wide navigation, layout, shared status presentation, and agent extension points.
* Platform and agent status are displayed in the Work Area for the currently selected context.
* Individual AI agents own their agent-specific pages, workflows, controls, and results.

---

# 3. Dashboard Architecture

```
Browser
    │
    ▼
FastAPI Dashboard Framework
    │
    ▼
Dashboard Routes
    │
    ▼
Platform Dispatcher
    │
    ▼
Project0 Platform Services
```

FastAPI is the selected application framework for the Project0 Dashboard. Jinja2 templates will provide the initial browser interface, and Uvicorn will host the local ASGI application.

---

# 4. Navigation Model

The Dashboard Framework provides persistent application navigation while the active page is displayed in the Work Area.

## Header

The Header is always visible and provides:

* Project0 Dashboard title
* User information (future)
* Help
* Logout (future)

## Breadcrumb Navigation

A horizontal breadcrumb is displayed directly beneath the Header.

Examples:

```
Dashboard

Dashboard > Documentation

Dashboard > Documentation Agent

Dashboard > Documentation Agent > Review Changes

Dashboard > Research Agent > Daily Opportunities
```

The Breadcrumb identifies the user's current location within the Dashboard Framework and updates automatically as navigation changes.

## Sidebar Navigation

The left sidebar contains two permanent navigation sections.

### Agents

Provides navigation to registered AI Agents.

### Workspace

Provides navigation to platform-level pages including:

* Project Overview
* Documentation
* Activity
* Settings

Project0 status is displayed in the Project Overview Work Area rather than persistently in the Sidebar.

The Dashboard Framework owns all navigation while individual agents own their internal pages.

---

# 5. Dashboard Layout

The Dashboard uses a persistent application shell.

```
Header

Breadcrumb Navigation

---------------------------------------------------------------

Sidebar                        Work Area
                               ┌─────────────────────────────┐
Agents                         │ Context Toolbar             │
                               ├─────────────────────────────┤
Workspace                      │                             │
                               │         Work Area           │
                               │                             │
                               │                             │
                               └─────────────────────────────┘
```

## Header

Displays platform identity and future user controls.

## Breadcrumb Navigation

Displays the current navigation path.

## Sidebar

The Sidebar contains two permanent navigation sections:

* Agents
* Workspace

The Sidebar remains visible while navigating the application. Status information is displayed in the Work Area for the selected platform page or agent.

## Context Toolbar

The Context Toolbar is displayed directly above the Work Area.

Its width matches the Work Area only.

The toolbar changes according to the currently selected page.

The Dashboard Framework provides the toolbar region while the active page supplies its commands.

## Work Area

Displays the currently selected Dashboard page or Agent Interface.

Only the Work Area changes during navigation.

---

# 6. Dashboard Components

## Project Overview

The Project Overview is the default Dashboard Work Area.

It displays Project0 overview and status information including:

* Repository
* Repository path
* Git branch
* Git status
* Current implementation phase
* Documentation count
* Platform version
* Test status
* Validation status
* LLM status
* Active workflow

Project0 status is shown only when the Project Overview is selected. It is not displayed persistently in the Sidebar.

## Agent Navigation

Displays all registered AI Agents.

Only implemented or registered agents appear.

## Workspace Navigation

Provides navigation to platform-level pages.

## Context Toolbar

Displays actions appropriate to the active page.

Examples:

Project Overview

* Refresh Status
* Open Documentation

Documentation Agent

* New Request
* Analyze
* Validate

Review Changes

* Approve
* Revise
* Reject
* Skip

The Dashboard Framework does not define toolbar commands.

Each page defines its own toolbar actions.

## Work Area

Displays all interactive content including:

* Project Overview and platform status
* Agent pages and agent status
* Reports
* Review screens
* Forms
* Results
* Settings

---

# 7. Documentation Integration

The Dashboard provides access to Project0 documentation without replacing MkDocs.

During initial development:

* `http://127.0.0.1:8000` hosts the local MkDocs documentation.
* `http://127.0.0.1:8001` hosts the Project0 Dashboard.

The Dashboard Documentation link redirects to the MkDocs site.

Development:
* Local MkDocs site
* GitHub Pages documentation

Future:
* Dashboard-served documentation.

---

# 8. Agent Integration

```
Dashboard
    │
    ▼
Agent Launcher
    ├── Documentation Agent
    ├── Research Agent
    └── Future Agents
```

The Dashboard hosts agents while existing platform services perform the work. Agent-specific features such as documentation review, validation presentation, repository updates, and Git diff display are outside the Dashboard Framework and belong in the applicable Agent Interface Design document.

---

# 9. Workflow Interaction

1. Start
2. Analyze
3. Progress
4. User Review
5. Validation
6. Apply Changes
7. Completion
8. History (future)

---

# 10. Platform Status

Platform status is displayed in the Project Overview Work Area rather than as a persistent Sidebar panel.

Initial information includes:

* Repository
* Repository path
* Current Git branch
* Git working tree status
* Current implementation phase
* Documentation count
* Automated test status
* Validation status
* Platform version
* LLM provider
* Active workflow

The same Work Area model applies to AI agents: when an agent is selected, its status, controls, and content are displayed in the Work Area for that agent.

Future additions may include:

* Embedding service status
* Vector database status
* Active model information
* Memory usage
* Background task status

---

# 11. User Interface Standards

* Consistent navigation
* Reusable cards and panels
* Standard status indicators
* Shared approval workflow controls
* Responsive browser layout
* Shared UI standards shall remain independent of any single agent.
* Agent-specific controls shall not be added to the Dashboard Framework solely for one agent.

---

# 12. Page Responsibilities

Every Dashboard page provides four elements:

* Page Title
* Breadcrumb location
* Context Toolbar
* Work Area content

The Dashboard Framework supplies the surrounding application shell.

Individual platform pages and AI Agents supply their own status, content, and toolbar actions.

The Sidebar selects the active platform or agent context. The Context Toolbar and Work Area then present the actions and content for that context.

This separation allows new agents to integrate into the Dashboard without modifying the Dashboard Framework.

---

# 13. Initial Implementation Scope

The first Dashboard Framework implementation includes:

* FastAPI application creation
* Platform-level dashboard routes
* Shared base template (dashboard.html)
* Dashboard home page template (dashboard_home.html)
* Agent placeholder template (agent_placeholder.html)
* Project Overview home page
* Shared dashboard stylesheet (css/dashboard.css)
* Documentation redirect
* Generic agent placeholders
* Basic status endpoint
* Unit and integration tests

The initial implementation excludes:

* Documentation Agent request forms
* Documentation review controls
* Git diff presentation
* Validation-result presentation
* Agent-specific workflow state

---

# 14. Future Expansion

* Dark mode
* Authentication
* Multi-user support
* Remote repositories
* Cloud deployment
* Plugin architecture
* Additional AI agents

---

# 15. Relationship to Agent Interface Documents

This document defines the Project0 platform user experience.

Each AI agent shall provide its own Interface Design document describing agent-specific pages and interactions while conforming to the Dashboard Design.

---

# 16. Related Documents

* Project Charter
* Documentation Standards
* Documentation Agent Functional Specification
* Documentation Agent Architecture
* Documentation Agent Design
* Component Communication Design
* Testing Guide
* Project Directory Structure
* Documentation Agent Interface Design (future)
