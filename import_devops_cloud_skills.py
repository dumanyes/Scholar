from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

devops_skills = {
    "Docker": [
        "Dockerfile Creation", "Docker Compose", "Image Layers", "Container Networking", "Volumes",
        "Environment Variables", "Docker Registry", "Docker Swarm", "Multi-Stage Builds", "Private Registries",
        "Container Lifecycle", "Security Best Practices", "Alpine Images", "Docker Inspect", "Optimizing Images"
    ],
    "Kubernetes": [
        "Pods", "Deployments", "Services", "ConfigMaps", "Secrets",
        "Namespaces", "Helm Charts", "Kubeconfig", "Rolling Updates", "Horizontal Pod Autoscaling",
        "Node Affinity", "Taints & Tolerations", "Persistent Volumes", "Ingress Controllers", "Kubernetes Dashboard"
    ],
    "AWS": [
        "EC2", "S3", "IAM", "RDS", "CloudWatch",
        "VPC", "Lambda", "Elastic Beanstalk", "Auto Scaling", "Load Balancer",
        "Route 53", "CloudFormation", "ECS", "EKS", "Cost Management"
    ],
    "Azure": [
        "Azure VM", "Blob Storage", "Azure Functions", "Resource Groups", "Azure CLI",
        "App Services", "Azure DevOps", "ARM Templates", "Virtual Network", "Cosmos DB",
        "Azure Active Directory", "Monitoring Tools", "AKS", "Load Testing", "Role-Based Access Control (RBAC)"
    ],
    "GCP": [
        "Compute Engine", "Cloud Storage", "Cloud Functions", "BigQuery", "Cloud Run",
        "App Engine", "GKE", "Pub/Sub", "IAM Policies", "Stackdriver",
        "Cloud Shell", "VPC", "Cloud SQL", "Billing", "Resource Manager"
    ],
    "CI/CD Pipelines": [
        "Build Scripts", "Testing Pipelines", "Deployment Automation", "Artifact Storage", "Pipeline Stages",
        "Environment Variables", "Secrets Management", "Notifications", "Pipeline Templates", "Manual Approvals",
        "Rollback Strategies", "Parallel Builds", "Pipeline as Code", "Performance Optimization", "Scheduled Pipelines"
    ],
    "Infrastructure as Code": [
        "Terraform", "Ansible", "Pulumi", "CloudFormation", "Infrastructure Modules",
        "Variables & Outputs", "Provisioning Resources", "State Management", "IaC Security", "Reusable Templates",
        "Version Control Integration", "Testing IaC", "Idempotency", "DRY Principles in IaC", "Secret Injection"
    ],
    "Monitoring & Logging": [
        "Prometheus", "Grafana", "Log Aggregation", "Metric Collection", "Alerting Systems",
        "ELK Stack", "Fluentd", "Tracing (Jaeger, Zipkin)", "Log Retention Policies", "Custom Dashboards",
        "Anomaly Detection", "Real-time Monitoring", "Uptime Checks", "System Health Metrics", "Logging Best Practices"
    ],
    "Jenkins": [
        "Jenkinsfile", "Pipeline as Code", "Job DSL", "Freestyle Jobs", "Credential Management",
        "Build Triggers", "Jenkins Plugins", "Parallel Builds", "Distributed Builds", "Post-Build Actions",
        "Jenkins Agents", "Security Configuration", "Log Analysis", "Declarative vs Scripted", "CI Integration"
    ],
    "GitHub Actions": [
        "Workflow Syntax", "Jobs & Steps", "Actions Marketplace", "Secrets Management", "Matrix Builds",
        "Event Triggers", "Caching Dependencies", "Reusable Workflows", "Artifacts Upload", "Environment Files",
        "Self-Hosted Runners", "CI/CD with Actions", "Status Checks", "Branch Filters", "Testing Automation"
    ],
    "Serverless Architecture": [
        "Function as a Service (FaaS)", "Cold Start Optimization", "API Gateway Integration", "Event Triggers", "Scalability",
        "Timeout Handling", "Serverless Frameworks", "Billing Models", "Logging & Monitoring", "Security Considerations",
        "State Management", "Orchestration (Step Functions)", "Error Handling", "Use Cases", "Resource Limits"
    ],
    "Load Balancing": [
        "Round Robin", "Least Connections", "IP Hash", "Health Checks", "Failover",
        "Application Load Balancer", "Network Load Balancer", "Reverse Proxy", "Load Testing Tools", "Geo Load Balancing",
        "Session Persistence", "SSL Termination", "Weighted Distribution", "DNS-Based Load Balancing", "Global Accelerator"
    ],
    "Cloud Security": [
        "Identity & Access Management", "Encryption at Rest", "Encryption in Transit", "Key Management Services", "Security Groups",
        "Network ACLs", "Data Loss Prevention", "Threat Detection", "Cloud Compliance", "Shared Responsibility Model",
        "Firewall Configuration", "Security Audits", "Secrets Management", "Multi-Factor Authentication", "Logging Access"
    ],
    "DevSecOps": [
        "Shift Left Security", "Security Scanning", "SAST", "DAST", "Secrets Detection",
        "Compliance as Code", "Security Gates", "Policy Enforcement", "SBOM", "Container Scanning",
        "Dependency Scanning", "Security Plugins", "CI/CD Security", "Access Monitoring", "Secure Coding Practices"
    ],
    "Cloud Databases": [
        "Amazon RDS", "Cloud SQL", "Cosmos DB", "Firestore", "DynamoDB",
        "Bigtable", "Aurora", "High Availability", "Backup & Restore", "Scaling Databases",
        "Read Replicas", "Write Throughput", "Latency Optimization", "Database Monitoring", "Serverless DBs"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in devops_skills.items():
    try:
        subcat = SkillsSubCategory.objects.filter(name=subcat_name).first()
        if not subcat:
            raise SkillsSubCategory.DoesNotExist

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
