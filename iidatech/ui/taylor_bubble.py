"""Floating Taylor (team leader) bubble - notifications, approvals, suggestions, voice.

Renders a fixed-position bubble in the bottom-right corner of the Employee OS page.
Streamlit cannot attach callbacks to injected HTML, so the pattern is:
- a CSS-pinned container holding a st.popover ("Taylor") with the actionable panel
- optional browser text-to-speech for new events via components.html
"""
from __future__ import annotations

from typing import Any

_BUBBLE_CSS = """
<style>
div[class*="st-key-taylor_bubble_dock"] {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
    width: auto;
}
div[class*="st-key-taylor_bubble_dock"] button[data-testid="stPopoverButton"] {
    border-radius: 999px;
    padding: 10px 18px;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #fff;
    border: none;
    box-shadow: 0 6px 24px rgba(79, 70, 229, 0.45);
    font-weight: 600;
}
div[class*="st-key-taylor_bubble_dock"] button[data-testid="stPopoverButton"]:hover {
    filter: brightness(1.1);
}
</style>
"""


def _speak(st: Any, text: str) -> None:
    """Browser TTS via Web Speech API (no server audio needed)."""
    try:
        import streamlit.components.v1 as components

        safe = text.replace("\\", " ").replace("`", "'").replace('"', "'")[:220]
        components.html(
            f"""
            <script>
            try {{
                const u = new SpeechSynthesisUtterance("{safe}");
                u.rate = 1.02; u.pitch = 1.0;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(u);
            }} catch (e) {{}}
            </script>
            """,
            height=0,
        )
    except Exception:
        pass


def render_taylor_bubble(
    st: Any,
    *,
    report_id: str,
    pulse: dict[str, Any],
    on_keys_anchor: str = "",
) -> dict[str, Any]:
    """Render the floating bubble. Returns founder actions taken this run.

    Action dict keys the caller must handle:
    - {"action": "approve_all"}
    - {"action": "retry_failed"}
    - {"action": "run_next"}
    - {"action": "employee_prompt", "harness_id": ..., "prompt": ...}
    """
    st.markdown(_BUBBLE_CSS, unsafe_allow_html=True)
    approvals = pulse.get("approvals") or []
    failed = pulse.get("failed") or []
    qc_failed = pulse.get("qc_failed") or []
    done = pulse.get("done") or []
    progress = pulse.get("progress") or {}
    headline = str(pulse.get("headline") or "")

    badge = ""
    if qc_failed:
        badge = f" ({len(qc_failed)} QC failed)"
    elif approvals:
        badge = f" ({len(approvals)} to approve)"
    elif failed:
        badge = f" ({len(failed)} stuck)"

    result: dict[str, Any] = {}

    voice_key = f"taylor_voice_{report_id}"
    seen_key = f"taylor_seen_sig_{report_id}"
    new_events = st.session_state.get(seen_key) != pulse.get("signature")

    dock = st.container(key="taylor_bubble_dock")
    with dock:
        label = f"Taylor{badge}" if not new_events else f"Taylor {'!' if badge else '*'}{badge}"
        with st.popover(label, use_container_width=False):
            st.markdown(f"**{headline}**")
            total = int(progress.get("total") or 0)
            if total:
                st.progress(min(1.0, (progress.get("done") or 0) / total), text=f"{progress.get('done')}/{total} tasks delivered")

            voice_on = st.toggle("Voice updates", value=bool(st.session_state.get(voice_key, False)), key=f"{voice_key}_toggle")
            st.session_state[voice_key] = voice_on

            if qc_failed:
                st.markdown("**QC failed — run stopped**")
                for row in qc_failed[:3]:
                    st.caption(f"- {row['title']}: {row.get('error') or 'quality check failed'}")
                if st.button("Retry QC-failed tasks", key=f"taylor_retry_{report_id}", type="primary"):
                    result = {"action": "retry_failed"}

            if approvals:
                st.markdown("**Needs your approval**")
                for row in approvals[:4]:
                    st.caption(f"- {row['title']} - this will {row['explanation']}.")
                if st.button(f"Approve all {len(approvals)}", key=f"taylor_approve_all_{report_id}", type="primary"):
                    result = {"action": "approve_all"}

            if failed and not qc_failed:
                st.markdown("**Needs attention**")
                for row in failed[:3]:
                    st.caption(f"- {row['title']}: {row['error'] or 'failed'}")

            if done:
                with st.expander(f"Delivered ({len(done)})", expanded=False):
                    for row in done[-5:]:
                        arts = ", ".join(row.get("artifacts") or []) or "no files"
                        st.caption(f"- {row['title']} - {arts}")

            sugg = pulse.get("suggestions") or []
            if sugg and not result:
                st.markdown("**What I suggest next**")
                for i, s in enumerate(sugg):
                    if st.button(s["label"], key=f"taylor_sugg_{report_id}_{i}"):
                        if s.get("kind") == "employee_prompt":
                            result = {"action": "employee_prompt", "harness_id": s.get("harness_id"), "prompt": s.get("prompt")}
                        elif s.get("kind") == "run_next":
                            result = {"action": "run_next"}
                        elif s.get("kind") == "retry_failed":
                            result = {"action": "retry_failed"}
                        elif s.get("kind") == "review_approvals":
                            st.info("Approval cards are just above." if approvals else "Nothing pending.")
                        elif s.get("kind") == "open_keys" and on_keys_anchor:
                            st.info("Scroll to the API keys section at the top of this page.")

    if new_events:
        st.session_state[seen_key] = pulse.get("signature")
        if st.session_state.get(voice_key) and headline:
            _speak(st, headline)
        if headline:
            st.toast(f"Taylor: {headline}", icon="\U0001f4ac")

    return result
