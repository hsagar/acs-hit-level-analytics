# AWS Setup

Prerequisites and one-time setup before deploying the pipeline.

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|---|---|---|
| Python | 3.13+ | Runtime and local dev |
| uv | latest | Package manager |
| Git | any | Source control |
| AWS CLI | v2 | Interact with AWS |
| AWS SAM CLI | 1.100+ | Deploy serverless infrastructure |

Verify:

```bash
python --version
uv --version
aws --version
sam --version
```

---

## 1. AWS Account Setup

* Create an AWS Account
* Enable MFA on the Root Account
* Create an IAM Admin User
* Create an IAM skr-deployer User

---

## 2. AWS CLI Setup

* Install (macOS)
```bash
brew install awscli
```

* Create an IAM User for Programmatic Access

* Configure the CLI

* Verify:

```bash
aws sts get-caller-identity
```

* Save your account ID — needed in later steps:

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

---

## 3. SAM CLI Setup

* Install (macOS)
```bash
brew tap aws/tap && brew install aws-sam-cli
```

* Create an S3 Bucket for SAM Artifacts

```bash
SAM_BUCKET="skr-sam-artifacts-${ACCOUNT_ID}"

aws s3 mb s3://${SAM_BUCKET} --region us-east-1
echo "SAM bucket: ${SAM_BUCKET}"
```
