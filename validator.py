import json
from core.client import get_local_client
from rules.s3_rules import audit_s3_encryption, audit_s3_public_access
from rules.ec2_rules import audit_security_groups
from rules.iam_rules import audit_iam_roles

AUTHOR = "JACKAL"

if __name__ == "__main__":
    print(f"[{AUTHOR}] Initializing Modular FinTech Compliance Validator...\n")
    
    # 1. Initialize Clients
    s3 = get_local_client('s3')
    ec2 = get_local_client('ec2')
    iam = get_local_client('iam')
    
    # 2. Execute Audits
    full_report = []
    full_report.extend(audit_s3_encryption(s3))
    full_report.extend(audit_s3_public_access(s3))
    full_report.extend(audit_security_groups(ec2))
    full_report.extend(audit_iam_roles(iam))
    
    # 3. Export Artifact
    report_file = "compliance_report.json"
    with open(report_file, "w") as f:
        json.dump(full_report, f, indent=4)
        
    print(f"\n[{AUTHOR}] Audit complete. Full results saved to {report_file}")
    
    # 4. Pipeline Enforcement
    failed_checks = [check for check in full_report if not check.get('compliant')]
    if failed_checks:
        print(f"[WARNING] {len(failed_checks)} compliance violations detected! Halting deployment.")
        exit(1)
    else:
        print("[SUCCESS] Infrastructure is 100% compliant. Proceeding with deployment.")
        exit(0)