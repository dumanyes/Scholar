from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

web_skills = {
    "HTML/CSS": [
        "HTML5 Semantics", "Forms & Inputs", "CSS Flexbox", "CSS Grid", "Responsive Units",
        "Media Queries", "Box Model", "Positioning", "Typography Styling", "Accessibility Tags",
        "HTML Tables", "Transitions & Animations", "Pseudo-classes", "Variables in CSS", "Z-index Usage"
    ],
    "JavaScript": [
        "DOM Manipulation", "ES6+ Syntax", "Arrow Functions", "Async/Await", "Event Handling",
        "Array Methods", "Promises", "JavaScript Modules", "Object Destructuring", "Fetch API",
        "Closures", "Scope & Hoisting", "Error Handling", "LocalStorage/SessionStorage", "Form Validation"
    ],
    "React.js": [
        "JSX", "Components", "Props & State", "Hooks (useState, useEffect)", "React Router",
        "Context API", "Forms in React", "React Query", "useReducer", "React Lifecycle",
        "Custom Hooks", "Performance Optimization", "React Testing Library", "Server-Side Rendering (Next.js)", "Component Memoization"
    ],
    "Vue.js": [
        "Vue CLI", "Components", "Vue Directives", "Vue Router", "Vuex State Management",
        "Composition API", "Vue Lifecycle Hooks", "Single File Components", "v-model Binding", "Event Handling",
        "Watchers & Computed", "Slots", "Transitions & Animations", "Vue Testing", "Vue 3 Features"
    ],
    "Django": [
        "Models & ORM", "Admin Interface", "Class-Based Views", "Forms", "Templates",
        "Authentication", "Middleware", "URL Routing", "File Uploads", "Django REST Framework",
        "Permissions & Roles", "Signals", "Static & Media Files", "Management Commands", "Testing Django Apps"
    ],
    "Flask": [
        "Routing", "Jinja2 Templating", "Flask Blueprints", "Flask-WTF Forms", "Flask-SQLAlchemy",
        "Authentication", "Flask RESTful", "Error Handling", "Session Management", "File Uploads",
        "Middleware", "Flask-Login", "Flask-Migrate", "Deploying Flask", "Flask CLI"
    ],
    "REST APIs": [
        "GET/POST/PUT/DELETE Methods", "Status Codes", "Request/Response Cycle", "Authentication Tokens", "Pagination",
        "Filtering & Sorting", "CRUD Operations", "Error Handling", "Rate Limiting", "Versioning APIs",
        "OpenAPI/Swagger Docs", "Nested Resources", "RESTful Principles", "Caching", "Idempotency"
    ],
    "WebSockets": [
        "Socket.IO", "Real-Time Messaging", "Bidirectional Communication", "WebSocket Handshake", "Event-Based Messaging",
        "Broadcasting Events", "WebSocket Security", "Scalability with Redis", "Handling Disconnections", "Presence Detection",
        "Rooms & Namespaces", "Binary Data Transfer", "Live Dashboards", "Multiplayer Game Events", "WebRTC Intro"
    ],
    "Web Accessibility (a11y)": [
        "ARIA Roles", "Keyboard Navigation", "Screen Readers", "Color Contrast", "Skip Links",
        "Semantic HTML", "Alt Text", "Focus Management", "Accessible Forms", "WCAG Guidelines",
        "Tab Indexing", "Landmark Elements", "Label Association", "Error Messaging", "Responsive Accessibility"
    ],
    "Responsive Design": [
        "Mobile-First Design", "Media Queries", "Flexible Layouts", "Viewport Meta Tag", "Grid/Flex Techniques",
        "Fluid Typography", "Responsive Images", "Breakpoint Strategies", "Hide/Show Elements", "Viewport Units",
        "Responsive Navigation", "Touch Targets", "Orientation Handling", "Column Wrapping", "Device Preview Testing"
    ],
    "Web Performance Optimization": [
        "Lazy Loading", "Code Splitting", "Image Compression", "Minification", "Critical CSS",
        "Caching Strategies", "HTTP/2", "Async Scripts", "CDN Usage", "DNS Prefetching",
        "Font Loading Strategies", "Resource Prioritization", "Performance Budgets", "Web Vitals", "Profiling Tools"
    ],
    "GraphQL": [
        "Schema Definition", "Resolvers", "Mutations", "Queries", "Apollo Client",
        "Nested Queries", "Fragments", "Variables", "Subscriptions", "Error Handling",
        "Pagination", "Authentication", "GraphQL Playground", "Caching with GraphQL", "Schema Stitching"
    ],
    "Tailwind CSS": [
        "Utility Classes", "Custom Themes", "Responsive Design", "Typography Plugin", "Dark Mode",
        "PurgeCSS", "Component Styling", "Hover/Focus States", "Flex/Grid with Tailwind", "Button Designs",
        "Tailwind Forms", "Tailwind with React", "Animations", "Color Palette", "Tailwind CLI"
    ],
    "CMS Platforms": [
        "WordPress Basics", "Custom Themes", "Plugins Development", "Content Blocks", "Gutenberg Editor",
        "Drupal CMS", "Joomla", "Headless CMS", "Strapi", "Sanity.io",
        "Content Modeling", "Authentication with CMS", "CMS Security", "API Access", "Deployment & Hosting"
    ],
    "SEO Basics": [
        "Meta Tags", "Title Tags", "Sitemap.xml", "Robots.txt", "Page Speed Optimization",
        "Canonical URLs", "Alt Text for SEO", "Schema Markup", "Mobile SEO", "Indexing Control",
        "Keyword Research", "Internal Linking", "SEO Audits", "Backlink Strategy", "Search Console"
    ],
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in web_skills.items():
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
