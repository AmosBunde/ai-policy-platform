# Terraform — RegulatorAI infrastructure (AWS)

Provisions VPC, EKS, RDS (PostgreSQL), ElastiCache (Redis), and OpenSearch.

## Remote state

State lives in S3 with DynamoDB locking (configured in `providers.tf`):

- Bucket: `regulatorai-terraform-state` (key `infrastructure/terraform.tfstate`, encrypted)
- Lock table: `regulatorai-terraform-locks`

### One-time bootstrap (before the first `terraform init`)

The state bucket and lock table are the only resources created outside
Terraform. Run once per AWS account:

```bash
aws s3api create-bucket \
  --bucket regulatorai-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket regulatorai-terraform-state \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket regulatorai-terraform-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"}}]}'

aws s3api put-public-access-block \
  --bucket regulatorai-terraform-state \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws dynamodb create-table \
  --table-name regulatorai-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Usage

```bash
terraform init                                  # connects to the S3 backend
terraform plan  -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
terraform output                                # cluster endpoint, DB host, …
```

Secrets (e.g. `rds_master_password`) are supplied via `TF_VAR_*` environment
variables or an untracked `secrets.auto.tfvars` — never committed.

## Notes

- Bucket names are globally unique; if `regulatorai-terraform-state` is taken
  in your account setup, change it in `providers.tf` *and* the bootstrap
  commands above, keeping them in sync.
- `terraform init -migrate-state` moves any pre-existing local state into the
  backend.
