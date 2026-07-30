from __future__ import annotations

import sys
import types

import pytest

import iidatech.services.report_engine as report_engine
from iidatech.services.report_engine import (
    _HeadlessStreamlitModule,
    _bind_headless_streamlit,
    _patch_streamlit_module,
)
from iidatech.ui.streamlit_adapter import HeadlessSessionState


@pytest.fixture
def isolated_streamlit_modules(monkeypatch):
    saved = {
        name: sys.modules.get(name)
        for name in (
            "streamlit",
            "streamlit.components",
            "streamlit.components.v1",
            "streamlit_app",
            "app",
        )
    }
    for name in saved:
        sys.modules.pop(name, None)

    monkeypatch.setattr(report_engine, "_STREAMLIT_PATCHED", False, raising=False)
    monkeypatch.setattr(report_engine, "_HEADLESS_STREAMLIT_MODULE", None, raising=False)
    monkeypatch.setattr(report_engine, "_APP_MODULE", None, raising=False)

    def _restore() -> None:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    yield
    _restore()


@pytest.fixture
def block_streamlit_import(monkeypatch):
    original_import = __import__

    def _blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name not in sys.modules and (name == "streamlit" or name.startswith("streamlit.")):
            raise ImportError("streamlit is not installed")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", _blocked_import)


def test_patch_streamlit_module_installs_headless_shim_without_streamlit(
    block_streamlit_import,
    isolated_streamlit_modules,
):
    _patch_streamlit_module()

    assert report_engine._STREAMLIT_PATCHED is True
    assert isinstance(sys.modules["streamlit"], _HeadlessStreamlitModule)
    assert isinstance(sys.modules["streamlit.components"], types.ModuleType)
    assert hasattr(sys.modules["streamlit.components.v1"], "html")
    assert hasattr(sys.modules["streamlit.components.v1"], "iframe")

    import streamlit as st

    assert isinstance(st.session_state, HeadlessSessionState)
    st.stop()
    st.rerun()
    st.components.v1.html("<div>ok</div>")
    st.components.v1.iframe("https://example.com")


def test_bind_headless_streamlit_rebinds_shim_adapter(
    block_streamlit_import,
    isolated_streamlit_modules,
):
    _patch_streamlit_module()

    session_state = HeadlessSessionState(business_application_purpose="Test purpose")
    app = types.SimpleNamespace()
    placeholder = _bind_headless_streamlit(app, session_state)

    streamlit_mod = sys.modules["streamlit"]
    assert app.st is placeholder
    assert streamlit_mod._adapter is placeholder
    assert streamlit_mod.session_state is session_state
    assert streamlit_mod.session_state["business_application_purpose"] == "Test purpose"
    assert streamlit_mod.stop.__self__ is placeholder
    assert streamlit_mod.rerun.__self__ is placeholder