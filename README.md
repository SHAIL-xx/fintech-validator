# FinTech DevSecOps Compliance Engine

Author: JACKAL
Domain: Cloud Security / Infrastructure as Code (IaC)

An automated Infrastructure-as-Code security auditing engine designed for FinTech and WealthTech compliance. This project provisions AWS infrastructure using Terraform, emulates the cloud environment locally using LocalStack, and evaluates security posture using a custom Python (Boto3) rules engine.

Integrated into a GitHub Actions CI/CD pipeline, the validator acts as a Shift-Left security gatekeeper, automatically failing deployments if infrastructure violates the Principle of Least Privilege, exposes data, or opens vulnerable network ports.

## Architecture and Workflow

1. Developer pushes code to GitHub, triggering the CI/CD pipeline.
2. GitHub Actions boots the LocalStack container.
3. Terraform applies the test_infra.tf blueprint.
4. Python Boto3 Validator executes compliance checks against S3, EC2, and IAM.
5. If violations are found, the pipeline exits with code 1 to block deployment.
6. If 100% compliant, the pipeline exits with code 0 to allow deployment.
7. A compliance_report.json artifact is exported in both scenarios.

## Security Rules Enforced

1. S3 Data at Rest (Encryption): Fails any bucket not utilizing aws:kms server-side encryption.
2. S3 Data Exposure (BPA): Fails any bucket where Block Public Access (BPA) booleans are not set to true.
3. EC2 Network Isolation: Fails any Security Group allowing SSH (Port 22) access from the public internet (0.0.0.0/0).
4. IAM Least Privilege: Fails any custom IAM role possessing the AdministratorAccess managed policy.

## Local Execution

To run this auditing engine on your local workstation:

1. Start the Local Cloud Emulator:
   lstk start

2. Provision the Mock Infrastructure:
   terraform init
   terraform apply -auto-approve

3. Run the Security Audit:
   python3 validator.py

## CI/CD Pipeline Automation

This repository includes a native .github/workflows/audit.yml pipeline that automates the entire validation lifecycle in an ephemeral Ubuntu runner.

- Zero-Friction: Uses an isolated Docker run command to spin up LocalStack without socket permission conflicts.
- Race-Condition Proof: Implements a strict curl polling loop to guarantee the LocalStack health endpoint is responsive before Terraform attempts to connect.
- Artifact Generation: Automatically uploads the compliance_report.json as a downloadable GitHub Artifact, regardless of pipeline success or failure.

## Project Structure

fintech-validator/
|-- .github/workflows/audit.yml
|-- core/client.py
|-- rules/ec2_rules.py
|-- rules/iam_rules.py
|-- rules/s3_rules.py
|-- test_infra.tf
|-- validator.py