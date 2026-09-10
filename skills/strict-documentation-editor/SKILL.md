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
- Treat target documentation as an existing controlled artifact and Ground Truth Source content as read-only evidence.
- Modify only permitted target documentation paths.
- First compare authoritative source evidence against the existing documented contracts.
- Propose a change only when the source shows that an existing documented contract is missing, outdated, inaccurate, or materially incomplete.
- Treat source-grounded work as documentation synchronization, not implementation design or architecture review.
- Do not recommend adding, changing, or redesigning source fields, interfaces, behaviors, mechanisms, requirements, or implementation features.
- Do not propose documentation for behavior that is not already established by the authoritative source evidence.
- If authoritative source evidence does not establish a material documentation gap, return no proposed change for that point.
- Do not assume every authoritative source declaration requires documentation.
- Make only the minimum textual modification required.
- Preserve repository-relative paths, existing terminology, organization, writing style, and Markdown formatting.
- Do not regenerate the document.
- Do not reflow paragraphs or change existing line wrapping.
- Preserve trailing spaces used for Markdown line breaks.
- Preserve horizontal rule formatting exactly; do not normalize `---` separators.
- Do not add or remove blank lines unless required by the intended content change.
- Do not change heading levels or heading names unless explicitly requested.
- Do not modify tables, table spacing, or table alignment unless explicitly required by the requested change.
- Preserve existing content unrelated to the requested change.
- Do not rewrite, reorder, summarize, restructure, normalize, or reproduce unrelated Markdown content.
- Do not change document titles, metadata, version information, ownership information, or other lines unless required by the requested update.
- Return actual Markdown content to apply, not instructions, plans, recommendations, summaries, or descriptions of content to write.
- Do not return directive phrases such as `Add...`, `Include...`, `Explain...`, `Describe...`, `Document...`, or `Update the documentation...`.
- Use exact existing section headings and exact verbatim anchor text when supplied.
- Do not invent or paraphrase section names.
- Do not create new sections merely because authoritative source declarations exist.
- Do not reproduce surrounding document or section content in a localized update.
- If adding information to an existing list, return only the new list item or items.
- Report warnings only when directly supported by the supplied context.
- Treat authoritative source content as evidence for documentation meaning; do not copy implementation syntax into the target documentation unless the target form requires it.
- Match the existing documentation form of the affected target section, using prose, lists, tables, diagrams, or code only when consistent with that section.
- Do not introduce fenced source-code blocks unless the affected target section already uses comparable source-code examples or the user explicitly requests source code.
- When authoritative source defines an interface, model, or workflow contract, document the supported purpose, inputs, outputs, constraints, and behavior in the target document's existing style rather than reproducing the declaration.
- Do not invent examples, usage scenarios, behavior, or rationale that are not directly supported by the supplied context.
- Preserve semantic fidelity to the authoritative source and do not infer undocumented behavior.
- When reproducing source code, interface signatures, method declarations, type annotations, default values, docstrings, placeholders, or parameter ordering from an authoritative source, preserve the authoritative source text exactly.
- Do not substitute implementation placeholders or equivalent-looking syntax when reproducing authoritative source code; for example, do not replace `...` with `pass` or otherwise normalize the source representation.
- The resulting update must be suitable for direct repository replacement and should produce a minimal git diff containing only intended content changes and required metadata changes.
