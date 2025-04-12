from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

research_skills = {
    "Literature Review": [
        "Systematic Review", "Scoping Review", "Narrative Review", "Meta-Analysis", "Thematic Analysis",
        "Search Strategies", "Reference Management", "Critical Appraisal", "Citation Tracking", "PRISMA Guidelines",
        "Grey Literature", "Inclusion Criteria", "Exclusion Criteria", "Review Protocols", "Research Databases"
    ],
    "Research Methodology": [
        "Qualitative Methods", "Quantitative Methods", "Mixed Methods", "Experimental Design", "Case Study Research",
        "Grounded Theory", "Phenomenology", "Action Research", "Sampling Techniques", "Longitudinal Studies",
        "Cross-sectional Studies", "Control Groups", "Randomized Trials", "Ethnographic Methods", "Survey Methods"
    ],
    "Scientific Writing": [
        "Abstract Writing", "Introduction Crafting", "Results Presentation", "Discussion Writing", "Scientific Style",
        "Technical Clarity", "Structure & Flow", "Audience Awareness", "Revising Drafts", "Editing Techniques",
        "Common Pitfalls", "Writing Concisely", "Passive vs Active Voice", "Writing for Journals", "Publication Standards"
    ],
    "LaTeX": [
        "Document Structure", "Math Equations", "Figures and Tables", "Bibliographies", "Packages and Classes",
        "Overleaf Usage", "Formatting Styles", "Citations with BibTeX", "Cross-referencing", "Beamer Presentations",
        "Custom Commands", "TikZ Diagrams", "Table of Contents", "Hyperlinks", "Template Management"
    ],
    "Citation Management": [
        "EndNote", "Zotero", "Mendeley", "BibTeX", "Reference Styles", "Citation Formats", "Importing References",
        "Organizing Sources", "In-text Citations", "Reference Lists", "Citation Networks", "Linking PDFs",
        "Annotations", "Syncing Across Devices", "Collaboration Tools"
    ],
    "Academic Publishing": [
        "Journal Selection", "Submission Guidelines", "Impact Factor", "Peer Review Process", "Open Access Options",
        "Predatory Journals", "Manuscript Formatting", "Plagiarism Checking", "Publication Ethics", "Rejection Handling",
        "Cover Letters", "Reviewer Comments", "Editorial Process", "Preprints", "ORCID ID"
    ],
    "Research Ethics": [
        "Informed Consent", "Ethics Approval", "Confidentiality", "Data Integrity", "Authorship Ethics",
        "Conflict of Interest", "Ethical Guidelines", "Plagiarism Avoidance", "Research Misconduct", "Animal Research",
        "Human Subject Protection", "Ethics Committees", "Data Fabrication", "Ethical Review Boards", "Research Transparency"
    ],
    "Thesis Writing": [
        "Problem Statement", "Literature Survey", "Methodology Chapter", "Results and Analysis", "Conclusion Chapter",
        "Formatting Standards", "Thesis Defense Preparation", "Supervisor Feedback", "Proposal Development",
        "Editing and Proofreading", "Plagiarism Checking", "Appendices", "Thesis Timeline Planning", "Citation Styles",
        "Binding and Submission"
    ],
    "Survey Design": [
        "Questionnaire Design", "Likert Scales", "Survey Tools (Google Forms, Qualtrics)", "Sampling Strategies",
        "Pretesting", "Pilot Studies", "Survey Logic", "Demographic Questions", "Data Cleaning", "Survey Bias",
        "Online vs Offline Surveys", "Ethical Considerations", "Response Rates", "Anonymity in Surveys", "Incentive Strategies"
    ],
    "Statistical Reporting": [
        "P-Values", "Confidence Intervals", "Effect Sizes", "Descriptive Stats", "Inferential Stats",
        "Graphs and Charts", "APA Format", "Table Design", "Hypothesis Testing", "Chi-Square Tests",
        "T-Tests", "ANOVA", "Regression Results", "Data Summary", "Reporting Standards"
    ],
    "Peer Review Process": [
        "Reviewer Responsibilities", "Manuscript Evaluation", "Constructive Feedback", "Confidentiality",
        "Double-Blind Review", "Editorial Board Roles", "Review Timelines", "Acceptance Criteria",
        "Ethical Reviewing", "Response to Reviewers", "Reviewer Guidelines", "Manuscript Scoring",
        "Post-Review Revisions", "Reviewer Recognition", "Editorial Recommendations"
    ],
    "Open Access Publishing": [
        "Gold Open Access", "Green Open Access", "Hybrid Journals", "Creative Commons Licenses", "APC Fees",
        "Institutional Repositories", "Open Data Mandates", "Plan S", "Preprint Servers", "Access Equity",
        "Copyright Retention", "Author Rights", "Funding Acknowledgment", "Visibility Enhancement", "Repository Submission"
    ],
    "Qualitative Analysis": [
        "Thematic Coding", "Content Analysis", "Grounded Theory", "NVivo", "Interview Transcription",
        "Focus Groups", "Open Coding", "Axial Coding", "Narrative Analysis", "Case Study Analysis",
        "Data Saturation", "Memo Writing", "Reflexivity", "Qualitative Sampling", "Pattern Matching"
    ],
    "Quantitative Analysis": [
        "Descriptive Statistics", "Inferential Statistics", "Hypothesis Testing", "SPSS", "R Programming",
        "Regression Analysis", "T-tests & ANOVA", "Multivariate Analysis", "Data Visualization",
        "Data Normalization", "Outlier Detection", "Chi-Square Testing", "Correlation", "Confidence Intervals",
        "Sampling Techniques"
    ],
    "Research Proposals": [
        "Research Objectives", "Background Context", "Research Gap", "Methodology Plan", "Expected Outcomes",
        "Timeline and Milestones", "Budgeting", "Feasibility", "Proposal Formatting", "Grant Applications",
        "Ethical Considerations", "Proposal Review", "Research Questions", "Impact Assessment", "Literature Citations"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in research_skills.items():
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
