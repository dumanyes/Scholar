from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

cyber_skills = {
    "Network Security": [
        "Firewalls", "Intrusion Detection Systems", "VPNs", "Network Segmentation", "Port Scanning",
        "Packet Sniffing", "Network Protocol Analysis", "IPSec", "TLS/SSL", "Secure Routing Protocols",
        "Wi-Fi Security", "Zero Trust Networking", "MAC Filtering", "DDoS Mitigation", "Network Access Control"
    ],
    "Cryptography": [
        "Symmetric Encryption", "Asymmetric Encryption", "RSA", "AES", "Hash Functions",
        "Digital Signatures", "Public Key Infrastructure", "SSL/TLS Handshake", "Key Exchange Protocols", "Cryptanalysis",
        "Quantum Cryptography", "Block Cipher Modes", "Certificate Authorities", "PGP", "HMAC"
    ],
    "Application Security": [
        "Input Validation", "Authentication Mechanisms", "Authorization Models", "Session Management", "OWASP Top 10",
        "CSRF Protection", "Secure Headers", "Code Review", "Security Patching", "Security Testing Tools",
        "Dependency Management", "Security in SDLC", "Threat Modeling", "Error Handling", "Content Security Policy"
    ],
    "Penetration Testing": [
        "Reconnaissance Techniques", "Vulnerability Scanning", "Exploit Development", "Metasploit Framework", "SQL Injection",
        "XSS Exploits", "Privilege Escalation", "Social Engineering", "Password Cracking", "Reverse Shells",
        "Pivoting Techniques", "Buffer Overflow", "Post-Exploitation", "Wireless Pen Testing", "Reporting Findings"
    ],
    "Security Auditing": [
        "Log Review", "Audit Trails", "Policy Compliance", "System Hardening", "Vulnerability Assessments",
        "Configuration Reviews", "Access Control Audits", "SIEM Tools", "Audit Reports", "Change Management Tracking",
        "File Integrity Monitoring", "Incident History Review", "Audit Automation", "Gap Analysis", "Risk Registers"
    ],
    "Secure Coding": [
        "Input Sanitization", "Use of Prepared Statements", "Avoiding Hardcoded Secrets", "Error Logging Practices", "Memory Safety",
        "Using Security Linters", "Authentication Best Practices", "Handling Exceptions Securely", "Using HTTPS", "Content Injection Prevention",
        "Race Condition Mitigation", "Avoiding Eval Functions", "Static Code Analysis", "Secure Dependencies", "Principle of Least Privilege"
    ],
    "Threat Modeling": [
        "STRIDE Model", "Attack Trees", "DFD Creation", "Asset Identification", "Threat Identification",
        "Risk Assessment", "Security Controls Mapping", "Mitigation Strategies", "Use Case Analysis", "Abuse Case Scenarios",
        "Tooling for Modeling", "Architecture Review", "Threat Prioritization", "Compliance Mapping", "Model Review Process"
    ],
    "Cloud Security": [
        "IAM in Cloud", "Shared Responsibility Model", "Cloud Encryption", "Access Keys Management", "Cloud Compliance",
        "Workload Security", "Cloud Configuration Scanning", "Cloud Firewall Rules", "Cloud Logging & Monitoring", "Data Residency",
        "Public/Private Subnetting", "Security Groups vs NACLs", "Serverless Security", "SaaS Security", "CASB"
    ],
    "Malware Analysis": [
        "Static Analysis", "Dynamic Analysis", "Reverse Engineering", "Disassemblers", "Sandboxing",
        "Memory Forensics", "Malware Classification", "Behavioral Analysis", "Obfuscation Techniques", "Anti-VM Detection",
        "Signature Creation", "Network Indicators", "YARA Rules", "PE File Analysis", "Malware Lifecycle"
    ],
    "Incident Response": [
        "Incident Identification", "Containment Strategies", "Root Cause Analysis", "Forensics Collection", "Eradication Steps",
        "Recovery Planning", "Incident Documentation", "Communication Plans", "Legal Compliance", "Post-Incident Review",
        "Playbook Creation", "Red Team/Blue Team", "Coordination with SOC", "Third-Party Coordination", "Retrospective Meetings"
    ],
    "Security Awareness": [
        "Phishing Simulation", "Password Hygiene", "Social Engineering Awareness", "Safe Browsing", "Device Security",
        "Insider Threats", "Reporting Procedures", "Email Security", "USB Threats", "Mobile Device Policies",
        "Secure Remote Work", "Multi-Factor Authentication", "Physical Security Basics", "Regular Training Programs", "Security News Updates"
    ],
    "Identity & Access Management": [
        "RBAC", "ABAC", "OAuth 2.0", "SAML", "SSO",
        "LDAP Integration", "IAM Policies", "Password Policies", "Access Reviews", "Provisioning & Deprovisioning",
        "Federated Identity", "Zero Trust Identity", "Privileged Access Management", "Directory Services", "Session Expiry Controls"
    ],
    "Data Privacy": [
        "GDPR", "CCPA", "Data Minimization", "User Consent", "PII Handling",
        "Data Classification", "Anonymization", "Data Retention Policies", "Data Breach Response", "Privacy Impact Assessment",
        "Cross-Border Data Transfer", "Right to be Forgotten", "Privacy by Design", "Third-Party Data Sharing", "Cookie Compliance"
    ],
    "SOC Operations": [
        "Security Monitoring", "Alert Triage", "Incident Escalation", "Threat Hunting", "Log Correlation",
        "Ticketing Systems", "Shift Handover", "SIEM Usage", "Runbooks", "Communication Protocols",
        "Intel Gathering", "Breach Detection", "Escalation Matrix", "Behavioral Analysis", "SOC Maturity Models"
    ],
    "Vulnerability Management": [
        "Vulnerability Scanning", "Patch Management", "Risk Prioritization", "Exploitability Scoring", "Remediation Planning",
        "Threat Intelligence Integration", "Vulnerability Databases", "Change Management Coordination", "Reporting & Metrics", "Scanning Schedules",
        "Vendor Communication", "CVSS Scoring", "Automated Patch Deployment", "Historical Trend Analysis", "Vulnerability Disclosure Process"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in cyber_skills.items():
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

