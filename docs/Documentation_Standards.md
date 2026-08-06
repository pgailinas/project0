# Documentation Standards

**Version:** 0.2  
**Owner:** Project0  
**Last Updated:** 2026-08-03

------------------------------------------------------------------------

# Documentation Principles

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

# Spreadsheet Companion Documents

When project tracking or structured data is better represented in a spreadsheet, a companion OpenDocument Spreadsheet (.ods) may accompany a Markdown document. The Markdown document remains the narrative description, while the spreadsheet serves as the authoritative structured data source. Companion documents shall share the same numeric document identifier.

### Python Source File Header Standard

All Python source files shall begin with the standard Project0 file header.

The header shall identify the owning platform component or AI agent, the source filename, and a concise statement describing the file's primary responsibility.

Standard format:

```python
# ============================================================
# Project0 - <Platform Component or AI Agent>
#
# File: <filename>.py
#
# Purpose:
#     <Brief description of the file's primary responsibility.>
#
# ============================================================
```
