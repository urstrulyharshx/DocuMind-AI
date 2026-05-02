import boto3

from app.core.config import Config


def get_boto3_session():
    """Returns a boto3 session configured for the app's AWS region."""
    return boto3.Session(region_name=Config.AWS_REGION)


def get_bedrock_client():
    """Returns a boto3 client for Bedrock when using boto3."""
    session = get_boto3_session()
    return session.client("bedrock-runtime")
