"""Public package interface for SpecMaker Core."""

from specmaker_core._dependencies.schemas import documents as _documents
from specmaker_core._dependencies.schemas import shared as _shared
from specmaker_core.review import (
    Completed,
    Deferred,
    RunOutcome,
    RunToken,
    list_agents,
    resume,
    review,
)

# Re-export for public API convenience
DocumentDraft = _documents.DocumentDraft
Manuscript = _documents.Manuscript
ReviewIssue = _documents.ReviewIssue
ReviewReport = _documents.ReviewReport
ProjectContext = _shared.ProjectContext
