"""Customer-facing Employee OS UI layer."""
from iidatech.ui.view_models import build_employee_os_workspace
from iidatech.ui.workspace import render_employee_os
from iidatech.ui.employee_os2 import render_employee_os2

__all__ = ["build_employee_os_workspace", "render_employee_os", "render_employee_os2"]
