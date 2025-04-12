from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

communication_skills = {
    "Public Speaking": [
        "Speech Preparation", "Storytelling", "Audience Engagement", "Body Language", "Stage Presence",
        "Voice Modulation", "Speech Writing", "Handling Q&A", "Presentation Software", "Practice Techniques",
        "Persuasive Speaking", "Visual Aids", "Overcoming Nervousness", "Impromptu Speaking", "Feedback Reception"
    ],
    "Technical Communication": [
        "Technical Writing", "User Manuals", "API Documentation", "Requirements Documentation", "Use Case Writing",
        "Release Notes", "White Papers", "Product Specs", "Version Control with Docs", "Markdown",
        "Diagrams & Charts", "Simplifying Complex Info", "Audience Analysis", "Information Architecture", "Document Templates"
    ],
    "Teamwork": [
        "Team Building", "Delegation", "Collaboration Tools", "Peer Feedback", "Conflict Resolution",
        "Shared Accountability", "Team Roles", "Trust Building", "Effective Meetings", "Goal Alignment",
        "Mentorship", "Cooperation Strategies", "Workload Balancing", "Constructive Criticism", "Collective Problem Solving"
    ],
    "Remote Collaboration Tools": [
        "Slack", "Zoom", "Microsoft Teams", "Notion", "Trello",
        "Asana", "Miro", "Google Workspace", "Shared Calendars", "Virtual Whiteboarding",
        "Screen Sharing", "Video Conferencing Etiquette", "Task Assignment", "Remote Onboarding", "Time Zone Coordination"
    ],
    "Conflict Resolution": [
        "Active Listening", "De-escalation Techniques", "Mediation", "Empathy in Dialogue", "Root Cause Analysis",
        "Nonviolent Communication", "Neutral Language", "Conflict Styles", "Resolution Frameworks", "Collaborative Problem Solving",
        "Negotiation Skills", "Emotional Regulation", "Consensus Building", "Feedback Delivery", "Escalation Paths"
    ],
    "Presentation Design": [
        "Slide Design", "Visual Storytelling", "Minimalist Design", "Typography", "Color Theory",
        "Image Sourcing", "Data Visualization", "Slide Transitions", "Infographics", "Presentation Templates",
        "Consistency in Design", "Audience Analysis", "Message Framing", "Accessible Design", "Software Tools (e.g. PowerPoint, Keynote)"
    ],
    "Documentation Writing": [
        "User Guides", "Process Documentation", "SOPs", "Knowledge Base Articles", "Internal Wikis",
        "Release Documentation", "FAQ Writing", "Versioning Docs", "Writing for Global Teams", "Instruction Clarity",
        "Style Guides", "Template Usage", "Searchable Content", "Diagram Integration", "Policy Documentation"
    ],
    "Stakeholder Communication": [
        "Status Updates", "Executive Summaries", "Email Briefings", "Meeting Notes", "Roadmap Presentations",
        "Expectation Setting", "Communication Plans", "Escalation Management", "Active Engagement", "Feedback Loops",
        "Stakeholder Mapping", "Risk Communication", "Reporting Progress", "Clarifying Needs", "Cross-Functional Coordination"
    ],
    "Meeting Facilitation": [
        "Agenda Creation", "Time Management", "Role Assignment", "Note Taking", "Action Item Tracking",
        "Inclusive Participation", "Facilitation Techniques", "Conflict Handling", "Follow-Up Communication", "Meeting Tools",
        "Remote Facilitation", "Brainstorming Sessions", "Decision Making", "Retrospectives", "Meeting Cadence"
    ],
    "Listening Skills": [
        "Active Listening", "Paraphrasing", "Clarifying Questions", "Nonverbal Feedback", "Empathetic Listening",
        "Distraction Management", "Listening without Interrupting", "Demonstrating Understanding", "Listening in Conflict",
        "Feedback via Listening", "Note Taking", "Retention Techniques", "Open-Mindedness", "Responsive Listening", "Observation Skills"
    ],
    "Negotiation": [
        "BATNA", "Interest-Based Bargaining", "Win-Win Solutions", "Concessions Management", "Tactics & Strategy",
        "Preparation Techniques", "Listening in Negotiation", "Closing Deals", "Conflict to Agreement", "Power Dynamics",
        "Cultural Sensitivity", "Value Creation", "Anchoring", "ZOPA", "Framing Offers"
    ],
    "Cross-cultural Communication": [
        "Cultural Awareness", "Language Barriers", "Etiquette", "High/Low Context Cultures", "Nonverbal Cues",
        "Time Perception", "Respect Norms", "Global Team Communication", "Translation Tools", "Accent Adaptation",
        "Cultural Intelligence", "Diversity & Inclusion", "Cultural Sensitivity Training", "Cross-cultural Feedback", "Building Trust"
    ],
    "Writing for Web": [
        "Concise Writing", "SEO Writing", "Headlines & CTAs", "Web Readability", "Content Strategy",
        "Tone of Voice", "Hyperlinking", "Writing for Mobile", "Blog Writing", "Product Descriptions",
        "Microcopy", "Metadata Writing", "Content Structuring", "Accessible Language", "Audience Engagement"
    ],
    "Community Building": [
        "Online Community Management", "Event Planning", "Moderation Guidelines", "Community Engagement", "Content Planning",
        "Value Creation", "Brand Voice", "Welcome Strategies", "Feedback Channels", "Cross-Promotion",
        "Recognition Programs", "Community Metrics", "Conflict Mediation", "Member Onboarding", "Ambassador Programs"
    ],
    "Feedback Techniques": [
        "Constructive Criticism", "Positive Reinforcement", "Feedback Sandwich", "Timing Feedback", "Clarity in Feedback",
        "Receiving Feedback", "Asking for Feedback", "Written vs Verbal", "Safe Environments", "Continuous Feedback",
        "Behavioral Focus", "Feedback Tools", "Feedback Frequency", "Coaching through Feedback", "Bias Awareness"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in communication_skills.items():
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
