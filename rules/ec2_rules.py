AUTHOR = "JACKAL"

def audit_security_groups(ec2_client):
    print(f"\n[{AUTHOR}] Executing FinTech Network Isolation Audit...")
    print("-" * 50)
    compliance_report = []
    try:
        custom_sgs = [sg for sg in ec2_client.describe_security_groups().get('SecurityGroups', []) if sg['GroupName'] != 'default']
        for sg in custom_sgs:
            sg_name = sg['GroupName']
            is_compliant = True
            for rule in sg.get('IpPermissions', []):
                if rule.get('FromPort', -1) <= 22 <= rule.get('ToPort', -1):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            is_compliant = False
            
            status = "PASS" if is_compliant else "FAIL"
            print(f"[{status}] Security Group: {sg_name:<20}")
            compliance_report.append({"resource": sg_name, "type": "Network_Isolation", "compliant": is_compliant})
            
        return compliance_report
    except Exception as e:
        return []