from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

software_skills = {
    "Object-Oriented Programming": [
        "Classes & Objects", "Encapsulation", "Inheritance", "Polymorphism", "Abstraction",
        "SOLID Principles", "Design Patterns", "Method Overriding", "Composition vs Inheritance",
        "Constructors & Destructors", "Access Modifiers", "UML Diagrams", "Interfaces", "Mixins", "Static Members"
    ],
    "Functional Programming": [
        "Pure Functions", "Immutability", "Higher-Order Functions", "Lambda Expressions", "Recursion",
        "First-Class Functions", "Map/Filter/Reduce", "Currying", "Closures", "Pattern Matching",
        "Lazy Evaluation", "Monads", "Functional Composition", "State Management", "Tail Recursion"
    ],
    "APIs": [
        "RESTful APIs", "GraphQL", "API Authentication", "Rate Limiting", "API Versioning",
        "Swagger/OpenAPI", "Postman Usage", "API Error Handling", "Webhooks", "Token-Based Auth",
        "Request/Response Cycle", "CORS", "OAuth 2.0", "gRPC", "JSON & XML Handling"
    ],
    "Mobile App Development": [
        "Flutter", "React Native", "Android SDK", "iOS Development", "Cross-Platform Tools",
        "App Lifecycle", "State Management (Bloc/Provider)", "Push Notifications", "SQLite/Mobile DBs",
        "Responsive Layouts", "Camera/GPS Integration", "App Store Deployment", "Testing Mobile Apps",
        "Offline Mode", "Firebase Integration"
    ],
    "Desktop Applications": [
        "Electron.js", "Tkinter", "PyQt", "WPF", "JavaFX",
        "Multithreading", "File Dialogs", "Form Validation", "Installer Creation", "System Tray Apps",
        "Native Look & Feel", "MVC Pattern", "Drag & Drop UI", "SQLite Integration", "Packaging Executables"
    ],
    "Game Development": [
        "Unity Engine", "Unreal Engine", "2D/3D Rendering", "Game Physics", "Game Loops",
        "Animation Systems", "Audio Integration", "Scene Management", "Character Controllers",
        "Game Scripting (C#, Lua)", "Asset Management", "Input Handling", "AI for Games",
        "Multiplayer Setup", "Game Deployment"
    ],
    "Unit Testing": [
        "Test Cases", "Test Fixtures", "Assertions", "Mocking", "Test Coverage",
        "Test-Driven Development", "Unittest (Python)", "Jest", "Mocha", "Pytest",
        "Integration Tests", "Behavior-Driven Development", "Test Suites", "CI Integration", "Code Quality"
    ],
    "Version Control (Git)": [
        "Git Basics", "Branching", "Merging", "Rebasing", "Pull Requests",
        "Conflict Resolution", "Tagging Releases", "Stashing Changes", "Git Hooks", "Cherry Picking",
        "Forking", "Git Workflows", "Submodules", "Commit Best Practices", "Git CLI Tools"
    ],
    "Debugging Techniques": [
        "Breakpoints", "Stack Traces", "Logging", "Print Debugging", "Watch Expressions",
        "Debugger Tools (PDB, Chrome DevTools)", "Memory Leak Detection", "Error Handling", "Code Linting",
        "Step Over/Into", "Try/Catch Blocks", "Debugging APIs", "Performance Profiling", "Thread Debugging",
        "Crash Reports"
    ],
    "CI/CD": [
        "Continuous Integration", "Continuous Delivery", "Pipeline Configuration", "GitHub Actions", "Jenkins",
        "Build Automation", "Artifact Management", "Testing Automation", "Deployment Scripts", "Rollback Strategies",
        "Docker in CI/CD", "Monitoring & Alerts", "Blue-Green Deployment", "YAML Pipelines", "Release Management"
    ],
    "Agile Development": [
        "Scrum", "Kanban", "User Stories", "Backlog Grooming", "Sprint Planning",
        "Daily Standups", "Burndown Charts", "Retrospectives", "Agile Artifacts", "Story Points",
        "Agile Estimation", "Velocity Tracking", "Product Owner Role", "Agile Tools (Jira, Trello)", "Continuous Feedback"
    ],
    "Software Architecture": [
        "Monolithic Architecture", "Microservices", "Service-Oriented Architecture", "MVC", "MVVM",
        "Layered Architecture", "Event-Driven Design", "Domain-Driven Design", "Clean Architecture",
        "Hexagonal Architecture", "Serverless", "Scalability Patterns", "Load Balancing", "Dependency Injection",
        "Architecture Diagrams"
    ],
    "Backend Development": [
        "RESTful APIs", "Authentication & Authorization", "Database Management", "ORMs", "Caching Mechanisms",
        "Web Frameworks (Django, Express)", "Middleware", "Error Handling", "Job Scheduling", "Session Management",
        "Logging & Monitoring", "Rate Limiting", "File Upload Handling", "API Throttling", "Security Best Practices"
    ],
    "Frontend Development": [
        "HTML/CSS", "JavaScript", "React.js", "Vue.js", "State Management (Redux/Vuex)",
        "Component-Based Design", "CSS Frameworks (Tailwind, Bootstrap)", "Form Handling", "DOM Manipulation",
        "Single Page Applications", "Responsive Design", "Browser Dev Tools", "Routing", "SSR/CSR", "Animation Libraries"
    ],
    "Clean Code Principles": [
        "Meaningful Naming", "DRY (Don't Repeat Yourself)", "KISS Principle", "YAGNI", "Refactoring",
        "Code Readability", "Code Reviews", "Single Responsibility Principle", "Commenting Best Practices",
        "Consistent Formatting", "Linting", "Code Smells", "Function Decomposition", "Testing as Documentation",
        "Maintainable Code"
    ],
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in software_skills.items():
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

