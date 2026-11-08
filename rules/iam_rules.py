from botocore.exceptions import ClientError

AUTHOR = "JACKAL"

def audit_iam_roles(iam_client):
    print(f"\n[{AUTHOR}] Executing FinTech IAM Privilege Audit...")
    print("-" * 50)
    compliance_report = []
    try:
        custom_roles = [role for role in iam_client.list_roles().get('Roles', []) if 'aws-service-role' not in role['Path']]
        for role in custom_roles:
            role_name = role['RoleName']
            is_compliant = True
            try:
                attached_policies = iam_client.list_attached_role_policies(RoleName=role_name).get('AttachedPolicies', [])
                for policy in attached_policies:
                    if policy['PolicyArn'] == 'arn:aws:iam::aws:policy/AdministratorAccess':
                        is_compliant = False
                        break
            except ClientError:
                continue
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] IAM Role: {role_name:<25}")
            compliance_report.append({"resource": role_name, "type": "IAM_Least_Privilege", "compliant": is_compliant})
            
        return compliance_report
    except Exception as e:
        return []