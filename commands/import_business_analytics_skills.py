from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

business_analytics_skills = {
    "Business Intelligence Tools": [
        "Tableau", "Power BI", "Looker", "QlikView", "Google Data Studio", "Data Blending", "Drill-Down Analysis",
        "Interactive Dashboards", "Embedded Analytics", "KPI Tracking", "Real-Time Reporting", "SQL Integration",
        "Custom Visuals", "Data Warehousing", "Storytelling with Data"
    ],
    "KPI Design": [
        "SMART KPIs", "Lagging vs Leading Indicators", "Benchmarking", "Balanced Scorecard", "Performance Metrics",
        "KPI Dashboards", "Goal Alignment", "Time-bound KPIs", "Data Collection", "Business Objectives",
        "Cascading KPIs", "KPI Trees", "Quantitative KPIs", "Qualitative KPIs", "Visualization of KPIs"
    ],
    "Customer Segmentation": [
        "RFM Analysis", "Clustering", "Demographic Segmentation", "Behavioral Segmentation", "Psychographic Segmentation",
        "Value-Based Segmentation", "Predictive Segmentation", "Customer Personas", "Look-alike Modeling",
        "Segmentation Trees", "K-Means", "Hierarchical Clustering", "LTV Segmentation", "Churn-Based Segments", "Purchase Behavior Analysis"
    ],
    "Financial Modeling": [
        "Discounted Cash Flow", "Three-Statement Model", "Scenario Analysis", "Sensitivity Analysis", "Capital Budgeting",
        "LBO Models", "Valuation Techniques", "Financial Ratios", "Revenue Forecasting", "Excel Modeling",
        "NPV & IRR", "Financial Assumptions", "Debt Modeling", "Equity Analysis", "Break-Even Analysis"
    ],
    "Operations Research": [
        "Linear Programming", "Integer Programming", "Simulation Modeling", "Decision Trees", "Network Optimization",
        "Game Theory", "Queuing Theory", "Inventory Models", "Scheduling Problems", "Transportation Models",
        "Assignment Problems", "Heuristic Methods", "Optimization Solvers", "Monte Carlo Simulation", "Markov Chains"
    ],
    "CRM Analytics": [
        "Customer Lifetime Value", "Customer Retention", "Lead Scoring", "Sales Funnel Analysis", "Behavior Tracking",
        "Churn Prediction", "Campaign Performance", "Customer Journey Mapping", "Engagement Metrics", "Segmentation Models",
        "A/B Testing", "Email Analytics", "NPS Analysis", "Touchpoint Attribution", "Upsell & Cross-sell Analysis"
    ],
    "Excel Power Query": [
        "Data Import", "M Language", "Data Transformation", "Merge & Append", "Pivoting", "Unpivoting",
        "Query Parameters", "Custom Columns", "Applied Steps", "Loading to Data Model", "Combining Files",
        "Dynamic Data Sources", "Conditional Columns", "Fuzzy Matching", "Scheduled Refresh"
    ],
    "Forecasting": [
        "Time Series Models", "ARIMA", "Exponential Smoothing", "Prophet", "Seasonal Decomposition",
        "Trend Analysis", "Holt-Winters", "Rolling Forecasts", "Prediction Intervals", "Outlier Detection",
        "Backtesting", "Model Selection", "Forecast Accuracy", "Business Forecasting", "Demand Forecasting"
    ],
    "Risk Analysis": [
        "Risk Matrix", "Monte Carlo Simulation", "What-if Analysis", "Stress Testing", "Value at Risk (VaR)",
        "Scenario Planning", "Contingency Planning", "Qualitative Risk Assessment", "Quantitative Risk Assessment",
        "Sensitivity Analysis", "Decision Trees", "Failure Mode Analysis", "Bayesian Risk Models", "Credit Risk Scoring", "Risk Dashboards"
    ],
    "Dashboard Design": [
        "Data Visualization Principles", "Color Theory", "Layout Optimization", "Responsive Design", "User-Centered Design",
        "Filters & Interactivity", "Mobile Dashboards", "Real-Time Dashboards", "Performance Indicators",
        "Visual Hierarchy", "Typography", "Drill-Down Features", "Cross-Filtering", "KPI Cards", "Accessibility"
    ],
    "Market Basket Analysis": [
        "Association Rules", "Apriori Algorithm", "Lift Metrics", "Support & Confidence", "Frequent Itemsets",
        "E-commerce Data", "Transaction Data Processing", "Recommendation Systems", "Affinity Analysis", "Rule Pruning",
        "FP-Growth", "Sequential Patterns", "Cross-Sell Opportunities", "Promotion Strategies", "Basket Profiling"
    ],
    "Sales Analytics": [
        "Sales Funnel Metrics", "Lead Conversion", "Win Rate Analysis", "Revenue Attribution", "Territory Performance",
        "Quota Achievement", "Customer Acquisition Cost", "Deal Velocity", "Forecast Accuracy", "Sales Cycle Length",
        "Sales Targeting", "Sales Enablement", "Pipeline Analysis", "Sales vs Targets", "Incentive Planning"
    ],
    "Churn Prediction": [
        "Retention Modeling", "Cohort Analysis", "Survival Analysis", "Early Warning Signals", "Customer Feedback Analysis",
        "Usage Pattern Monitoring", "Engagement Scores", "Sentiment Analysis", "Predictive Modeling", "Logistic Regression",
        "Decision Trees", "Time-to-Churn Models", "Customer Satisfaction", "Reactivation Campaigns", "Churn Scoring"
    ],
    "ROI Analysis": [
        "Cost-Benefit Analysis", "NPV & IRR", "Marketing ROI", "Project ROI", "ROI Dashboards", "Attribution Modeling",
        "Customer ROI", "CAC vs LTV", "Break-Even Analysis", "Time to ROI", "Efficiency Ratios", "Investment Metrics",
        "Capital Allocation", "ROI Forecasting", "KPI ROI Mapping"
    ],
    "Data-driven Strategy": [
        "Strategic KPIs", "SWOT from Data", "Executive Dashboards", "Objective Setting", "Hypothesis Testing",
        "Data Storytelling", "Scenario Simulation", "Key Metric Tracking", "Strategy Maps", "Goal Alignment",
        "Customer Insights", "Performance Reviews", "Data Roadmaps", "Analytics-Driven Culture", "OKRs"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in business_analytics_skills.items():
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
