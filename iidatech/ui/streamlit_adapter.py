"""Headless Streamlit adapter — UI boundary for legacy app.py orchestration."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredEngineError:
    success: bool = False
    error_code: str = ""
    recoverable: bool = True
    section: int | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "error_code": self.error_code,
            "recoverable": self.recoverable,
            "section": self.section,
            "message": self.message,
        }


class ReportEngineAbort(Exception):
    """Fatal abort — preflight validation failed; entire report must stop."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "fatal_abort",
        stop_stack: str = "",
        stop_context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.stop_stack = stop_stack
        self.stop_context = stop_context or {}


class HeadlessSessionState(dict):
    """Minimal session_state replacement for headless runs."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class _ContainerLike:
  """Minimal placeholder for st.empty() / st.container() in headless runs."""

  def container(self, *args: Any, **kwargs: Any) -> _ContainerLike:
      return self

  def progress(self, *args: Any, **kwargs: Any) -> None:
      return None

  def empty(self, *args: Any, **kwargs: Any) -> _ContainerLike:
      return self

  def update(self, *args: Any, **kwargs: Any) -> None:
      return None

  def metric(self, *args: Any, **kwargs: Any) -> None:
      return None

  def __enter__(self) -> _ContainerLike:
      return self

  def __exit__(self, *args: Any) -> None:
      return None


class _ProgressLike(_ContainerLike):
  pass


class HeadlessStreamlitAdapter:
    """Drop-in Streamlit stand-in for backend/headless report generation."""

    def __init__(self, session_state: HeadlessSessionState | None = None) -> None:
        self.session_state = session_state or HeadlessSessionState()
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.infos: list[str] = []
        self.recoverable_errors: list[dict[str, Any]] = []
        self._current_section: int | None = None
        self._fatal_abort = False
        self.last_stop_stack: str = ""
        self.last_stop_context: dict[str, Any] = {}

    def set_execution_section(self, section_id: int | None) -> None:
        self._current_section = int(section_id) if section_id is not None else None

    def stop(self, *args: Any, **kwargs: Any) -> None:
        message = str(args[0] if args else kwargs.get("message") or "").strip()
        if not message or message == "execution stopped":
            if self.errors:
                message = self.errors[-1]
            elif self.warnings:
                message = self.warnings[-1]
            elif self.infos:
                message = self.infos[-1]
            else:
                message = "execution stopped"
        recoverable = kwargs.get("recoverable")
        if recoverable is None:
            recoverable = self._current_section is not None
        error_code = str(kwargs.get("error_code") or ("section_synthesis_failed" if recoverable else "preflight_abort"))
        self.last_stop_stack = "".join(traceback.format_stack(limit=32))
        self.last_stop_context = {
            "message": message,
            "error_code": error_code,
            "recoverable": bool(recoverable),
            "section": self._current_section,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "infos": list(self.infos[-3:]),
        }
        structured = StructuredEngineError(
            success=False,
            error_code=error_code,
            recoverable=bool(recoverable),
            section=self._current_section,
            message=message,
        )
        structured_dict = structured.to_dict()
        structured_dict["stop_stack"] = self.last_stop_stack
        self.recoverable_errors.append(structured_dict)
        self.errors.append(message)
        if recoverable:
            return
        self._fatal_abort = True
        raise ReportEngineAbort(
            message,
            error_code=error_code,
            stop_stack=self.last_stop_stack,
            stop_context=self.last_stop_context,
        )

    def rerun(self, *args: Any, **kwargs: Any) -> None:
        return None

    def __getitem__(self, key: Any) -> HeadlessStreamlitAdapter:
        return self

    def _record(self, bucket: list[str], message: Any) -> None:
        text = str(message).strip()
        if text:
            bucket.append(text)

    def __getattr__(self, name: str) -> Any:
        if name == "columns":
            def _columns(spec: Any, *args: Any, **kwargs: Any) -> list[HeadlessStreamlitAdapter]:
                count = spec if isinstance(spec, int) else len(spec)
                return [HeadlessStreamlitAdapter(self.session_state) for _ in range(max(int(count), 1))]
            return _columns
        if name in {"progress", "status"}:
            return lambda *args, **kwargs: _ProgressLike()
        if name == "empty":
            return lambda *args, **kwargs: _ContainerLike()
        if name in {"spinner", "expander", "container", "sidebar"}:
            return lambda *args, **kwargs: self
        if name == "metric":
            return lambda *args, **kwargs: None
        if name == "warning":
            return lambda *args, **kwargs: self._record(self.warnings, args[0] if args else "")
        if name == "error":
            return lambda *args, **kwargs: self._record(self.errors, args[0] if args else "")
        if name in {"info", "success", "caption", "markdown", "write", "subheader", "title", "divider"}:
            return lambda *args, **kwargs: self._record(self.infos, args[0] if args else "")
        if name in {"button", "download_button", "checkbox", "text_input", "text_area", "selectbox", "slider", "number_input", "file_uploader", "radio"}:
            if name == "checkbox":
                return lambda *args, **kwargs: bool(kwargs.get("value", True if "cloud synthesis" in str(args[0] if args else "").lower() else kwargs.get("value", False)))
            if name == "slider":
                return kwargs.get("value", (1, 3)) if "value" in kwargs else (1, 3)
            if name == "number_input":
                return kwargs.get("value", 0)
            if name == "selectbox":
                options = args[1] if len(args) > 1 else kwargs.get("options", [])
                index = kwargs.get("index", 0)
                try:
                    return options[index]
                except Exception:
                    return options[0] if options else ""
            return lambda *args, **kwargs: kwargs.get("value", args[1] if len(args) > 1 else "")
        if name in {"dataframe", "table", "json", "code"}:
            return lambda *args, **kwargs: None

        def _noop(*args: Any, **kwargs: Any) -> HeadlessStreamlitAdapter:
            return self

        return _noop

    def __enter__(self) -> HeadlessStreamlitAdapter:
        return self

    def __exit__(self, *args: Any) -> None:
        return None