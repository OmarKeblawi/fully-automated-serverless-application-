import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iam as iam,
    aws_lambda as _lambda,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class ServerlessStack(Stack):
    """
    CDK Stack that provisions:
      - S3 bucket (with sample file upload)
      - SNS topic + email subscription
      - Least-privilege IAM role
      - Python Lambda (list S3 objects → publish SNS)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        notification_email = self.node.try_get_context("notification_email") or os.environ.get(
            "NOTIFICATION_EMAIL", "your-email@example.com"
        )

        # ── S3 Bucket ────────────────────────────────────────────────────────
        bucket = s3.Bucket(
            self,
            "SampleBucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # Upload sample_files/ directory contents to the bucket on every deploy
        s3deploy.BucketDeployment(
            self,
            "DeploySampleFiles",
            sources=[s3deploy.Source.asset("sample_files")],
            destination_bucket=bucket,
            destination_key_prefix="sample_files/",
        )

        # ── SNS Topic + Email Subscription ───────────────────────────────────
        topic = sns.Topic(
            self,
            "NotificationTopic",
            display_name="Serverless App Notifications",
            topic_name="serverless-app-notifications",
        )

        topic.add_subscription(
            subscriptions.EmailSubscription(notification_email)
        )

        # ── IAM Role for Lambda (least-privilege) ────────────────────────────
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Least-privilege role for the serverless Lambda function",
        )

        # Allow Lambda to write logs
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # S3 read-only on the specific bucket
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3ReadAccess",
                effect=iam.Effect.ALLOW,
                actions=["s3:ListBucket", "s3:GetObject"],
                resources=[bucket.bucket_arn, f"{bucket.bucket_arn}/*"],
            )
        )

        # SNS publish on the specific topic
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="SNSPublishAccess",
                effect=iam.Effect.ALLOW,
                actions=["sns:Publish"],
                resources=[topic.topic_arn],
            )
        )

        # ── Lambda Function ───────────────────────────────────────────────────
        handler = _lambda.Function(
            self,
            "ServerlessHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "SNS_TOPIC_ARN": topic.topic_arn,
            },
            description="Lists S3 objects and publishes SNS notifications",
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "BucketName", value=bucket.bucket_name, description="S3 Bucket name")
        cdk.CfnOutput(self, "TopicArn", value=topic.topic_arn, description="SNS Topic ARN")
        cdk.CfnOutput(
            self,
            "LambdaFunctionName",
            value=handler.function_name,
            description="Lambda function name",
        )
        cdk.CfnOutput(
            self,
            "LambdaFunctionArn",
            value=handler.function_arn,
            description="Lambda function ARN",
        )
