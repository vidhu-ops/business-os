"""Shared CSS for Employee OS."""







EMPLOYEE_OS_CSS = """



<style>



.iida-os { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif; }



.iida-metric-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; }



.iida-metric-label { color: #64748b; font-size: 0.75rem; text-transform: uppercase; }



.iida-metric-value { font-size: 1.5rem; font-weight: 700; color: #0f172a; }



.iida-alert { background: #fff7ed; border-left: 3px solid #f97316; padding: 0.65rem; border-radius: 8px; margin: 0.35rem 0; }



.iida-alert-critical { background: #fef2f2; border-left-color: #ef4444; }



.iida-emp-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem; }



.iida-avatar { width: 42px; height: 42px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; }



.iida-status-working { background: #dcfce7; color: #166534; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; }



.iida-status-blocked { background: #fee2e2; color: #991b1b; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; }



.iida-status-idle { background: #f1f5f9; color: #475569; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; }



.iida-progress-bar { background: #e2e8f0; border-radius: 999px; height: 6px; overflow: hidden; margin: 0.5rem 0; }



.iida-progress-fill { background: linear-gradient(90deg, #6366f1, #8b5cf6); height: 100%; }



.iida-feed-item { padding: 0.65rem 0; border-bottom: 1px solid #f1f5f9; }



.iida-approval-card { background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; }



.iida-badge { display: inline-block; padding: 0.12rem 0.45rem; border-radius: 999px; font-size: 0.68rem; font-weight: 650; margin-right: 0.25rem; }



.iida-badge-verified { background: #dcfce7; color: #166534; }



.iida-badge-simulated { background: #e0e7ff; color: #3730a3; }



.iida-badge-blocked { background: #fee2e2; color: #991b1b; }

.iida-war-room { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; }

.iida-debate-arg { border-left: 3px solid #6366f1; padding: 0.5rem 0.65rem; margin: 0.35rem 0; background: #fff; border-radius: 6px; }

.iida-debate-obj { border-left: 3px solid #f59e0b; padding: 0.5rem 0.65rem; margin: 0.35rem 0; background: #fffbeb; border-radius: 6px; }

.iida-debate-counter { border-left: 3px solid #10b981; padding: 0.5rem 0.65rem; margin: 0.35rem 0; background: #ecfdf5; border-radius: 6px; }

.iida-consensus { background: #ede9fe; border: 1px solid #c4b5fd; border-radius: 10px; padding: 0.75rem; margin-top: 0.5rem; }

.iida-vote-pill { display: inline-block; background: #e2e8f0; padding: 0.1rem 0.45rem; border-radius: 999px; font-size: 0.72rem; margin: 0.1rem; }



</style>



"""











def inject_employee_os_styles(st) -> None:



    st.markdown(EMPLOYEE_OS_CSS, unsafe_allow_html=True)



