---
name: strict-documentation-editor
description: Performs minimal source-grounded updates to existing controlled Markdown documentation while preserving unrelated content and exact repository locations.
metadata:
  category: documentation
  project0-phase: local
---

# Strict Documentation Editing

Treat target documentation as an existing controlled artifact.

## Requirements

- Analyze only the supplied target documentation, authoritative source content, and request.
- Treat Ground Truth Source content as read-only evidence.
- Modify only permitted target documentation paths.
- Make only the minimum textual modification required.
- Preserve repository-relative paths and existing Markdown formatting.
- Preserve existing content unrelated to the requested change.
- Do not rewrite, reorder, normalize, or reproduce unrelated Markdown content.
- Do not change metadata or other lines unless required by the requested update.
- Return actual Markdown content to apply, not instructions, plans, or descriptions of content to write.
- Use exact existing section headings and exact verbatim anchor text when supplied.
- Do not invent or paraphrase section names.
- Do not reproduce surrounding document or section content in a localized update.
- If adding information to an existing list, return only the new list item or items.
- Report warnings only when directly supported by the supplied context.
- When reproducing source code, interface signatures, method declarations, type annotations, default values, docstrings, placeholders, or parameter ordering from an authoritative source, preserve the authoritative source text exactly.
- Do not substitute implementation placeholders or equivalent-looking syntax when reproducing authoritative source code; for example, do not replace `...` with `pass` or otherwise normalize the source representation.
