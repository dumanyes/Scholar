from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

uiux_skills = {
    "Design Thinking": [
        "Empathize Phase", "Define Phase", "Ideate Techniques", "Prototyping", "User-Centered Design",
        "Iterative Design", "Design Sprints", "Stakeholder Interviews", "Problem Framing", "Journey Mapping",
        "Value Proposition Design", "Scenario Building", "Design Critique", "Design Synthesis", "Innovation Workshops"
    ],
    "User Research": [
        "Surveys", "Interviews", "User Personas", "Field Studies", "Diary Studies",
        "Card Sorting", "Usability Testing", "Focus Groups", "User Journey Mapping", "Heuristic Evaluation",
        "A/B Testing", "Ethnographic Research", "Eye Tracking", "Clickstream Analysis", "Behavioral Analytics"
    ],
    "Wireframing": [
        "Low-Fidelity Wireframes", "Sketching", "Balsamiq", "Axure", "Wireframe Components",
        "Interaction Flow", "Layout Design", "Content Placement", "Information Hierarchy", "Grids and Spacing",
        "Wireframe Annotations", "Responsive Wireframes", "Clickable Wireframes", "Wireframing Templates", "Rapid Prototyping"
    ],
    "Prototyping": [
        "Interactive Prototypes", "InVision", "Figma Prototyping", "User Flow Simulation", "Clickable Prototypes",
        "Rapid Prototyping", "Low/High Fidelity", "Feedback Loops", "A/B Prototype Testing", "Prototype Validation",
        "Paper Prototypes", "Interactive Mockups", "Behavior Design", "Microinteractions", "Design Iterations"
    ],
    "Interaction Design": [
        "Affordances", "Feedback Loops", "Usability Principles", "State Changes", "Animation Timing",
        "Touch Targets", "Navigation Patterns", "Interactive Patterns", "Fitts’s Law", "Design for Emotion",
        "Accessibility in Interaction", "Microinteractions", "Gesture-Based Interfaces", "Haptic Feedback", "Transition Design"
    ],
    "Visual Design": [
        "Layout Design", "Typography", "Grid Systems", "Whitespace", "Visual Hierarchy",
        "Color Theory", "Contrast & Balance", "Design Aesthetics", "Iconography", "Mood Boards",
        "Design Patterns", "Responsive Design", "Consistency in Design", "Design Tokens", "Visual Identity"
    ],
    "Design Systems": [
        "Component Libraries", "Design Tokens", "Figma Libraries", "Style Guides", "UI Kits",
        "Atomic Design", "Pattern Libraries", "Design Governance", "Brand Consistency", "Documentation Standards",
        "Cross-platform Design", "System Versioning", "Accessibility Standards", "Reusable Components", "Design System Adoption"
    ],
    "Accessibility Design": [
        "WCAG Guidelines", "Screen Reader Testing", "Color Contrast", "Keyboard Navigation", "Alt Text Usage",
        "ARIA Roles", "Accessible Forms", "Tab Indexing", "Semantic HTML", "Captions & Transcripts",
        "Focus Indicators", "Skip Links", "Inclusive Design", "Mobile Accessibility", "Testing Tools (e.g., Axe)"
    ],
    "Figma": [
        "Auto Layout", "Components & Variants", "Prototyping", "Design Tokens", "Collaborative Design",
        "Version History", "Interactive Components", "Design Systems in Figma", "Figma Plugins", "Team Libraries",
        "Constraints & Resizing", "Figma for Dev Handoff", "Smart Animate", "Comments & Feedback", "Figma Shortcuts"
    ],
    "Adobe XD": [
        "Artboards", "Prototyping Tools", "Auto-Animate", "Repeat Grid", "Voice Prototyping",
        "Design Specs", "Sharing & Collaboration", "Components", "Stacks & Padding", "Plugin Usage",
        "Responsive Resize", "Linked Assets", "Adobe Fonts", "User Testing", "Microinteractions"
    ],
    "Photoshop": [
        "Layers & Masks", "Photo Retouching", "Typography Tools", "Color Adjustments", "Smart Objects",
        "Image Exporting", "Brush Tools", "Filters & Effects", "Compositing", "Adjustment Layers",
        "Selections & Paths", "Content-Aware Tools", "3D Tools", "Layer Styles", "Photo Manipulation"
    ],
    "Illustrator": [
        "Vector Drawing", "Pen Tool Mastery", "Typography Design", "Shape Builder Tool", "Pathfinder Operations",
        "Gradient & Mesh Tools", "Logo Design", "Illustration Techniques", "Artboards", "Color Palettes",
        "Custom Brushes", "Symbols", "Image Trace", "Pattern Design", "Exporting Assets"
    ],
    "Usability Testing": [
        "Moderated Testing", "Unmoderated Testing", "Task-Based Testing", "Screen Recording Tools", "User Feedback Collection",
        "Remote Testing", "Session Replay", "Think Aloud Protocol", "First Click Testing", "Surveys & Polls",
        "A/B Testing", "Success Metrics", "Heatmaps", "Bug Reporting", "Report Synthesis"
    ],
    "Color Theory": [
        "Color Wheel", "Complementary Colors", "Analogous Colors", "Triadic Schemes", "Contrast & Harmony",
        "Color Psychology", "Accessibility & Color", "Branding & Color", "Neutral Colors", "Monochromatic Schemes",
        "Hue, Saturation, Brightness", "Color Consistency", "Color Tools", "Gradients", "Color Palettes"
    ],
    "Animation Design": [
        "Principles of Animation", "Ease-in/Ease-out", "Motion Curves", "Microinteractions", "Lottie Files",
        "After Effects Integration", "Frame-by-frame Animation", "UI Transitions", "Loading Animations", "Timing & Spacing",
        "State Animations", "Scroll Animations", "SVG Animations", "Prototyping Animations", "Interactive Motion Design"
    ]
}


created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in uiux_skills.items():
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
