"""Errors the CLI prints without a traceback."""


class PipelineError(Exception):
    """A user-facing failure: bad config, a missing object, a rejected constant."""


class RebaseConflictError(PipelineError):
    """Vanilla and the constants both changed the same fields."""

    def __init__(self, report_path, conflicts):
        self.report_path = report_path
        self.conflicts = conflicts
        super().__init__(
            f"{len(conflicts)} rebase conflict(s). Report: {report_path}. "
            "Edit mod/constants, or re-run with --accept after reviewing the report."
        )
