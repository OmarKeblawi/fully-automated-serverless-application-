# Project Walkthrough — Plain English Guide

This document explains every part of this project in simple terms.  
If you're preparing for an interview, read this end-to-end — it covers what each file does, what each AWS service is, and how everything connects together.

---

## Table of Contents

- [What Does This Project Do?](#what-does-this-project-do)
- [AWS Services Used (Explained Simply)](#aws-services-used-explained-simply)
- [Key Concepts Explained](#key-concepts-explained)
- [How the Code Works — File by File](#how-the-code-works--file-by-file)
- [How to Set Up Your AWS Account](#how-to-set-up-your-aws-account)
- [How to Fix the GitHub Actions Error](#how-to-fix-the-github-actions-error)
- [Interview Q&A Cheat Sheet](#interview-qa-cheat-sheet)

---

## What Does This Project Do?

Imagine you have a folder of files on your computer. This project does the following automatically:

1. **Creates a storage space on AWS** (called an S3 bucket — think of it like a Google Drive folder in the cloud)
2. **Uploads your sample files** from your computer to that cloud storage
3. **Creates a small program that runs in the cloud** (called a Lambda function) — when you trigger it, it:
   - Looks at all the files in the storage space
   - Sends you an **email** listing what files are there
4. **Sets up an email notification system** (called SNS) so you get that email
5. **All of this is done automatically** — you don't click around the AWS website to create things. Instead, the code describes what you want, and AWS builds it for you

---

## AWS Services Used (Explained Simply)

### S3 (Simple Storage Service)
**What it is:** Cloud file storage. Think of it like Google Drive or Dropbox, but for programs.  
**In this project:** We create a "bucket" (a folder) and upload 3 sample files into it.  
**Analogy:** S3 bucket = a folder in the cloud. Objects = the files inside it.

### Lambda
**What it is:** A way to run a small program in the cloud **without owning a server**. You just upload your code, and AWS runs it for you whenever you tell it to.  
**In this project:** Our Lambda function is a Python script that reads the list of files in the S3 bucket and sends you an email about them.  
**Analogy:** Lambda = a robot worker that sits idle until you tell it to do something. You only pay for the seconds it actually works.  
**Why "serverless"?** You don't need to set up or manage any server. AWS handles all the computing infrastructure — you just provide the code.

### SNS (Simple Notification Service)
**What it is:** A messaging service. You create a "topic" (like a mailing list), subscribe email addresses to it, and then your code can send messages to all subscribers.  
**In this project:** When the Lambda runs, it publishes a message to the SNS topic, and SNS delivers that message as an email to you.  
**Analogy:** SNS topic = a WhatsApp group. Publishing = sending a message to the group. Subscribers = people in the group who receive it.

### IAM (Identity and Access Management)
**What it is:** The security system of AWS. It controls **who** can do **what** on **which** resources.  
**In this project:** We create a "role" (like an employee badge with limited access) that only allows our Lambda to:
- Read files from our specific S3 bucket (not other people's buckets)
- Send messages to our specific SNS topic (not other topics)
- Write its own logs  

**Analogy:** IAM role = a keycard. Our Lambda's keycard only opens 3 doors: the storage room (S3), the mailroom (SNS), and its own locker (CloudWatch Logs). It can't open any other door in the building.

### CloudFormation
**What it is:** AWS's system for creating resources from a blueprint. You give it a template (a JSON/YAML file) that says "I want an S3 bucket, a Lambda function, etc." and CloudFormation creates everything for you.  
**In this project:** We don't write CloudFormation directly — instead, we use CDK (see below), which generates the CloudFormation template for us.

### CloudWatch Logs
**What it is:** AWS's logging system. When your Lambda runs, its `print` statements and errors show up here.  
**In this project:** The `AWSLambdaBasicExecutionRole` policy gives our Lambda permission to write its logs here.

---

## Key Concepts Explained

### What is CDK (Cloud Development Kit)?

**The problem:** Normally, to create AWS resources, you either:
- Click around the AWS website (console) — tedious, error-prone, not repeatable
- Write a CloudFormation template in JSON/YAML — works but is verbose and hard to read

**The solution:** CDK lets you write **Python code** (or other languages) that describes what AWS resources you want. CDK then converts your Python code into a CloudFormation template automatically.

**Think of it this way:**
- CloudFormation = writing a construction blueprint by hand
- CDK = telling an architect what you want in plain language, and they draw the blueprint for you

**In this project:** The file `infrastructure/serverless_stack.py` is where we describe all our AWS resources in Python. When we run `cdk deploy`, CDK:
1. Runs our Python code
2. Generates a CloudFormation template
3. Sends that template to AWS
4. AWS reads the template and creates everything

### What is IaC (Infrastructure as Code)?

Instead of manually clicking around a website to create servers, databases, storage, etc., you **write code** that describes what you want. Benefits:
- **Repeatable:** Run the same code and get the same infrastructure every time
- **Version-controlled:** Your infrastructure is in Git, so you can track changes
- **Reviewable:** Someone can review your infrastructure the same way they review code
- **Destroyable:** Run one command to tear everything down

CDK is one IaC tool. Others include Terraform, CloudFormation (raw), and Pulumi.

### What is an Identity Provider?

**Simple explanation:** An Identity Provider (IdP) is a service that verifies "who you are." 

**Examples you already use:**
- When you click "Sign in with Google" on a website — Google is the Identity Provider
- When you log into GitHub — GitHub is the Identity Provider

**In this project:** We tell AWS: "Hey, GitHub is a trusted Identity Provider. If someone proves they're coming from my GitHub repository, give them access."

### What is OIDC (OpenID Connect)?

**Simple explanation:** OIDC is a **protocol** (a set of rules) for proving your identity across different services. It's the technology behind "Sign in with Google/GitHub/Facebook" buttons.

**The problem it solves in this project:**  
Our GitHub Actions workflow needs to deploy things to our AWS account. But how does AWS know the request is really coming from our GitHub repo and not some random hacker?

**Without OIDC (the old way):**
1. You create a username/password (access key) in AWS
2. You paste that password into GitHub as a "secret"
3. GitHub Actions uses that password every time it needs to talk to AWS
4. **Risk:** If someone steals that password, they have permanent access to your AWS account

**With OIDC (the modern way):**
1. You tell AWS: "I trust GitHub as an identity provider"
2. When GitHub Actions runs, GitHub gives the workflow a **temporary ID card** (called a JWT token)
3. The workflow shows that ID card to AWS
4. AWS checks: "Is this ID card from GitHub? Is it from the right repository? OK, here are temporary credentials that expire in 1 hour"
5. **Benefit:** No permanent password stored anywhere. If someone sees the temporary credentials, they expire quickly

**Analogy:** 
- Old way = giving your house key to a friend (if they lose it, anyone can enter)
- OIDC = your friend uses a video doorbell, you see it's them, and you remotely unlock the door for 5 minutes

### What is `cdk bootstrap`?

Before CDK can deploy your resources, it needs a place to store temporary files (like the zip file of your Lambda code). `cdk bootstrap` creates a special S3 bucket and some IAM roles in your AWS account for this purpose. You only need to do this **once per AWS account per region**.

**Analogy:** Before you can cook, you need to set up the kitchen (put up shelves, plug in the oven). You only do this once — after that, you can cook as many meals as you want.

### What is "Least Privilege"?

A security principle: give every component **only the permissions it needs** and nothing more.

**Example:** If a bank employee only needs to access the vault, don't also give them the key to the CEO's office. In our project, the Lambda only needs to read S3 and publish to SNS, so that's all we allow.

### What is `workflow_dispatch`?

A GitHub Actions trigger that means: "This workflow runs only when someone **manually** clicks the 'Run workflow' button on the GitHub website." It doesn't run automatically on every push or pull request.

---

## How the Code Works — File by File

### `app.py` — The Starting Point

Think of this as the **front door** of the application. When you run `cdk deploy`, CDK reads `cdk.json` which says "run `python3 app.py`". This file:
- Creates the CDK application
- Says "I want a stack called ServerlessStack" (a stack = a group of related AWS resources)
- Tells CDK which AWS account and region to deploy to

### `infrastructure/serverless_stack.py` — The Blueprint

This is the **most important file**. It describes **every AWS resource** that gets created:

1. **S3 Bucket** (lines 34-42):
   - Creates the cloud storage
   - `RemovalPolicy.DESTROY` = delete this bucket when I run `cdk destroy` (normally AWS keeps it around for safety)
   - `auto_delete_objects=True` = empty the bucket first before deleting (you can't delete a bucket that has files in it)
   - `BlockPublicAccess.BLOCK_ALL` = nobody on the internet can access this bucket directly

2. **Upload Sample Files** (lines 45-51):
   - Takes the files from your local `sample_files/` folder
   - Uploads them to the S3 bucket every time you deploy
   - The files end up in a subfolder called `sample_files/` inside the bucket

3. **SNS Topic + Email** (lines 54-63):
   - Creates the notification topic (the mailing list)
   - Subscribes your email address to it
   - The email address comes from either the command line or an environment variable

4. **IAM Role** (lines 66-98):
   - Creates the security badge for the Lambda
   - Adds 3 permissions: read S3, publish to SNS, write logs

5. **Lambda Function** (lines 101-115):
   - Creates the Lambda using Python 3.12
   - Points to the code in the `lambda/` folder
   - Gives it the IAM role we created
   - Passes the bucket name and SNS topic ARN as "environment variables" (so the Lambda code knows which bucket and topic to use)

6. **Outputs** (lines 118-131):
   - After deployment, prints out important information (bucket name, function name, etc.)

### `lambda/handler.py` — The Actual Program

This is the **Python code that runs in the cloud** when the Lambda is triggered:

1. **Step 1:** Get the list of all files in the S3 bucket
   - Uses pagination (if there are more than 1000 files, S3 sends them in batches — this code handles that)
2. **Step 2:** Build a human-readable message with:
   - Current timestamp
   - Bucket name
   - How many files were found
   - A list of each file with its size
3. **Step 3:** Send that message to the SNS topic (which delivers it as an email)
4. **Step 4:** Return a JSON response saying "success" with all the details

**Why are the boto3 clients created outside the function?**  
When AWS runs your Lambda, it keeps the "container" warm for a while after the first run. If another request comes in within ~15 minutes, it reuses the same container. Creating the clients outside the function means they're created once and reused, making subsequent runs faster.

### `.github/workflows/deploy.yml` — The Automation Pipeline

This is the GitHub Actions workflow. When you click "Run workflow" on GitHub:

1. **Checks out your code** from the repository
2. **Installs Python 3.12** (the Lambda is written in Python)
3. **Installs Node.js 20** (CDK CLI is a Node.js application, even though our code is Python)
4. **Installs the CDK CLI** (`npm install -g aws-cdk`)
5. **Installs Python packages** (`pip install -r requirements.txt`)
6. **Logs into AWS** using OIDC ← this is where the error happens if not set up
7. **Runs `cdk bootstrap`** (sets up the CDK kitchen, safe to run multiple times)
8. **Runs `cdk deploy`** (creates/updates all the AWS resources)

### `tests/test_handler.py` — The Unit Tests

These tests verify that the Lambda function works correctly **without actually connecting to AWS**. They:
- Replace ("mock") the real AWS connections with fake ones
- Call the Lambda function with test data
- Check that it returns the right response

**7 tests:**
- Does it return a 200 status code? ✅
- Does it count objects correctly? ✅
- Does it list the right file names? ✅
- Does it include the bucket name? ✅
- Does it call SNS exactly once? ✅
- Does it include the SNS message ID? ✅
- Does it handle an empty bucket without crashing? ✅

### `tests/invoke_lambda.py` — Manual Trigger Script

After deploying, you can use this script to trigger the Lambda from your computer:
```bash
python tests/invoke_lambda.py --function-name <NAME_FROM_CDK_OUTPUT>
```
It sends a test request to your deployed Lambda and shows you the response.

### `test_event.json` — Test Input

A simple JSON file that gets sent to the Lambda when you trigger it manually. The Lambda doesn't actually use the content of this event — it always just lists the S3 bucket and sends an email. But Lambda always expects some input event.

### `sample_files/` — The Files That Get Uploaded

Three sample files (`sample1.txt`, `sample2.txt`, `sample3.csv`) that get uploaded to the S3 bucket during deployment. These are the files the Lambda will list when it runs.

### `cdk.json` — CDK Configuration

Tells CDK:
- How to run the app (`python3 app.py`)
- Various feature flags (these are CDK best-practice settings that control the behavior of different AWS service constructs)

### `requirements.txt` — Python Dependencies

The Python packages needed to run CDK:
- `aws-cdk-lib` — the CDK library itself
- `constructs` — a supporting library for CDK

### `requirements-dev.txt` — Development Dependencies

Extra packages for testing/development:
- `pytest` — for running unit tests
- `boto3` — AWS SDK for Python (used by the invoke script)

---

## How to Set Up Your AWS Account

### Do I Need an AWS Account?

**Yes.** The assignment says "deploy a fully automated serverless application on AWS." There's no way around it — you need a real AWS account to deploy to.

**Will it cost money?** Probably not. AWS Free Tier gives you:
- 1 million Lambda invocations per month — free
- 5 GB of S3 storage — free
- SNS email notifications — free (first 1,000)
- All of this is free for 12 months after creating your account

### Step 1: Create an AWS Account

1. Go to [https://aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Enter your email, choose a password, pick an account name
4. Enter your credit card (required, but you won't be charged for this project)
5. Verify your identity (phone verification)
6. Choose the "Basic Support — Free" plan
7. Sign in to the AWS Console

### Step 2: Create an IAM User for Yourself (Best Practice)

When you created your AWS account, you got a "root" account. It's best practice not to use it for daily work.

1. Go to the AWS Console → search for **IAM** → click it
2. Click **Users** in the left sidebar → **Create user**
3. Name: `admin` (or your name)
4. Check **"Provide user access to the AWS Management Console"**
5. Choose **"I want to create an IAM user"**
6. Set a password
7. Click **Next** → **Attach policies directly** → check **AdministratorAccess** → **Next** → **Create user**
8. Save the sign-in URL and log out of root, then log in as this new IAM user

### Step 3: Set Up OIDC So GitHub Actions Can Access Your AWS Account

This is the part that tells AWS: "Trust my GitHub repository."

#### 3a. Create the Identity Provider

1. In the AWS Console, go to **IAM** → **Identity providers** (left sidebar)
2. Click **Add provider**
3. Fill in:
   - **Provider type:** OpenID Connect
   - **Provider URL:** `https://token.actions.githubusercontent.com` → click **Get thumbprint**
   - **Audience:** `sts.amazonaws.com`
4. Click **Add provider**

#### 3b. Create the Role for GitHub Actions

1. Go to **IAM** → **Roles** → **Create role**
2. **Trusted entity type:** Web identity
3. **Identity provider:** Select `token.actions.githubusercontent.com` (the one you just created)
4. **Audience:** Select `sts.amazonaws.com`
5. Click **Next**
6. Search for and check **AdministratorAccess** → click **Next**
7. **Role name:** `GitHubActionsDeployRole`
8. Click **Create role**

Now you need to **edit the trust policy** to restrict access to your specific repository:

1. Click on the role you just created (`GitHubActionsDeployRole`)
2. Go to the **Trust relationships** tab → click **Edit trust policy**
3. Replace the content with this (change `YOUR_GITHUB_USERNAME` and `YOUR_REPO_NAME`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
```

4. Replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID (find it in the top-right corner of the AWS console)
5. Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username
6. Replace `YOUR_REPO_NAME` with `fully-automated-serverless-application`
7. Click **Update policy**

Now, copy the **Role ARN** from the role's summary page. It looks like:  
`arn:aws:iam::123456789012:role/GitHubActionsDeployRole`

### Step 4: Add Secrets to Your GitHub Repository

1. Go to your GitHub repository page
2. Click **Settings** (tab at the top)
3. In the left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret** and add:

| Name | Value |
|------|-------|
| `AWS_ROLE_ARN` | The role ARN you copied (e.g., `arn:aws:iam::123456789012:role/GitHubActionsDeployRole`) |
| `AWS_REGION` | `us-east-1` |

---

## How to Fix the GitHub Actions Error

The error you saw:
```
Error: Credentials could not be loaded, please check your action inputs:
Could not load credentials from any providers
```

**Why it happened:** The workflow tried to authenticate with AWS using OIDC, but:
- The `AWS_ROLE_ARN` secret was either missing or empty in your GitHub repo, AND/OR
- The OIDC Identity Provider wasn't set up in your AWS account, AND/OR
- The IAM role didn't exist or didn't trust GitHub

**How to fix:** Complete all the steps in the [How to Set Up Your AWS Account](#how-to-set-up-your-aws-account) section above.

After setup is complete:
1. Push any code changes to GitHub
2. Go to **Actions** tab → **Deploy Serverless Application** → **Run workflow**
3. Enter your real email address in the input field
4. Click **Run workflow** and watch it complete

After deployment:
- **Check your email** — you'll receive a "AWS Notification - Subscription Confirmation" email from AWS. **You must click the "Confirm subscription" link** or you won't receive any Lambda notifications.

---

## Interview Q&A Cheat Sheet

### "What does this project do?"
> It's a serverless application on AWS. It creates cloud storage (S3), uploads sample files to it during deployment, and creates a Lambda function that — when triggered — lists all the files in the storage and sends an email report via SNS. Everything is defined as Infrastructure as Code using AWS CDK, and the deployment is automated through a GitHub Actions CI/CD pipeline.

### "What is Infrastructure as Code?"
> Instead of manually clicking around the AWS website to create resources, I write Python code that describes what I want. This code lives in Git, so it's version-controlled, reviewable, and repeatable. I use AWS CDK, which converts my Python code into CloudFormation templates that AWS uses to create the resources.

### "What is a Lambda function?"
> It's a small piece of code that runs in the cloud without me managing any servers. I just upload the code, and AWS runs it whenever I trigger it. I only pay for the time it actually runs — if nobody triggers it, it costs nothing.

### "What is the principle of least privilege?"
> It means giving each component only the minimum permissions it needs. My Lambda function can only read from its specific S3 bucket and publish to its specific SNS topic — nothing else. Even if the Lambda code gets compromised, the attacker can't access other AWS resources.

### "How does the CI/CD pipeline work?"
> When I manually trigger the GitHub Actions workflow, it checks out the code, installs dependencies, authenticates with AWS using OIDC (no stored passwords), and runs `cdk deploy` which creates or updates all the AWS resources.

### "What is OIDC and why did you use it?"
> OIDC is a way for GitHub to prove its identity to AWS without storing any passwords. When the workflow runs, GitHub gives it a temporary ID token. AWS verifies this token and gives back temporary credentials that expire in an hour. This is more secure than storing AWS access keys as secrets because there are no permanent credentials that could be leaked.

### "How did you test the Lambda function?"
> I have unit tests that mock the AWS services, so I can run them locally without any AWS account. I also have a manual invoke script that calls the real deployed Lambda and shows the response. And there's a test event JSON file for testing through the AWS console.

### "Walk me through what happens when the Lambda is invoked."
> The Lambda receives an event (any JSON), then it calls the S3 API to list all objects in the configured bucket. It builds a human-readable message with the timestamp, bucket name, object count, and details of each file. Then it publishes that message to the SNS topic, which sends it as an email. Finally, it returns a JSON response with a 200 status code and all the execution details.

### "What happens during `cdk deploy`?"
> CDK runs my Python code (`app.py`) to generate a CloudFormation template. Then it uploads the template and any assets (like the Lambda code zip) to a staging S3 bucket (created by `cdk bootstrap`). CloudFormation reads the template and creates/updates all the resources: S3 bucket, SNS topic, IAM role, Lambda function, and uploads the sample files.

### "What is `cdk bootstrap` and why is it needed?"
> Before CDK can deploy anything, it needs a place in your AWS account to store temporary files. `cdk bootstrap` creates a special S3 bucket and some IAM roles for this purpose. You only need to run it once per AWS account per region.

### "Why is the S3 bucket created with `RemovalPolicy.DESTROY`?"
> By default, AWS won't delete an S3 bucket when you tear down the stack — this is a safety measure to prevent accidental data loss. Setting `DESTROY` tells CloudFormation it's OK to delete the bucket. Combined with `auto_delete_objects=True`, CDK adds a helper that empties the bucket first, since AWS won't delete a bucket that still has files in it.
