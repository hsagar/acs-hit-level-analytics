# Infrastructure Deployment

Covers IAM permissions for the deployer user and SAM-based infrastructure management.

---

## 1. IAM Permissions

The `skr-deployer` user needs the following minimum permissions. Apply the policy:

```bash
aws iam put-user-policy \
  --user-name skr-deployer \
  --policy-name skr-deployer-policy \
  --policy-document file://infrastructure/skr-deployer-policy.json
```

---

## 2. SAM Template

[infrastructure/template.yaml](../infrastructure/template.yaml) defines all AWS resources:

- Two S3 buckets (raw input, processed output)
- Lambda function with an S3 trigger on the `raw/` prefix
- IAM execution role
- CloudWatch log group (30-day retention)

---

## 3. First-Time Deploy

```bash
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

`sam build` packages the Lambda code into `.aws-sam/build/`.  
`sam deploy` uploads the package to S3 and creates/updates the CloudFormation stack.

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

---

## 4. Subsequent Deploys

GitHub Actions handles this automatically on every push to `main`. To deploy manually:

```bash
sam build --template infrastructure/template.yaml && \
sam deploy \
  --stack-name skr-pipeline-dev \
  --s3-bucket ${SAM_BUCKET} \
  --parameter-overrides Environment=dev AccountId=${ACCOUNT_ID} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

---

## 5. S3 Bucket Layout

```
skr-raw-dev-{accountId}/
  raw/
  archive/

skr-processed-dev-{accountId}/
  processed/
    [2026-04-16]_SearchKeywordPerformance.tab
    [2026-04-17]_SearchKeywordPerformance.tab
```

---

## 6. Tear Down

```bash
aws s3 rm s3://skr-raw-dev-${ACCOUNT_ID} --recursive
aws s3 rm s3://skr-processed-dev-${ACCOUNT_ID} --recursive

aws cloudformation delete-stack --stack-name skr-pipeline-dev
aws cloudformation wait stack-delete-complete --stack-name skr-pipeline-dev
```
