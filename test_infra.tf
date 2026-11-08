provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3  = "http://localhost:4566"
    kms = "http://localhost:4566"
    ec2 = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}

resource "aws_kms_key" "wealthtech_key" {
  description = "KMS key for WealthTech secure vault"
}

# 1. Compliant Bucket
resource "aws_s3_bucket" "secure_vault" {
  bucket = "wealthtech-secure-vault-local"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure_vault_encryption" {
  bucket = aws_s3_bucket.secure_vault.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.wealthtech_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "secure_vault_bpa" {
  bucket = aws_s3_bucket.secure_vault.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# 2. Non-Compliant Bucket
resource "aws_s3_bucket" "public_drop" {
  bucket = "wealthtech-public-drop-local"
}

resource "aws_s3_bucket_public_access_block" "public_drop_bpa" {
  bucket = aws_s3_bucket.public_drop.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
} 

# 3. Complaint Security Groups (No SSH exposure)
resource "aws_security_group" "complaint_sg" {
  name = "wealthcare-secure-sg"
  description = "Complaint SG allowing only HTTPS"

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. Non-Complaint Security Group (Open SSH)
resource "aws_security_group" "non_complaint_sg"{
  name = "wealthcare-open-sg"
  description = "Non-complaint SG with open SSH"

  ingress{
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
} 

# Standard Trust Policy for EC2
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# 5. Compliant IAM Role (Restricted Access)
resource "aws_iam_role" "compliant_role" {
  name               = "wealthtech-restricted-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "compliant_attach" {
  role       = aws_iam_role.compliant_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# 6. Non-Compliant IAM Role (AdministratorAccess)
resource "aws_iam_role" "non_compliant_role" {
  name               = "wealthtech-admin-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "non_compliant_attach" {
  role       = aws_iam_role.non_compliant_role.name
  # WealthTech Violation: Full admin rights granted to a custom role
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" 
}