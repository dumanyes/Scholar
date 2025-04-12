from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

project_mgmt_skills = {
    "Agile Methodology": [
        "Scrum", "Kanban", "User Stories", "Sprints", "Agile Ceremonies",
        "Backlog Grooming", "Agile Metrics", "Agile Tools", "Burndown Charts",
        "Agile Coaching", "Velocity Tracking", "Agile Mindset", "Retrospectives",
        "Agile Transformation", "Scaled Agile (SAFe)"
    ],
    "Scrum": [
        "Scrum Roles", "Sprint Planning", "Daily Standups", "Sprint Review",
        "Sprint Retrospective", "Scrum Artifacts", "Product Backlog",
        "Sprint Backlog", "Scrum Board", "Definition of Done", "Scrum Master Skills",
        "Team Velocity", "Burndown Charts", "Scrum Ceremonies", "Scrum Values"
    ],
    "Kanban": [
        "Kanban Board", "Work In Progress (WIP)", "Pull System", "Cycle Time",
        "Lead Time", "Flow Efficiency", "Swimlanes", "Cumulative Flow Diagram",
        "Service Level Expectation (SLE)", "Limiting WIP", "Continuous Delivery",
        "Bottleneck Analysis", "Card Aging", "Classes of Service", "Visual Signals"
    ],
    "Waterfall Model": [
        "Requirements Gathering", "System Design", "Implementation",
        "Integration & Testing", "Deployment", "Maintenance", "Milestone Planning",
        "Documented Processes", "Sequential Phases", "Fixed Scope",
        "Project Lifecycle", "Phase Reviews", "Gantt Charts", "Change Requests",
        "Stakeholder Sign-off"
    ],
    "Project Planning": [
        "Scope Definition", "Milestones", "Deliverables", "Project Timeline",
        "Work Breakdown Structure (WBS)", "Dependencies", "Critical Path Method (CPM)",
        "Resource Allocation", "Budget Estimation", "Contingency Planning",
        "Planning Tools", "Task Prioritization", "Project Charter", "Assumption Log",
        "Planning Workshops"
    ],
    "Risk Management": [
        "Risk Identification", "Risk Assessment", "Risk Matrix", "Probability & Impact",
        "Mitigation Plans", "Contingency Plans", "Risk Register", "SWOT Analysis",
        "Qualitative Risk Analysis", "Quantitative Risk Analysis", "Residual Risk",
        "Risk Audits", "Early Warning Indicators", "Risk Owner Assignment", "Risk Communication"
    ],
    "Budgeting": [
        "Cost Estimation", "Budget Baseline", "Variance Analysis", "Cost Control",
        "Earned Value Management", "Funding Requirements", "Contingency Reserves",
        "Top-down Budgeting", "Bottom-up Budgeting", "Forecasting", "Budget Reviews",
        "Cash Flow Analysis", "Financial Reporting", "Budget Approval", "Budget Reallocation"
    ],
    "Task Management Tools": [
        "Jira", "Asana", "Trello", "ClickUp", "Monday.com", "Notion",
        "Microsoft Project", "Basecamp", "Smartsheet", "Wrike", "Todoist",
        "Backlog", "GanttPRO", "Zoho Projects", "Airtable"
    ],
    "Gantt Charts": [
        "Timeline Planning", "Milestone Visualization", "Task Dependencies",
        "Progress Tracking", "Critical Path Visualization", "Baseline Comparison",
        "Gantt Tools", "Interactive Gantt Charts", "Time Estimation", "Chart Updating",
        "Project Phases", "Task Duration", "Slack Time", "Schedule Buffer", "Resource Assignment"
    ],
    "Roadmapping": [
        "Product Roadmaps", "Technology Roadmaps", "Strategic Planning",
        "Milestone Tracking", "Release Planning", "Timeline Alignment",
        "Goals and Initiatives", "Themes and Epics", "Roadmapping Tools",
        "Cross-functional Planning", "Vision Mapping", "Dependencies Mapping",
        "Backlog Prioritization", "Quarterly Planning", "Stakeholder Alignment"
    ],
    "Stakeholder Management": [
        "Stakeholder Identification", "Stakeholder Analysis", "Engagement Strategies",
        "Expectation Management", "Communication Planning", "Stakeholder Matrix",
        "Power/Interest Grid", "Escalation Processes", "Feedback Gathering",
        "Conflict Resolution", "Status Updates", "Stakeholder Interviews",
        "Influence Mapping", "Stakeholder Buy-in", "Change Impact Analysis"
    ],
    "OKRs & KPIs": [
        "Objective Setting", "Key Results Definition", "Tracking Progress", "Performance Metrics",
        "Alignment with Strategy", "Weekly Check-ins", "KPI Dashboards", "SMART Goals",
        "Quantitative Indicators", "Qualitative Indicators", "Benchmarking", "Outcome vs Output",
        "OKR Tools", "Quarterly Reviews", "Goal Cascading"
    ],
    "Time Management": [
        "Time Blocking", "Pomodoro Technique", "Eisenhower Matrix", "Time Auditing",
        "Task Prioritization", "Scheduling", "Time Tracking Tools", "Meeting Management",
        "Focus Techniques", "Avoiding Multitasking", "Deadline Management", "Buffer Time",
        "Work-Life Balance", "Daily Planning", "Goal-Oriented Planning"
    ],
    "Documentation & Reporting": [
        "Project Reports", "Meeting Minutes", "Status Updates", "Lessons Learned",
        "Risk Reports", "Technical Documentation", "Change Logs", "Progress Reports",
        "Budget Reports", "Time Reports", "Requirement Documentation", "Acceptance Criteria",
        "Issue Logs", "Action Items", "Final Project Reports"
    ],
    "Resource Allocation": [
        "Resource Planning", "Resource Leveling", "Role Assignment", "Skills Mapping",
        "Capacity Planning", "Utilization Tracking", "Team Availability", "Task Distribution",
        "Cross-Functional Teams", "Outsourcing Decisions", "Tool Assignments", "Time Tracking",
        "Backup Planning", "Load Balancing", "Resource Forecasting"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in project_mgmt_skills.items():
    subcat = SkillsSubCategory.objects.filter(name=subcat_name).first()
    if not subcat:
        missing_subcats.append(subcat_name)
        print(f"❌ Subcategory not found: {subcat_name}")
        continue

    print(f"\n📂 Processing subcategory: {subcat_name}")
    for skill_name in skill_list:
        try:
            obj, is_new = Skill.objects.get_or_create(name=skill_name, subcategory=subcat)
            if is_new:
                created += 1
                print(f"✅ Created: {skill_name}")
            else:
                skipped += 1
                print(f"⚠️ Already exists: {skill_name}")
        except IntegrityError:
            skipped += 1
            print(f"🚫 Integrity error (skipped): {skill_name}")

print("\n🎉 Import Complete!")
print(f"✅ Total created: {created}")
print(f"⚠️ Total skipped: {skipped}")
if missing_subcats:
    print("❌ Missing subcategories:")
    for subcat in missing_subcats:
        print(f" - {subcat}")
