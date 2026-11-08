provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

 endpoints {
    s3  = "http://127.0.0.1:4566"
    kms = "http://127.0.0.1:4566"
    ec2 = "http://127.0.0.1:4566"
    iam = "http://127.0.0.1:4566"
  }
}

resource "aws_kms_key" "wealthtech_key" {
  description = "KMS key for WealthTech secure vault"
}

# 1. Secure Vault Bucket
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
  bucket                  = aws_s3_bucket.secure_vault.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# 2. PATCHED: Public Drop is now KMS Encrypted and Blocked
resource "aws_s3_bucket" "public_drop" {
  bucket = "wealthtech-public-drop-local"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "public_drop_encryption" {
  bucket = aws_s3_bucket.public_drop.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.wealthtech_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "public_drop_bpa" {
  bucket                  = aws_s3_bucket.public_drop.id
  block_public_acls       = true # PATCHED
  ignore_public_acls      = true # PATCHED
  block_public_policy     = true # PATCHED
  restrict_public_buckets = true # PATCHED
}

# 3. Secure Security Group
resource "aws_security_group" "compliant_sg" {
  name        = "wealthtech-secure-sg"
  description = "Compliant SG allowing only HTTPS"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. PATCHED: SSH restricted to internal corporate IP range
resource "aws_security_group" "non_compliant_sg" {
  name        = "wealthtech-internal-sg"
  description = "Compliant SG with internal SSH"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"] # PATCHED
  }
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# 5. Restricted Role
resource "aws_iam_role" "compliant_role" {
  name               = "wealthtech-restricted-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "compliant_attach" {
  role       = aws_iam_role.compliant_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# 6. PATCHED: AdministratorAccess downgraded to EC2 ReadOnly
resource "aws_iam_role" "non_compliant_role" {
  name               = "wealthtech-admin-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "non_compliant_attach" {
  role       = aws_iam_role.non_compliant_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess" # PATCHED
}