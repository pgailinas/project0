# Documentation Standards

**Version:** 0.3  
**Owner:** Project0  
**Last Updated:** 2026-09-11

---

## 1. Documentation Principles

1. Repository documentation is the authoritative source of project knowledge.
2. Documentation is living project knowledge.
3. Every document has a single purpose.
4. Write once. Reference often.
5. Capture decisions, not discussions.
6. Document only to the level necessary to support development, maintenance, and decision making.
7. Begin each design document with a concise executive summary.
8. Prefer diagrams when they communicate information more effectively than text.
9. Documentation shall remain consistent across the repository.
10. Markdown is the authoritative documentation format.
11. All documentation is version controlled in Git.
12. Material for MkDocs is the standard publishing platform.
13. Design documents should define contracts, responsibilities, and interactions, but should not prescribe implementation details.
14. Platform framework documents shall describe implemented platform capabilities without prescribing future functionality. Dashboard framework documentation shall distinguish reusable platform infrastructure from AI agent implementations.
15. Reusable user interface frameworks, shared stylesheets, and template layouts shall be documented once in their authoritative design document and referenced elsewhere rather than duplicated.

## 2. Document Metadata

Controlled Project0 documents shall begin with a level-one title followed by this metadata, in this order:

```markdown
# <Document Title>

**Version:** <version>  
**Owner:** <owner>  
**Last Updated:** <YYYY-MM-DD>
```

`Status` may be added when a document requires an explicit lifecycle or implementation state. Dates shall use `YYYY-MM-DD`. `README.md` and MkDocs landing pages may omit controlled-document metadata.

## 3. Markdown Formatting

- Use one level-one heading for the document title.
- Use level-two headings for primary sections and level-three headings for subsections.
- Number primary sections in controlled technical documents when the document benefits from stable navigation. Apply one numbering convention consistently within each document family.
- Use sentence case for headings unless an official name requires different capitalization.
- Use hyphenated unordered lists and numerals for ordered procedures.
- Use tables for exact mappings or comparisons. Use prose for explanations that do not benefit from tabular structure.
- Use fenced code blocks with a language identifier for code, configuration, commands, and structured data.
- Use backticks for filenames, paths, commands, configuration names, environment variables, identifiers, and literal values.
- Use repository-relative Markdown links for internal documents.
- Use horizontal rules sparingly; do not place them between every primary section.
- Wrap prose consistently according to the repository formatter or lint configuration when one is defined.

## 4. Common Document Structure

Controlled documents shall contain, when applicable:

1. A concise statement of purpose.
2. Scope and authority boundaries.
3. The family-specific body defined in this standard.
4. Current constraints, limitations, or exclusions when material.
5. Related authoritative documents when cross-references are necessary.

Design documents shall begin with a concise `Executive Summary`. Other document families may use an executive summary when it materially improves comprehension.

A required section without repository-supported content shall be reported as a documentation gap. Unsupported content shall not be invented solely to populate a standard section. Conditional sections may be omitted when they do not apply.

## 5. Document Families

Documents within the same family shall use a common section structure so comparable information can be located consistently. Family structure governs organization, not shared functionality. Agent-specific content shall not be inferred from another agent's document.

### 5.1 Charters

Charters define purpose, mission, scope, authority, operating principles, and success criteria.

Required structure:

1. Purpose
2. Mission
3. Vision
4. Objectives
5. Scope
6. Operating Principles
7. Authority and Constraints
8. Success Criteria
9. Relationship to Other Documents

`Out of Scope`, `Stakeholders`, `Risks and Assumptions`, and `Future Direction` are conditional sections.

### 5.2 Functional Specifications

Functional specifications define what a component or agent shall do without prescribing internal implementation.

Required structure:

1. Purpose
2. Scope
3. Functional Principles
4. Responsibilities
5. Inputs and Request Contract
6. Functional Workflow
7. Outputs and Result Contract
8. Validation and Error Behavior
9. Configuration
10. Constraints and Exclusions
11. Success or Acceptance Criteria

Detailed workflow stages may appear as subsections or primary sections when their complexity requires it.

### 5.3 Architecture Documents

Architecture documents define topology, major components, responsibility boundaries, dependencies, and architectural constraints.

Required structure:

1. Executive Summary
2. Purpose and Scope
3. Architectural Principles
4. Runtime Topology or Architectural Workflow
5. Components and Responsibilities
6. Data and Interface Boundaries
7. External Dependencies
8. Validation and Failure Boundaries
9. Architectural Constraints

Future expansion is conditional and shall be clearly separated from implemented architecture.

### 5.4 Design Documents

Design documents describe how the implemented components satisfy the approved architecture and functional specification.

Required structure:

1. Executive Summary
2. Purpose and Scope
3. Design Principles
4. Component Design
5. Component Interactions or Data Flow
6. Interfaces and Contracts
7. Configuration and Error Handling
8. Design Constraints and Current Limitations
9. Verification Evidence

Detailed algorithms or source-level behavior shall be included only when necessary to explain a contract, responsibility, or material design decision.

### 5.5 Interface Design Documents

Interface design documents define public boundaries among browser routes, services, workflows, providers, data models, and platform components.

Required structure:

1. Executive Summary
2. Purpose and Scope
3. Interface Boundaries
4. User or Browser Interface
5. Service and Workflow Interfaces
6. Provider Interfaces
7. Data and Result Contracts
8. Configuration and Status Interfaces
9. Error and Safety Guarantees
10. Limitations

Only interface types applicable to the documented component shall be included.

### 5.6 Testing Guides

Testing guides explain how to run, interpret, and troubleshoot the applicable tests. They do not replace test plans or test-result records.

Required structure:

1. Purpose
2. Testing Objectives and Principles
3. Test Organization
4. Test Environment and Configuration
5. Standard and Focused Test Commands
6. Manual or Browser Validation
7. Result Interpretation and Completion Criteria
8. Troubleshooting

Live-provider validation, repository-safety checks, and current gaps are conditional sections.

### 5.7 Test Plans

Test plans define intended verification coverage, scenarios, environments, and acceptance gates.

Required structure:

1. Executive Summary
2. Purpose and Scope
3. Verification Principles
4. Test Levels and Locations
5. Functional Verification Scenarios
6. Safety and Failure Scenarios
7. Integration and Acceptance Scenarios
8. Test Data and Environment
9. Entry and Exit Criteria
10. Known Coverage Considerations

Provider-specific scenarios are conditional.

### 5.8 Test Results

Test-result documents record verified evidence and shall distinguish executed results from test inventory or expected coverage.

Required structure:

1. Executive Summary
2. Audit and Execution Basis
3. Validation Status
4. Executed Test Results
5. Observed Failures, Constraints, and Risks
6. Defect Record
7. Validation Decision
8. Next Required Verification

Exact commands, environment, commit or repository state, test counts, failures, skips, and execution date shall be recorded when results are claimed.

### 5.9 Project Status and Roadmap Documents

Status documents describe the verified current state. Roadmaps describe delivery organization, sequencing, and future work. A roadmap shall not be treated as authority for completed implementation when a dedicated status document exists.

Status and roadmap documents shall identify their purpose, status authority, current evidence basis, limitations, and update rules.

### 5.10 Reference and Environment Documents

Reference documents include directory structure, development environment, development standards, shared contracts, and similar lookup material. Their structure shall follow the subject rather than a forced common template, while complying with the repository-wide metadata and formatting rules.

Directory documentation shall describe intentional architecture and directory responsibilities. It shall not become a manually maintained inventory of every repository file.

## 6. Cross-References and Duplication

- Each material concept shall have one authoritative document.
- Other documents may include a short contextual summary and shall link to the authoritative source for detail.
- Cross-references shall identify the document by descriptive title, not only by path.
- Circular references shall be avoided.
- Shared platform behavior shall not be duplicated in agent documents unless a brief explanation is required to define the agent boundary.
- Parallel agent documents may share structure but shall not assume identical responsibilities, workflows, or constraints.

## 7. Content Preservation and Change Classification

Documentation updates shall be classified as:

- **Formatting:** Presentation changes that do not alter meaning.
- **Structural:** Relocation or reorganization of existing content without altering meaning.
- **Substantive:** Additions, removals, corrections, or wording changes that may alter meaning.

Formatting and structural normalization shall preserve requirements, numerical values, commands, paths, configuration names, environment variables, status claims, and behavioral descriptions. Substantive changes require authoritative repository evidence and explicit review.

Contradictions, obsolete claims, and missing required content shall be reported for review. They shall not be silently resolved. Requirement strength expressed by `shall`, `must`, `should`, `may`, or equivalent language shall not be changed without substantive review.

## 8. Validation Requirements

Updated documentation shall be validated for:

- Markdown syntax and heading hierarchy.
- Repository-relative links and referenced paths.
- Consistent titles, terminology, filenames, and configuration names.
- MkDocs navigation and strict build behavior.
- Compliance with the applicable document-family structure.
- Unintended factual additions, removals, or requirement changes.
- Changed-file scope through a path-scoped Git diff.

Validation shall distinguish automated checks from human review. A formatting pass shall not be reported as content validation unless the underlying claims were verified against authoritative repository evidence.

## 9. Spreadsheet Companion Documents

When project tracking or structured data is better represented in a spreadsheet, a companion OpenDocument Spreadsheet (`.ods`) may accompany a Markdown document. The Markdown document remains the narrative description, while the spreadsheet serves as the authoritative structured data source. Companion documents shall share the same numeric document identifier.

## 10. Python Source File Header Standard

All Python source files shall begin with the standard Project0 file header.

The header shall identify the owning platform component or AI agent, the source filename, and a concise statement describing the file's primary responsibility.

Standard format:

```python
## ============================================================
## Project0 - <Platform Component or AI Agent>
#
## File: <filename>.py
#
## Purpose:
##     <Brief description of the file's primary responsibility.>
#
## ============================================================
```

## 11. Repository Baseline Context

Repository baseline documents provide optional reference context to the Documentation Agent. Their paths are repository-specific configuration and must not be hard-coded requirements of the reusable agent framework. Baseline documents are reference-only unless they are explicitly identified as target documentation paths.
