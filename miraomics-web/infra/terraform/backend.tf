# Remote state in S3 with DynamoDB locking.
#
# Bootstrap the state bucket + lock table ONCE before `terraform init`
# (they can't be created by the same config that stores its state in them):
#
#   aws s3api create-bucket --bucket miraomics-tfstate --region us-east-1
#   aws s3api put-bucket-versioning --bucket miraomics-tfstate \
#     --versioning-configuration Status=Enabled
#   aws dynamodb create-table --table-name miraomics-tflock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST
#
# Then uncomment and run `terraform init`.

terraform {
  backend "s3" {
    bucket         = "miraomics-tfstate"
    key            = "web/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "miraomics-tflock"
    encrypt        = true
  }
}
