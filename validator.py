import json
import boto3 
import datetime 
from core.client import get_local_client
from rules.s3_rules import audit_s3_encryption, audit_s3_public_access
from rules.ec2_rules import audit_security_groups
from rules.iam_rules import audit_iam_roles

AUTHOR = "JACKAL"

# Configure LocalStack SQS Client with explicit dummy credentials
sqs = boto3.client('sqs', 
                   endpoint_url='http://localhost:4566', 
                   region_name='us-east-1',
                   aws_access_key_id='test',
                   aws_secret_access_key='test')
                   
QUEUE_URL = 'http://localhost:4566/000000000000/fintech-raw-logs'

def emit_audit_log(validation_type, raw_input, status):
    """ Pushes the raw validation event to the SQS buffer. """
    log_event = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "operator": AUTHOR,
        "service": "fintech-validator",
        "event_type": validation_type,
        "status": status,
        "raw_data": raw_input # Contains the unmasked PII or audit report
    }

    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,               # Fixed: QueueURL -> QueueUrl
            MessageBody=json.dumps(log_event) # Fixed: MeesageBody -> MessageBody
        )
        print(f"[Validator] Audit log emitted to SQS for {validation_type}")
    except Exception as e:
        print(f"[!] Failed to emit audit log to SQS: {str(e)}")

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
    
    # Serialize the full report so it can be passed as a string payload
    raw_payload = json.dumps(full_report)
    
    if failed_checks:
        print(f"[WARNING] {len(failed_checks)} compliance violations detected! Halting deployment.")
        emit_audit_log("compliance_failure", raw_payload, "FAIL")
        exit(1)
    else:
        print("[SUCCESS] Infrastructure is 100% compliant. Proceeding with deployment.")
        emit_audit_log("compliance_success", raw_payload, "SUCCESS")
        exit(0)