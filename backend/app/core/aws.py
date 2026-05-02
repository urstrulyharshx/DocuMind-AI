# AWS initialization and configuration utilities
import os
from dotenv import load_dotenv

import boto3

# Load environment variables (if not already loaded)
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_BEDROCK_API_KEY = os.getenv("AWS_BEDROCK_API_KEY")

def get_boto3_session():
	"""Returns a boto3 session configured for the app's AWS region."""
	return boto3.Session(region_name=AWS_REGION)

def get_bedrock_client():
	"""Returns a boto3 client for Bedrock (if using boto3)."""
	session = get_boto3_session()
	return session.client("bedrock-runtime")

# Add other AWS resource initializations here as needed
