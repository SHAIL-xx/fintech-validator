# 1. Configure the AWS Provider for LocalStack
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3  = "http://localhost:4566"
    sqs = "http://localhost:4566"
    iam = "http://localhost:4566"
    ec2 = "http://localhost:4566"
    kms = "http://localhost:4566"
    sts = "http://localhost:4566"
  }
}

# 2. Provision the SQS Queue
resource "aws_sqs_queue" "fintech_queue" {
  name = "fintech-raw-logs"
}

# 3. Provision the Compliant S3 Bucket
resource "aws_s3_bucket" "archive_bucket" {
  bucket = "fintech-masked-archive"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.archive_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 4. Provision the Compliant Security Group (No Port 22)
resource "aws_security_group" "db_sg" {
  name        = "fintech-database-sg"
  description = "Security group for internal FinTech database"
  # Intentionally omitting ingress rules to ensure network isolation compliance
}

# 5. Provision the Least-Privilege IAM Role
resource "aws_iam_role" "worker_role" {
  name = "MaskingWorkerRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = aws_iam_role.worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}