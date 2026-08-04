# Component Communication Design

**Version:** 0.2  
**Owner:** Project0  
**Last Updated:** 2026-08-04  

---

## 1. Purpose

This document defines how Project0 platform components communicate. It establishes the implemented communication patterns, execution flow, interface responsibilities, shared model usage, and event handling.

It complements, but does not replace, the **Shared Data Models and Error Contracts** document, which defines the communication objects themselves.

## 2. Scope

This document applies to the following implemented components:

* Platform Dispatcher
* Workflow Engine
* Context Builder
* Context Rule Registry
* Context Filter
* Repository Service
* Shared Interfaces
* Shared Context Models
* Shared Workflow Models

It also provides the communication foundation for these planned components:

* Validation Engine
* Reasoning Service
* Documentation Agent
* User Review
* Future AI agents

## 3. Design Objectives

The communication architecture shall:

* Minimize component coupling.
* Depend on typed interfaces rather than concrete implementations where practical.
* Use shared immutable models for component communication.
* Maximize reuse across future AI agents.
* Provide workflow and task traceability.
* Preserve deterministic behavior where AI reasoning is not required.
* Support human approval before future repository changes are applied.
* Allow future distributed and asynchronous execution.

## 4. Communication Principles

1. The Platform Dispatcher provides the platform-level entry point.
2. The Workflow Engine owns workflow task execution.
3. Components communicate through defined typed interfaces.
4. Shared data models are the authoritative communication objects.
5. Components do not directly access another component's internal state.
6. The Context Builder coordinates context selection through the Context Rule Registry, Context Filter, and Repository Interface.
7. Current repository communication is read-only.
8. Future repository writes shall occur only after validation and approval.
9. Significant workflow and task state changes may generate events.
10. Components shall not bypass the Workflow Engine for workflow execution control.

## 5. Communication Model

Project0 currently uses two communication patterns.

### Synchronous Request/Response

Used when an immediate result is required.

Implemented examples:

* Dispatch a context workflow.
* Execute a Workflow Task.
* Request workflow-specific Context Filter criteria.
* Discover repository documentation.
* Read repository files.
* Build a Context Package.
* Return a Workflow Execution Result.

### Workflow and Task Events

Used to announce execution lifecycle changes when a Workflow Event Publisher is configured.

Implemented events:

* `WorkflowStarted`
* `WorkflowCompleted`
* `WorkflowFailed`
* `TaskStarted`
* `TaskCompleted`
* `TaskFailed`

Additional validation, artifact, and approval events are planned for future phases.

## 6. Implemented Communication Flow

```mermaid
flowchart TD
    A["Application Entry Point<br/><small>main.py</small>"]
    B["Platform Dispatcher<br/><small>Dispatch Context Workflow</small>"]
    C["Workflow Engine<br/><small>Execute Workflow Task</small>"]
    D["Context Builder<br/><small>Assemble Context Package</small>"]
    E["Context Rule Registry<br/><small>Resolve Workflow Rule</small>"]
    F["Context Filter<br/><small>Select Repository Files</small>"]
    G["Repository Service<br/><small>Discover and Read Files</small>"]
    H["Local Repository<br/><small>Authoritative Content</small>"]
    I["Context Package"]
    J["Task Execution Result"]
    K["Workflow Execution Result"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> D
    D --> F
    F --> D
    D --> G
    G --> H
    G --> D
    D --> I
    I --> J
    J --> K
    K --> B
```

The implemented sequence is:

1. `main.py` creates the Platform Dispatcher.
2. The Platform Dispatcher creates a Workflow Task.
3. The Platform Dispatcher submits the task to the Workflow Engine.
4. The Workflow Engine begins workflow and task execution.
5. The task invokes the Context Builder through the Context Builder Interface.
6. The Context Builder requests criteria from the Context Rule Registry.
7. The Context Rule Registry returns workflow-specific Context Filter criteria.
8. The Context Filter selects eligible repository files.
9. The Context Builder requests selected files through the Repository Interface.
10. The Repository Service returns structured file results.
11. The Context Builder produces a Context Package.
12. The Workflow Engine returns Task and Workflow Execution Results.

## 7. Platform Responsibilities

### Platform Dispatcher

* Assemble default platform services.
* Create platform-level Workflow Tasks.
* Dispatch tasks to the Workflow Engine.
* Preserve supplied workflow identifiers or generate new identifiers.
* Return Workflow Execution Results.
* Avoid implementing repository, context, or workflow behavior directly.

### Workflow Engine

* Validate workflow requests.
* Execute tasks in supplied order.
* Track workflow and task identifiers.
* Capture task outputs and failures.
* Stop execution after the first failed task.
* Publish configured workflow and task events.
* Return structured Task and Workflow Execution Results.

### Context Builder

* Request workflow-specific selection criteria.
* Apply deterministic Context Filters.
* Read selected documents through the Repository Interface.
* Preserve repository document metadata.
* Return Context Packages.
* Preserve partial results and communicate read warnings.

### Context Rule Registry

* Resolve Context Rules by workflow type.
* Convert Context Rules into Context Filter criteria.
* Maintain default workflow-specific selection policies.
* Report requests for unregistered workflow types.

### Context Filter

* Apply documentation, extension, path, and pattern criteria.
* Normalize repository paths.
* Return selected files in deterministic order.
* Avoid reading repository content or defining workflow policy.

### Repository Service

* Discover supported repository files.
* Discover Markdown documentation.
* Read one or multiple repository files.
* Validate repository-relative paths.
* Prevent access outside the repository root.
* Return structured repository results and errors.

### Shared Interfaces

* Define stable component contracts.
* Allow structural conformance without explicit inheritance.
* Support dependency injection and isolated testing.
* Allow alternate implementations without changing consumers.

### Shared Data Models

* Define immutable communication objects.
* Provide shared workflow and task statuses.
* Provide Context Packages and Workflow Execution Results.
* Preserve identifiers, timestamps, outputs, warnings, and errors.

### Planned Components

The following responsibilities remain planned:

* AI-assisted reasoning
* Validation of proposed updates
* User review and approval
* Controlled repository modification
* Git diff and commit generation
* Dashboard and audit storage

## 8. Communication Contracts

Implemented communication objects include:

### Context Models

* `ContextWorkflowType`
* `ContextBuildStatus`
* `ContextRequest`
* `ContextDocument`
* `ContextPackage`

### Workflow Models

* `WorkflowStatus`
* `TaskStatus`
* `WorkflowTask`
* `TaskExecutionResult`
* `WorkflowExecutionResult`

### Repository Results

* Repository file metadata
* Repository list results
* Individual file read results
* Batch file results
* Structured repository errors

Additional validation, approval, artifact, and agent communication objects remain defined or planned in **Shared_Data_Models_and_Error_Contracts.md**.

## 9. Event Categories

### Implemented Workflow Events

* `WorkflowStarted`
* `WorkflowCompleted`
* `WorkflowFailed`

### Implemented Task Events

* `TaskStarted`
* `TaskCompleted`
* `TaskFailed`

### Planned Validation Events

* `ValidationStarted`
* `ValidationCompleted`
* `ValidationFailed`

### Planned Artifact Events

* `ArtifactProposed`
* `ArtifactValidated`
* `ArtifactApproved`
* `ArtifactCommitted`

### Planned Approval Events

* `ApprovalRequested`
* `ApprovalGranted`
* `ApprovalRejected`

## 10. Error Handling

Current errors are communicated through exceptions or structured result objects, depending on the component boundary.

Implemented behavior includes:

* Invalid workflow requests raise `ValueError`.
* Task exceptions are converted into failed Task Execution Results.
* A failed task produces a failed Workflow Execution Result.
* Repository errors include an error code, message, and optional path.
* Repository discovery failure produces a failed Context Package.
* Partial repository reads produce a Context Package with warnings.
* Empty context selection produces a completed-with-warnings Context Package.

Future shared error contracts may additionally identify:

* originating component
* workflow identifier
* task identifier
* severity
* recovery recommendation

## 11. Logging and Traceability

Implemented communication is traceable through:

* workflow identifier
* task identifier
* context identifier
* workflow and task names
* timezone-aware timestamps
* component logger name
* workflow status
* task status
* context source count
* structured warnings and errors

Persistent audit storage is not part of the current implementation.

## 12. Initial Implementation

The implemented Phase 2 communication foundation uses:

* Python structural `Protocol` interfaces
* Python immutable dataclasses
* String enumerations for statuses and workflow types
* Synchronous in-process communication
* Optional workflow event publishing
* Structured application logging
* Repository-relative file access
* pytest unit and integration testing

The current implementation does not yet use:

* Pydantic
* persistent message queues
* SQLite audit storage
* distributed communication
* asynchronous workflow execution

## 13. Future Evolution

The communication architecture is designed to support future enhancements including:

* Documentation Agent execution
* Reasoning Service integration
* Validation Engine integration
* Human review and approval
* Controlled repository writes
* Git diff and commit operations
* Persistent workflow state
* Persistent audit storage
* Distributed agents
* Persistent message queues
* Cloud execution
* Multiple concurrent workflows
* Additional AI agent types
* Enhanced dashboard monitoring
* Asynchronous workflow execution

## 14. Relationship to Shared Data Models and Error Contracts

This document defines **how** Project0 platform components communicate.

The companion document **Shared_Data_Models_and_Error_Contracts.md** defines **what** is communicated.

The two documents are intended to be used together:

| Document                               | Responsibility                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| Shared Data Models and Error Contracts | Defines shared model structures, identifiers, statuses, results, and error contracts.   |
| Component Communication Design         | Defines communication patterns, execution flow, events, and component responsibilities. |

Communication payloads shall conform to the shared models defined in the companion document or to implemented subsystem result contracts.

## 15. Implementation Status

The Phase 2 communication foundation has been implemented and validated through unit and integration testing.

The validated end-to-end flow includes:

1. Create the Platform Dispatcher.
2. Validate Project0 startup.
3. Create a context Workflow Task.
4. Execute the task through the Workflow Engine.
5. Build workflow-specific repository context.
6. Resolve Context Rules.
7. Apply deterministic Context Filters.
8. Read real repository documentation.
9. Return a Context Package.
10. Return Task and Workflow Execution Results.

The next implementation phase will extend this communication foundation with AI reasoning, validation, user review, and controlled repository modification.


