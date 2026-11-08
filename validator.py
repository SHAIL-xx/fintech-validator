import boto3
from botocore.exceptions import ClientError
import json

AUTHOR = "JACKAL"

def get_local_client(service_name: str):
    """Returns a Boto3 client configured for LocalStack."""
    return boto3.client(
        service_name,
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

def audit_s3_encryption(s3_client):
    """
    Audits all S3 buckets for Server-Side Encryption (SSE-S3 or SSE-KMS).
    Fails buckets that lack encryption.
    """
    print(f"\n[{AUTHOR}] Executing FinTech S3 Encryption Audit...")
    print("-" * 50)
    
    compliance_report = []
    
    try:
        buckets = s3_client.list_buckets().get('Buckets', [])
        
        if not buckets:
            print("[INFO] No S3 buckets found in local environment.")
            return compliance_report
            
        for bucket in buckets:
            bucket_name = bucket['Name']
            is_compliant = False
            encryption_type = "UNENCRYPTED"
            
            try:
                # Attempt to retrieve encryption config
                response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
                
                if rules:
                    encryption_type = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                    is_compliant = (encryption_type == "aws:kms")
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                    # Expected error for unencrypted buckets
                    is_compliant = False
                else:
                    print(f"[ERROR] Failed to query {bucket_name}: {e}")
                    continue
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Bucket: {bucket_name:<20} | Algorithm: {encryption_type}")
            
            compliance_report.append({
                "resource": bucket_name,
                "type": "S3_Encryption",
                "compliant": is_compliant,
                "details": encryption_type
            })
            
        return compliance_report
        
    except Exception as e:
        print(f"[FATAL] Connection to LocalStack failed: {e}")
        return []

def audit_s3_public_access(s3_client):
    """
    Audits all S3 buckets for explicitly enabled Block Public Access.
    Fails buckets missing the configuration or having any setting disabled.
    """
    print(f"\n[{AUTHOR}] Executing FinTech S3 Public Access Audit...")
    print("-" * 50)
    
    compliance_report = []
    
    try:
        buckets = s3_client.list_buckets().get('Buckets', [])
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            is_compliant = False
            
            try:
                response = s3_client.get_public_access_block(Bucket=bucket_name)
                config = response.get('PublicAccessBlockConfiguration', {})
                
                # WealthTech strict: ALL four blocks must be explicitly TRUE
                if (config.get('BlockPublicAcls') and 
                    config.get('IgnorePublicAcls') and 
                    config.get('BlockPublicPolicy') and 
                    config.get('RestrictPublicBuckets')):
                    is_compliant = True
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchPublicAccessBlockConfiguration':
                    # Missing configuration means it is vulnerable
                    is_compliant = False
                else:
                    print(f"[ERROR] Failed to query {bucket_name}: {e}")
                    continue
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Bucket: {bucket_name:<20}")
            
            compliance_report.append({
                "resource": bucket_name,
                "type": "S3_Public_Access",
                "compliant": is_compliant
            })
            
        return compliance_report
        
    except Exception as e:
        print(f"[FATAL] Execution failed: {e}")
        return [] 

def audit_security_groups(ec2_client):
    """
    Audit all custom EC2 Security groups for network isolation.
    """
    print(f"\n[{AUTHOR}] Executing FinTech Network Isolation Audit...")
    print("-"*50)

    compliance_report = []

    try:
        sgs = ec2_client.describe_security_groups().get('SecurityGroups', [])

        # Filter out default VPC security groups to keep the audit focused 
        custom_sgs = [sg for sg in sgs if sg['GroupName'] != 'default']

        for sg in custom_sgs:
            sg_name = sg['GroupName']
            is_compliant = True

            for rule in sg.get('IpPermissions', []):
                # Check if standard SSH (Port 22) is in the allowed range 
                if rule.get('FromPort', -1) <= 22 <= rule.get('ToPort', -1):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            is_compliant = False
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Security Group: {sg_name:<20}")

            compliance_report.append({
                "resource": sg_name,
                "type": "Network_Isolation",
                "compliant": is_compliant
            })

        return compliance_report

    except Exception as e :
        print(f"[FATAL] EC2 Execution failed: {e}")
        return []

if __name__ == "__main__":
    print(f"[{AUTHOR}] Initializing FinTech Compliance Validator...\n")
    
    s3 = get_local_client('s3')
    ec2 = get_local_client('ec2')
    
    # 1. Collect all audit data
    full_report = []
    full_report.extend(audit_s3_encryption(s3))
    full_report.extend(audit_s3_public_access(s3))
    full_report.extend(audit_security_groups(ec2))
    
    # 2. Export to JSON artifact
    report_file = "compliance_report.json"
    with open(report_file, "w") as f:
        json.dump(full_report, f, indent=4)
        
    print(f"\n[{AUTHOR}] Audit complete. Full results saved to {report_file}")
    
    # 3. CI/CD Pipeline Enforcement
    failed_checks = [check for check in full_report if not check.get('compliant')]
    
    if failed_checks:
        print(f"[WARNING] {len(failed_checks)} compliance violations detected! Halting deployment.")
        exit(1) # Tells the OS/Pipeline that the job failed
    else:
        print("[SUCCESS] Infrastructure is 100% compliant. Proceeding with deployment.")
        exit(0) # Tells the OS/Pipeline that the job succeeded