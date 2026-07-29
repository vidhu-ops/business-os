# IIDATECH Employee OS - Figma Component Spec

## Screens
1. Company Dashboard - revenue, burn, runway, projects, alerts
2. Employee Cards - avatar, role, status, task, progress, KPIs
3. Live Activity Feed - Slack-style timeline
4. Chat - founder to employee messaging
5. Approval Center - budget and action approvals
6. Deliverables - CSV, reports, proposals, campaigns

## Components
- MetricCard, GoalList, ProjectRow, AlertBanner
- EmployeeCard (Sarah example: Growth Manager, Working, 72%)
- ActivityItem, ChatBubble, ApprovalCard, DeliverableRow

## Layout
Left column: dashboard, team grid, deliverables
Right column: activity, approvals, chat

## Streamlit entry
iidatech.ui.workspace.render_employee_os wired in preview Employees tab.
