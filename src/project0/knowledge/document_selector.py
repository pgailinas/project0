# ============================================================
# Project0 - Document Selector
#
# File: document_selector.py
#
# Purpose:
#     Select relevant repository documents using deterministic
#     Project0 knowledge rules.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from project0.models.knowledge_models import (
    DocumentRecord,
    DocumentReference,
    DocumentSelection,
    KnowledgeRequest,
)


class DocumentSelector:
    """Select repository documents for a knowledge request."""

    _BASELINE_DOCUMENTS = (
        Path("docs/project/Project_Charter.md"),
        Path("docs/project/Documentation_Standards.md"),
    )

    _STOP_WORDS = {
        "and",
        "are",
        "but",
        "for",
        "from",
        "had",
        "has",
        "have",
        "into",
        "its",
        "not",
        "our",
        "than",
        "that",
        "the",
        "their",
        "then",
        "these",
        "this",
        "those",
        "was",
        "were",
        "with",
        "you",
        "your",
    }

    _EXPLICIT_PATH_SCORE = 100.0
    _REQUIRED_TAG_SCORE = 20.0
    _SEARCH_TERM_SCORE = 10.0
    _CHANGED_PATH_SCORE = 5.0
    _BASELINE_SCORE = 1.0

    def select_documents(
        self,
        request: KnowledgeRequest,
        documents: Sequence[DocumentRecord],
    ) -> DocumentSelection:
        """Select documents relevant to a knowledge request."""

        documents_by_path = {
            document.path: document
            for document in documents
        }

        selected: dict[Path, DocumentReference] = {}
        warnings: list[str] = []

        self._select_requested_paths(
            request=request,
            documents_by_path=documents_by_path,
            selected=selected,
            warnings=warnings,
        )

        if not request.requested_paths:
            self._select_matching_documents(
                request=request,
                documents=documents,
                selected=selected,
            )

        if request.include_baseline_documents:
            self._select_baseline_documents(
                documents_by_path=documents_by_path,
                selected=selected,
            )

        ordered_references = tuple(
            sorted(
                selected.values(),
                key=lambda reference: (
                    -reference.score,
                    reference.path.as_posix(),
                ),
            )[: request.maximum_documents]
        )

        selected_paths = {
            reference.path
            for reference in ordered_references
        }

        ordered_documents = tuple(
            documents_by_path[reference.path]
            for reference in ordered_references
        )

        excluded_paths = tuple(
            sorted(
                (
                    document.path
                    for document in documents
                    if document.path not in selected_paths
                ),
                key=lambda path: path.as_posix(),
            )
        )

        return DocumentSelection(
            documents=ordered_documents,
            references=ordered_references,
            excluded_paths=excluded_paths,
            warnings=tuple(warnings),
        )

    def _select_requested_paths(
        self,
        request: KnowledgeRequest,
        documents_by_path: dict[Path, DocumentRecord],
        selected: dict[Path, DocumentReference],
        warnings: list[str],
    ) -> None:
        """Select explicitly requested documents."""

        for path in request.requested_paths:
            document = documents_by_path.get(path)

            if document is None:
                warnings.append(
                    f"Requested document was not found: {path}"
                )
                continue

            selected[path] = DocumentReference(
                path=document.path,
                title=document.title,
                reason="Explicitly requested document.",
                score=self._EXPLICIT_PATH_SCORE,
                matched_terms=(),
            )

    def _select_matching_documents(
        self,
        request: KnowledgeRequest,
        documents: Sequence[DocumentRecord],
        selected: dict[Path, DocumentReference],
    ) -> None:
        """Select documents matching deterministic request criteria."""

        for document in documents:
            score = 0.0
            reasons: list[str] = []
            matched_terms: list[str] = []

            tag_matches = self._match_required_tags(
                request=request,
                document=document,
            )

            if tag_matches:
                score += (
                    len(tag_matches)
                    * self._REQUIRED_TAG_SCORE
                )
                reasons.append("Matched required document tags.")
                matched_terms.extend(tag_matches)

            search_matches = self._match_search_terms(
                request=request,
                document=document,
            )

            if search_matches:
                score += (
                    len(search_matches)
                    * self._SEARCH_TERM_SCORE
                )
                reasons.append("Matched request search terms.")
                matched_terms.extend(search_matches)

            changed_path_matches = self._match_changed_paths(
                request=request,
                document=document,
            )

            if changed_path_matches:
                score += (
                    len(changed_path_matches)
                    * self._CHANGED_PATH_SCORE
                )
                reasons.append("Matched changed repository paths.")
                matched_terms.extend(changed_path_matches)

            if score == 0.0:
                continue

            existing_reference = selected.get(document.path)

            if existing_reference is not None:
                selected[document.path] = DocumentReference(
                    path=existing_reference.path,
                    title=existing_reference.title,
                    reason=existing_reference.reason,
                    score=existing_reference.score + score,
                    matched_terms=self._deduplicate_terms(
                        (
                            *existing_reference.matched_terms,
                            *matched_terms,
                        )
                    ),
                )
                continue

            selected[document.path] = DocumentReference(
                path=document.path,
                title=document.title,
                reason=" ".join(reasons),
                score=score,
                matched_terms=self._deduplicate_terms(
                    tuple(matched_terms)
                ),
            )

    def _select_baseline_documents(
        self,
        documents_by_path: dict[Path, DocumentRecord],
        selected: dict[Path, DocumentReference],
    ) -> None:
        """Select standard baseline project documents."""

        for path in self._BASELINE_DOCUMENTS:
            document = documents_by_path.get(path)

            if document is None or path in selected:
                continue

            selected[path] = DocumentReference(
                path=document.path,
                title=document.title,
                reason="Baseline project document.",
                score=self._BASELINE_SCORE,
                matched_terms=(),
            )

    def _match_required_tags(
        self,
        request: KnowledgeRequest,
        document: DocumentRecord,
    ) -> tuple[str, ...]:
        """Return required tags matched by a document."""

        document_tags = {
            tag.casefold()
            for tag in document.tags
        }

        return tuple(
            tag
            for tag in request.required_tags
            if tag.casefold() in document_tags
        )

    def _match_search_terms(
        self,
        request: KnowledgeRequest,
        document: DocumentRecord,
    ) -> tuple[str, ...]:
        """Return request terms found in document searchable text."""

        searchable_text = " ".join(
            (
                document.path.as_posix(),
                document.title,
                document.content,
                " ".join(
                    heading.title
                    for heading in document.headings
                ),
                " ".join(document.tags),
            )
        ).casefold()

        terms = (
            request.search_terms
            if request.search_terms
            else self._query_terms(request.query)
        )

        return tuple(
            term
            for term in terms
            if term.casefold() in searchable_text
        )

    def _match_changed_paths(
        self,
        request: KnowledgeRequest,
        document: DocumentRecord,
    ) -> tuple[str, ...]:
        """Return changed path terms matched by a document."""

        searchable_text = " ".join(
            (
                document.path.as_posix(),
                document.title,
                document.content,
                " ".join(document.tags),
            )
        ).casefold()

        matched_terms: list[str] = []

        for changed_path in request.changed_paths:
            path_terms = self._path_terms(changed_path)

            if any(
                term.casefold() in searchable_text
                for term in path_terms
            ):
                matched_terms.append(changed_path.as_posix())

        return tuple(matched_terms)

    def _query_terms(
        self,
        query: str,
    ) -> tuple[str, ...]:
        """Create deterministic search terms from a request query."""

        return tuple(
            term
            for term in (
                word.strip(".,:;!?()[]{}").casefold()
                for word in query.split()
            )
            if len(term) >= 3
            and term not in self._STOP_WORDS
        )

    def _path_terms(
        self,
        path: Path,
    ) -> tuple[str, ...]:
        """Create deterministic matching terms from a repository path."""

        terms: list[str] = []

        for part in path.with_suffix("").parts:
            normalized_part = part.replace("-", "_")

            terms.extend(
                term.casefold()
                for term in normalized_part.split("_")
                if len(term) >= 3
            )

        return self._deduplicate_terms(tuple(terms))

    def _deduplicate_terms(
        self,
        terms: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Return terms in original order without duplicates."""

        unique_terms: list[str] = []
        seen_terms: set[str] = set()

        for term in terms:
            normalized_term = term.casefold()

            if normalized_term in seen_terms:
                continue

            seen_terms.add(normalized_term)
            unique_terms.append(term)

        return tuple(unique_terms)
