# acs-hit-level-analytics


## Overview

`acs-hit-level-analytics` reads Adobe Analytics hit-level TSV data and
produces a tab-delimited output of e-commerce revenue attributed to search
engine keywords.

## Quick Start

```bash
# Clone the repository
git clone git@github.com:hsagar/acs-hit-level-analytics.git
cd acs-hit-level-analytics
git fetch origin
git checkout develop

# Install dependencies
make install

# Run Tests
make test

# Cleanup
make clean
```

## SAM CLI

AWS SAM (Serverless Application Model) is the deployment tool for this project. It builds Lambda packages and manages CloudFormation stacks.

### Create an S3 Bucket for SAM Artifacts

SAM needs an S3 bucket to store deployment artifacts (Lambda ZIPs) before deploying. This is separate from the pipeline buckets.

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SAM_BUCKET="skr-sam-artifacts-${ACCOUNT_ID}"

aws s3 mb s3://${SAM_BUCKET} --region us-east-1
echo "SAM bucket: ${SAM_BUCKET}"
```

## IAM Permissions for Deployment

The `skr-deployer` IAM user (used by CLI and GitHub Actions) needs the following minimum permissions after initial setup.

### Minimum Permissions Policy

Create a file `infrastructure/skr-deployer-policy.json`:
Apply it to the user:

```bash
aws iam put-user-policy \
  --user-name skr-deployer \
  --policy-name skr-deployer-policy \
  --policy-document file://infrastructure/skr-deployer-policy.json
```

## Infrastructure Deployment (SAM)

### SAM Template

The file [template.yaml](infrastructure/template.yaml) defines all AWS resources. It creates:

- Two S3 buckets (raw input, processed output)
- A Lambda function with an S3 trigger on the `raw/` prefix
- An IAM execution role for the Lambda
- A CloudWatch log group with 30-day retention

### First-Time Deploy

```bash
# From the project root:
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SAM_BUCKET="skr-sam-artifacts-${ACCOUNT_ID}"

sam build --template infrastructure/template.yaml

sam deploy \
  --stack-name skr-pipeline-dev \
  --s3-bucket ${SAM_BUCKET} \
  --parameter-overrides \
      Environment=dev \
      AccountId=${ACCOUNT_ID} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --confirm-changeset
```

`sam build` packages the Lambda code and dependencies into `.aws-sam/build/`.  
`sam deploy` uploads the package to S3 and creates/updates the CloudFormation stack.

> The `--confirm-changeset` flag shows you exactly what will change before applying. Remove it for unattended deploys.

### Verify the Stack

```bash
aws cloudformation describe-stacks \
  --stack-name skr-pipeline-dev \
  --query 'Stacks[0].StackStatus'
# "CREATE_COMPLETE"

aws cloudformation describe-stack-resources \
  --stack-name skr-pipeline-dev \
  --query 'StackResources[*].[ResourceType,PhysicalResourceId]' \
  --output table
```

### Subsequent Deploys

For code changes after first deploy:

```bash
sam build && sam deploy --stack-name skr-pipeline-dev --s3-bucket ${SAM_BUCKET} \
  --parameter-overrides Environment=dev AccountId=${ACCOUNT_ID} \
  --capabilities CAPABILITY_NAMED_IAM --region us-east-1
```

### S3 Bucket Layout

```
skr-raw-dev-{accountId}/
  raw/          ← drop .tsv files here to trigger the pipeline
  archive/      ← processed files are moved here automatically

skr-processed-dev-{accountId}/
  processed/
    [2025-01-15]_SearchKeywordPerformance.tab
    [2025-01-16]_SearchKeywordPerformance.tab
```

### Tear Down

```bash
# Empties and removes all resources created by the stack
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 rm s3://skr-raw-dev-${ACCOUNT_ID} --recursive
aws s3 rm s3://skr-processed-dev-${ACCOUNT_ID} --recursive

aws cloudformation delete-stack --stack-name skr-pipeline-dev
aws cloudformation wait stack-delete-complete --stack-name skr-pipeline-dev
```
