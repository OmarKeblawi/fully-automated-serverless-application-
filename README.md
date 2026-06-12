# Fully Automated Serverless Application

A fully automated serverless application on AWS, deployed with **AWS CDK (Python)** as Infrastructure as Code. On each invocation the Lambda function lists all objects in an S3 bucket and sends an email summary via SNS. Sample files are uploaded to S3 automatically during every deployment, and the Lambda can be triggered manually for testing.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Tools & Frameworks](#tools--frameworks)
5. [Prerequisites](#prerequisites)
6. [Setup & Deployment](#setup--deployment)
7. [Manual Lambda Test Instructions](#manual-lambda-test-instructions)
8. [CI/CD with GitHub Actions](#cicd-with-github-actions)
9. [Important Notes](#important-notes)

---

## Project Overview

| Component | What it does |
|-----------|-------------|
| **S3 Bucket** | Stores the sample files; the Lambda reads from it |
| **S3 BucketDeployment** | Uploads every file in `sample_files/` to S3 on each `cdk deploy` |
| **Lambda Function** | Lists all bucket objects and publishes a summary to SNS |
| **SNS Topic** | Broadcasts the execution report to subscribed email addresses |
| **IAM Role** | Least-privilege role: S3 read + SNS publish + Lambda execution |
| **GitHub Actions** | `workflow_dispatch`-triggered CI/CD pipeline that runs `cdk deploy` |

---

## Architecture

```
GitHub Actions (workflow_dispatch)
        │
        ▼
   cdk deploy
        │
        ├─► S3 Bucket  ◄── BucketDeployment uploads sample_files/
        │
        ├─► SNS Topic + Email Subscription
        │
        └─► Lambda Function (Python 3.12)
                  │  on invoke
                  ├─► s3:ListBucket  ──► collect object list
                  └─► sns:Publish   ──► email notification
```

---

## Repository Structure

```
.
├── app.py                        # CDK app entry point
├── cdk.json                      # CDK configuration
├── requirements.txt              # CDK Python dependencies
├── requirements-dev.txt          # Dev/test dependencies
├── test_event.json               # Sample event for manual Lambda invocation
├── .github/
│   └── workflows/
│       └── deploy.yml            # GitHub Actions deploy workflow
├── infrastructure/
│   └── serverless_stack.py       # CDK Stack definition
├── lambda/
│   └── handler.py                # Lambda function source code
├── sample_files/
│   ├── sample1.txt
│   ├── sample2.txt
│   └── sample3.csv
└── tests/
    ├── invoke_lambda.py          # boto3 manual-trigger script
    └── test_handler.py           # Unit tests (no AWS credentials needed)
```

---

## Tools & Frameworks

| Tool | Version | Purpose |
|------|---------|---------|
| [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) | v2 (Python) | Infrastructure as Code |
| Python | 3.12 | Lambda runtime & CDK app language |
| Node.js | 20 | Required by CDK CLI |
| boto3 | latest | AWS SDK for manual trigger script & unit tests |
| pytest | ≥7 | Unit testing |
| GitHub Actions | — | CI/CD pipeline |

---

## Prerequisites

### Local development

- **AWS CLI** configured (`aws configure`) with admin-level permissions
- **Node.js 20+** (`node --version`)
- **Python 3.12+** (`python3 --version`)
- **AWS CDK CLI** — install globally:

  ```bash
  npm install -g aws-cdk
  cdk --version
  ```

- Install Python dependencies:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate          # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt   # for tests/manual invoke
  ```

### GitHub repository secrets (for CI/CD)

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | ARN of the IAM role to assume via OIDC (e.g. `arn:aws:iam::123456789012:role/GitHubActionsRole`) |
| `AWS_REGION` | *(optional)* AWS region; defaults to `us-east-1` |

> See [Configuring OIDC in AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) to set up the trust relationship.

---

## Setup & Deployment

### 1. Bootstrap CDK (one-time per account/region)

```bash
cdk bootstrap
```

### 2. Deploy

```bash
cdk deploy --context notification_email=your-email@example.com
```

CDK will:
1. Create the S3 bucket
2. Upload `sample_files/` contents into the bucket under the `sample_files/` prefix
3. Create the SNS topic and add your email as a subscriber
4. Create the IAM role with least-privilege permissions
5. Deploy the Lambda function

At the end of the deploy you will see CloudFormation **Outputs** similar to:

```
Outputs:
ServerlessStack.BucketName        = serverlessstack-samplebucket1234-abc
ServerlessStack.LambdaFunctionName = ServerlessStack-ServerlessHandler1234
ServerlessStack.TopicArn          = arn:aws:sns:us-east-1:123456789012:serverless-app-notifications
```

Keep the `LambdaFunctionName` handy for manual testing.

### 3. Confirm the SNS email subscription

> **⚠️ Important:** AWS SNS will send a confirmation email to the address you provided. You **must click the "Confirm subscription" link** in that email before any notifications will be delivered.

### 4. Destroy (cleanup)

```bash
cdk destroy
```

---

## Manual Lambda Test Instructions

Three ways to manually invoke the Lambda:

### Option A — Invoke script (boto3)

```bash
# Activate your virtual env first
source .venv/bin/activate

python tests/invoke_lambda.py \
  --function-name ServerlessStack-ServerlessHandler1234 \
  --region us-east-1
```

The script reads `test_event.json` as the payload by default. Pass `--event-file path/to/event.json` to use a custom file.

### Option B — AWS CLI

```bash
aws lambda invoke \
  --function-name ServerlessStack-ServerlessHandler1234 \
  --payload file://test_event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

### Option C — AWS Management Console

1. Open the **Lambda** console → select the function
2. Click **Test** → create a new test event with the contents of `test_event.json`
3. Click **Test** again to invoke

### Expected output

After a successful invocation you will receive an email like:

```
Subject: S3 Bucket Report – 3 object(s) found

Serverless App – Execution Report
Timestamp : 2024-11-15T10:30:00.123456+00:00
Bucket    : serverlessstack-samplebucket1234-abc
Objects   : 3

Object listing:
  - sample_files/sample1.txt (255 bytes)
  - sample_files/sample2.txt (248 bytes)
  - sample_files/sample3.csv (189 bytes)
```

---

## CI/CD with GitHub Actions

The workflow is located at `.github/workflows/deploy.yml` and is triggered **manually** via `workflow_dispatch`.

### How to trigger

1. Go to **Actions** → **Deploy Serverless Application**
2. Click **Run workflow**
3. Enter your notification email address
4. Click **Run workflow**

The pipeline will:
1. Set up Python 3.12 and Node.js 20
2. Install the CDK CLI and Python dependencies
3. Authenticate to AWS using OIDC (no long-lived credentials stored)
4. Run `cdk bootstrap` (idempotent)
5. Run `cdk deploy --require-approval never`

### Running unit tests locally

```bash
pytest tests/test_handler.py -v
```

No AWS credentials are required — the tests mock all boto3 calls.

---

## Important Notes

- **SNS email confirmation is required.** After the first deployment, check your inbox for a confirmation email from `no-reply@sns.amazonaws.com` and click the confirmation link. Notifications will not be delivered until this is done.
- The S3 bucket is created with `RemovalPolicy.DESTROY` and `auto_delete_objects=True`, so running `cdk destroy` will delete the bucket and all its contents.
- The IAM role follows the **principle of least privilege**: it only grants `s3:ListBucket` + `s3:GetObject` on the specific bucket, and `sns:Publish` on the specific topic.
- The CDK `BucketDeployment` construct uses a helper Lambda under the hood to copy files; this Lambda requires internet access (or a VPC endpoint) if deployed inside a VPC.
