#!/usr/bin/env python3
"""
Deploy AI Referee infrastructure with KVS, MSK 3.8.x, and Flink 1.20
"""

import boto3
import json
import time

kvs = boto3.client('kinesisvideo', region_name='us-east-1')
msk = boto3.client('kafka', region_name='us-east-1')
kda = boto3.client('kinesisanalyticsv2', region_name='us-east-1')
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')

REGION = 'us-east-1'
ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']

def create_kvs_stream():
    """Create Kinesis Video Stream"""
    print("\n📹 Creating Kinesis Video Stream...")
    
    try:
        response = kvs.create_stream(
            StreamName='sports-security-video-stream',
            DataRetentionInHours=24,
            MediaType='video/h264',
            Tags={'Project': 'AI-Referee'}
        )
        print(f"✅ KVS Stream created: {response['StreamARN']}")
        return response['StreamARN']
    except kvs.exceptions.ResourceInUseException:
        print("✅ KVS Stream already exists")
        return None

def create_msk_cluster(vpc_id, subnet_ids, security_group_id):
    """Create MSK 3.8.x cluster"""
    print("\n📨 Creating MSK 3.8.x cluster...")
    
    try:
        response = msk.create_cluster(
            ClusterName='sports-security-msk-cluster',
            KafkaVersion='3.8.x',
            NumberOfBrokerNodes=3,
            BrokerNodeGroupInfo={
                'InstanceType': 'kafka.m5.large',
                'ClientSubnets': subnet_ids,
                'SecurityGroups': [security_group_id],
                'StorageInfo': {
                    'EbsStorageInfo': {'VolumeSize': 100}
                }
            },
            ClientAuthentication={
                'Sasl': {
                    'Iam': {'Enabled': True}
                }
            },
            EncryptionInfo={
                'EncryptionInTransit': {
                    'ClientBroker': 'TLS',
                    'InCluster': True
                }
            },
            Tags={'Project': 'AI-Referee'}
        )
        print(f"✅ MSK Cluster creating: {response['ClusterArn']}")
        return response['ClusterArn']
    except Exception as e:
        print(f"⚠️  MSK Cluster error: {e}")
        return None

def create_flink_app(msk_bootstrap_servers, kvs_stream_name, role_arn):
    """Create Managed Flink 1.20 application"""
    print("\n⚡ Creating Managed Flink 1.20 application...")
    
    try:
        response = kda.create_application(
            ApplicationName='sports-security-flink-app',
            RuntimeEnvironment='FLINK-1_20',
            ServiceExecutionRole=role_arn,
            ApplicationConfiguration={
                'EnvironmentProperties': {
                    'PropertyGroups': [{
                        'PropertyGroupId': 'ProducerConfigProperties',
                        'PropertyMap': {
                            'msk.bootstrap.servers': msk_bootstrap_servers,
                            'kvs.stream.name': kvs_stream_name
                        }
                    }]
                },
                'FlinkApplicationConfiguration': {
                    'CheckpointConfiguration': {
                        'ConfigurationType': 'DEFAULT'
                    },
                    'MonitoringConfiguration': {
                        'ConfigurationType': 'CUSTOM',
                        'LogLevel': 'INFO',
                        'MetricsLevel': 'APPLICATION'
                    },
                    'ParallelismConfiguration': {
                        'ConfigurationType': 'CUSTOM',
                        'Parallelism': 1,
                        'ParallelismPerKPU': 1,
                        'AutoScalingEnabled': False
                    }
                }
            },
            Tags=[{'Key': 'Project', 'Value': 'AI-Referee'}]
        )
        print(f"✅ Flink app created: {response['ApplicationDetail']['ApplicationARN']}")
        return response['ApplicationDetail']['ApplicationARN']
    except Exception as e:
        print(f"⚠️  Flink app error: {e}")
        return None

def create_dynamodb_table():
    """Create DynamoDB table for violations"""
    print("\n💾 Creating DynamoDB table...")
    
    try:
        response = dynamodb.create_table(
            TableName='sports-violations',
            KeySchema=[
                {'AttributeName': 'violation_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'violation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[{'Key': 'Project', 'Value': 'AI-Referee'}]
        )
        print(f"✅ DynamoDB table created")
        return response['TableDescription']['TableArn']
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ DynamoDB table already exists")
        return None

def create_s3_buckets():
    """Create S3 buckets for evidence and Flink code"""
    print("\n📦 Creating S3 buckets...")
    
    buckets = [
        f'sports-security-evidence-{ACCOUNT_ID}',
        f'sports-security-flink-code-{ACCOUNT_ID}'
    ]
    
    for bucket_name in buckets:
        try:
            s3.create_bucket(Bucket=bucket_name)
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            print(f"✅ Created bucket: {bucket_name}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"✅ Bucket already exists: {bucket_name}")

def create_sns_topic(email):
    """Create SNS topic for alerts"""
    print("\n📧 Creating SNS topic...")
    
    try:
        response = sns.create_topic(
            Name='sports-security-alerts',
            Tags=[{'Key': 'Project', 'Value': 'AI-Referee'}]
        )
        topic_arn = response['TopicArn']
        
        # Subscribe email
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"✅ SNS topic created: {topic_arn}")
        print(f"📧 Check {email} to confirm subscription")
        return topic_arn
    except Exception as e:
        print(f"⚠️  SNS error: {e}")
        return None

if __name__ == '__main__':
    print("🚀 Deploying AI Referee Infrastructure")
    print("=" * 60)
    
    # Note: VPC, subnets, and security groups should be created first
    # Use CloudFormation template for complete deployment
    
    print("\n⚠️  For complete deployment, use CloudFormation template:")
    print("   static/ai-referee-infrastructure-nested.yaml")
    print("\n   This script shows the individual service creation steps.")
