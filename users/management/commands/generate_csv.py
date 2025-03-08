import csv
import random
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Generate CSV files for 100 sample users and 100 sample projects with fully filled fields."

    def handle(self, *args, **options):
        self.generate_users_csv()
        self.generate_projects_csv()
        self.stdout.write(self.style.SUCCESS("CSV files generated successfully."))

    def generate_users_csv(self):
        with open("users_extended.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "email", "bio", "birthdate"])
            for i in range(100):
                username = f"user{i}"
                email = f"user{i}@example.com"
                bio = f"User{i} is a sample user with interests in various fields."
                year = 1990
                month = (i % 12) + 1
                day = ((i % 28) + 1)
                birthdate = f"{year}-{month:02d}-{day:02d}"
                writer.writerow([username, email, bio, birthdate])
        self.stdout.write("users_extended.csv generated.")

    def generate_projects_csv(self):
        """
        Generates a CSV of 100 projects with the following columns:
          title, description, mission, objectives, link, owner,
          categories, required_skills, languages, required_roles, is_active
        """
        # 1. Define arrays for categories, languages, and roles (random picks).
        categories_list = [
            "AI", "Business", "Research", "Healthcare", "Education",
            "Arts & Media", "Social Impact", "Machine Learning", "Software", "Environment"
        ]
        languages_list = [
            "English", "Spanish", "German", "French", "Chinese", "Japanese"
        ]
        roles_list = [
            "ML Engineer", "Backend Developer", "Frontend Developer",
            "Project Manager", "Data Scientist", "Researcher", "Designer"
        ]

        # 2. Define balanced skill groups (as in your original code).
        groups = {
            0: ["Cloud Databases", "Cloud Networking", "Cloud Storage", "Cloud Monitoring", "GCP BigQuery", "Azure Functions", "CloudFormation", "Serverless", "Cloud Architecture", "Google Cloud Platform", "AWS Lambda", "Amazon S3", "Amazon EC2"],
            1: ["BigQuery", "Spark", "Jupyter", "Statistics", "NLP", "Deep Learning", "Machine Learning", "Data Cleaning", "Data Visualization", "SQL", "Seaborn", "Matplotlib", "Keras", "PyTorch", "TensorFlow", "Scikit-learn", "NumPy", "Pandas", "R"],
            2: ["Kotlin Multiplatform", "Jetpack Compose", "SwiftUI", "NativeScript", "PhoneGap", "Corona SDK", "Cocos2d-x", "Unity", "Dart", "Cordova", "Ionic", "Xamarin", "Objective-C", "Swift", "Flutter", "React Native", "iOS", "Android"],
            3: ["Documentation", "Strategic Planning", "Change Management", "Quality Management", "Time Management", "Leadership", "Communication", "Asana", "Trello", "JIRA", "Gantt Charts", "Stakeholder Management", "Resource Allocation", "Budgeting", "Project Planning", "Waterfall", "Kanban", "Scrum", "Agile"],
            4: ["Security Testing", "Continuous Testing", "TDD", "BDD", "Agile Testing", "Acceptance Testing", "System Testing", "Integration Testing", "Unit Testing", "Regression Testing", "Load Testing", "Performance Testing", "API Testing", "Postman", "Cypress", "TestNG", "JUnit", "Selenium", "Automation Testing", "Manual Testing"],
            5: ["Accessibility", "Design Systems", "Persona Creation", "User Flow", "Design Thinking", "Adobe Illustrator", "Adobe Photoshop", "Information Architecture", "Usability", "Responsive Design", "Visual Design", "Interaction Design", "User Testing", "Prototyping", "Wireframing", "User Research", "InVision", "Figma", "Adobe XD", "Sketch"],
            6: ["Reverse Engineering", "Threat Hunting", "Cloud Security", "Security Architecture", "Forensics", "Compliance", "Identity Management", "Endpoint Protection", "SIEM", "Security Auditing", "Risk Management", "Vulnerability Assessment", "Malware Analysis", "Cryptography", "Incident Response", "Intrusion Detection", "Firewalls", "Ethical Hacking", "Penetration Testing", "Network Security"],
            7: ["Apache", "Nginx", "OpenShift", "Chef", "Puppet", "CI/CD", "ELK Stack", "Grafana", "Prometheus", "Google Cloud", "Azure", "AWS", "Terraform", "Ansible", "CircleCI", "Travis CI", "GitLab CI", "Jenkins", "Kubernetes", "Docker"],
            8: ["Elixir Phoenix", "Micronaut", "Kotlin", "Play Framework", "Scala", "Fiber", "Go", ".NET Core", "C#", "ASP.NET", "Laravel", "PHP", "Express.js", "Node.js", "Spring", "Java", "Ruby on Rails", "Flask", "Django", "Python"],
            9: ["Ant Design", "Material UI", "Styled Components", "CSS Modules", "Babel", "Webpack", "Redux", "Nuxt.js", "Next.js", "TypeScript", "jQuery", "Tailwind CSS", "Bootstrap", "Svelte", "Vue.js", "Angular", "React", "JavaScript", "CSS", "HTML"]
        }

        def get_skill_from_group(group_index, project_index):
            """
            For a given group and project index, return a skill name from that group.
            Vary the selection by project index every 10 projects.
            """
            group = groups[group_index]
            return group[(project_index // 10) % len(group)]

        # 3. Create the CSV with all columns:
        #    title, description, mission, objectives, link, owner, categories, required_skills, languages, required_roles, is_active
        with open("research_projects_extended.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "title", "description", "mission", "objectives", "link",
                "owner", "categories", "required_skills", "languages",
                "required_roles", "is_active"
            ])

            for i in range(100):
                title = f"Project{i}"
                description = f"Description for Project{i}. This project covers balanced topics."
                mission = f"Mission for Project{i}: Develop innovative solutions across multiple fields."
                objectives = f"Objectives for Project{i}: Integrate balanced skills and technologies."
                link = f"https://example.com/project{i}"
                owner = f"user{i}"  # Must match users_extended.csv

                # 2 random categories:
                c1 = categories_list[i % len(categories_list)]
                c2 = categories_list[(i+1) % len(categories_list)]
                if c1 == c2:
                    categories_str = c1
                else:
                    categories_str = f"{c1},{c2}"

                # 2 random languages:
                l1 = languages_list[i % len(languages_list)]
                l2 = languages_list[(i+1) % len(languages_list)]
                if l1 == l2:
                    languages_str = l1
                else:
                    languages_str = f"{l1},{l2}"

                # 2 random roles:
                r1 = roles_list[i % len(roles_list)]
                r2 = roles_list[(i+1) % len(roles_list)]
                if r1 == r2:
                    roles_str = r1
                else:
                    roles_str = f"{r1},{r2}"

                # 4 required skills from 4 different skill groups in a cyclic manner:
                g0 = i % 10
                g1 = (i + 1) % 10
                g2 = (i + 2) % 10
                g3 = (i + 3) % 10
                skill0 = get_skill_from_group(g0, i)
                skill1 = get_skill_from_group(g1, i)
                skill2 = get_skill_from_group(g2, i)
                skill3 = get_skill_from_group(g3, i)
                required_skills_str = f"{skill0},{skill1},{skill2},{skill3}"

                is_active = True

                writer.writerow([
                    title,
                    description,
                    mission,
                    objectives,
                    link,
                    owner,
                    categories_str,
                    required_skills_str,
                    languages_str,
                    roles_str,
                    is_active
                ])

        self.stdout.write("research_projects_extended.csv generated.")
