from botocore.exceptions import ClientError

AUTHOR = "JACKAL"

def audit_s3_encryption(s3_client):
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
                response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
                if rules:
                    encryption_type = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                    is_compliant = (encryption_type == 'aws:kms')
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    is_compliant = False
                else:
                    continue
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Bucket: {bucket_name:<20} | Algorithm: {encryption_type}")
            compliance_report.append({"resource": bucket_name, "type": "S3_Encryption", "compliant": is_compliant, "details": encryption_type})
            
        return compliance_report
    except Exception as e:
        return []

def audit_s3_public_access(s3_client):
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
                if (config.get('BlockPublicAcls') and config.get('IgnorePublicAcls') and 
                    config.get('BlockPublicPolicy') and config.get('RestrictPublicBuckets')):
                    is_compliant = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    is_compliant = False
                else:
                    continue
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Bucket: {bucket_name:<20}")
            compliance_report.append({"resource": bucket_name, "type": "S3_Public_Access", "compliant": is_compliant})
            
        return compliance_report
    except Exception as e:
        return []