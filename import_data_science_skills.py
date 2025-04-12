from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

ds_skills = {
    "Data Wrangling": [
        "Data Reshaping", "Merging Datasets", "Data Aggregation", "Pivoting", "Melting",
        "Datetime Parsing", "Data Type Conversion", "Handling Missing Data", "Filtering Rows", "Grouping Data",
        "Combining DataFrames", "Handling Duplicates", "Unstacking/Stacking", "Outlier Treatment", "Data Pipelines"
    ],
    "Data Cleaning": [
        "Handling Nulls", "Standardizing Text", "Removing Duplicates", "Fixing Data Types", "Outlier Detection",
        "Inconsistency Detection", "Missing Value Imputation", "Regular Expressions", "Text Normalization", "Data Validation",
        "String Cleaning", "Column Renaming", "Error Correction", "Dealing with Noise", "Data Integrity Checks"
    ],
    "Data Visualization": [
        "Bar Charts", "Histograms", "Box Plots", "Scatter Plots", "Heatmaps",
        "Line Graphs", "Pie Charts", "Interactive Dashboards", "Geospatial Maps", "Time Series Plots",
        "Faceting", "Data Storytelling", "Seaborn", "Plotly", "Matplotlib"
    ],
    "Statistical Modeling": [
        "Linear Regression", "Logistic Regression", "Hypothesis Testing", "ANOVA", "Chi-Square Test",
        "Correlation Analysis", "T-Test", "Multivariate Analysis", "Bayesian Inference", "Statistical Inference",
        "Model Assumptions", "Variance Inflation Factor", "Residual Analysis", "Model Comparison", "R-squared"
    ],
    "A/B Testing": [
        "Randomized Experiments", "Control vs Treatment", "Hypothesis Setup", "P-Value Interpretation", "Sample Size Calculation",
        "Confidence Intervals", "Statistical Significance", "Uplift Modeling", "Power Analysis", "False Positives/Negatives",
        "Test Duration", "Bayesian A/B Testing", "Sequential Testing", "Conversion Rate Analysis", "Multivariate Testing"
    ],
    "Experimental Design": [
        "Randomization", "Blocking", "Factorial Design", "Confounding Variables", "Control Groups",
        "Placebo Effects", "Double-Blind Setup", "Independent vs Dependent Variables", "Pre/Post Testing", "Between/Within Subjects",
        "Latin Square Design", "Replication", "Experimental Bias", "Sample Representativeness", "Causal Inference"
    ],
    "Survey Analysis": [
        "Questionnaire Design", "Likert Scale Analysis", "Cross Tabulation", "Descriptive Statistics", "Sampling Methods",
        "Data Weighting", "Survey Bias", "Response Rate", "Missing Survey Data", "Open-ended Analysis",
        "Survey Monkey Tools", "Survey Validation", "Skip Logic", "Online Surveys", "Survey Visualization"
    ],
    "EDA (Exploratory Data Analysis)": [
        "Univariate Analysis", "Bivariate Analysis", "Distribution Checking", "Data Profiling", "Summary Statistics",
        "Correlation Matrix", "Pairplots", "Anomaly Detection", "Outlier Analysis", "Missing Value Analysis",
        "Boxplots", "Violin Plots", "Data Types Overview", "Initial Hypotheses", "EDA Reports"
    ],
    "Data Ethics": [
        "Bias in Data", "Privacy Principles", "GDPR", "Data Ownership", "Consent Management",
        "Ethical Data Collection", "Algorithmic Fairness", "Explainability", "AI Responsibility", "Data Transparency",
        "Security Protocols", "Misuse Prevention", "Audit Trails", "De-identification", "Ethical Datasets"
    ],
    "Business Intelligence": [
        "Dashboards", "KPIs", "OLAP", "Power BI", "Tableau",
        "Self-Service BI", "Data Warehousing", "ETL Pipelines", "BI Reporting", "Drill-down Analysis",
        "Scorecards", "Business KPIs", "Data Integration", "Visualization Tools", "Insights Generation"
    ],
    "Predictive Analytics": [
        "Time Series Models", "Regression Analysis", "Classification Models", "Churn Prediction", "Lead Scoring",
        "Propensity Modeling", "Forecasting", "Predictive Maintenance", "Uplift Modeling", "Survival Analysis",
        "SVMs", "Decision Trees", "Gradient Boosting", "Model Validation", "Feature Importance"
    ],
    "Prescriptive Analytics": [
        "Optimization Models", "Linear Programming", "Simulation", "Decision Trees", "What-if Analysis",
        "Scenario Planning", "Operations Research", "Heuristics", "Constraint Programming", "Resource Allocation",
        "Trade-off Analysis", "Prescriptive Dashboards", "Cost-Benefit Analysis", "Monte Carlo Simulation", "Policy Recommendations"
    ],
    "Geospatial Data": [
        "Geocoding", "Spatial Joins", "Map Visualization", "Coordinate Systems", "Shapefiles",
        "GeoJSON", "Spatial Aggregation", "Proximity Analysis", "Choropleth Maps", "Spatial Clustering",
        "QGIS", "OpenStreetMap", "Leaflet.js", "PostGIS", "Raster Data"
    ],
    "Open Data": [
        "Open Government Data", "Data Portals", "Licensing", "Metadata Standards", "Data Repositories",
        "CSV/JSON/XML Formats", "API Access", "Data Discovery", "Crowdsourced Data", "FAIR Principles",
        "Web Scraping", "Public Datasets", "Civic Tech", "Reusability", "Open Science"
    ],
    "Data Journalism": [
        "Data Storytelling", "Narrative Visualization", "Fact-checking", "Freedom of Information", "Investigative Reporting",
        "Public Records Analysis", "Infographics", "Newsroom Collaboration", "Statistical Claims", "Social Media Data",
        "Jupyter Notebooks", "Mapbox", "Scraping Tools", "Accessible Charts", "Visual Integrity"
    ],
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in ds_skills.items():
    try:
        subcat = SkillsSubCategory.objects.get(name=subcat_name)
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
    except SkillsSubCategory.DoesNotExist:
        missing_subcats.append(subcat_name)
        print(f"❌ Subcategory not found: {subcat_name}")

print("\n🎉 Import Complete!")
print(f"✅ Total created: {created}")
print(f"⚠️ Total skipped: {skipped}")
if missing_subcats:
    print("❌ Missing subcategories:")
    for subcat in missing_subcats:
        print(f" - {subcat}")
