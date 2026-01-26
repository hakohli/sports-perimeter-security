#!/usr/bin/env python3
"""
Deploy sports perimeter security infrastructure
"""

import boto3
import json
import time

msk = boto3.client('kafka', region_name='us-east-1')
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

CLUSTER_NAME = 'sports-security-cluster'
REGION = 'us-east-1'

def create_s3_bucket():
    """Create S3 bucket for video evidence"""
    bucket_name = 'sports-security-evidence'
    
    print("\n📦 Creating S3 bucket...")
    
    try:
        s3.create_bucket(Bucket=bucket_name)
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Add lifecycle policy (delete after 30 days)
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [{
                    'Id': 'DeleteOldEvidence',
                    'Status': 'Enabled',
                    'Expiration': {'Days': 30}
                }]
            }
        )
        
        # Tag bucket
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={'TagSet': [
                {'Key': 'Project', 'Value': 'Sports-Security'},
                {'Key': 'NoDelete', 'Value': 'true'}
            ]}
        )
        
        print(f"✓ Created S3 bucket: {bucket_name}")
        return bucket_name
        
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ S3 bucket already exists: {bucket_name}")
        return bucket_name

def create_dynamodb_table():
    """Create DynamoDB table for violations"""
    table_name = 'sports-violations'
    
    print("\n💾 Creating DynamoDB table...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'violation_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'violation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'timestamp-index',
                'KeySchema': [
                    {'AttributeName': 'timestamp', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Project', 'Value': 'Sports-Security'},
                {'Key': 'NoDelete', 'Value': 'true'}
            ]
        )
        print(f"✓ Created DynamoDB table: {table_name}")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"✓ DynamoDB table already exists: {table_name}")

def create_sns_topic():
    """Create SNS topic for alerts"""
    topic_name = 'sports-security-alerts'
    
    print("\n📧 Creating SNS topic...")
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        
        sns.tag_resource(
            ResourceArn=topic_arn,
            Tags=[
                {'Key': 'Project', 'Value': 'Sports-Security'},
                {'Key': 'NoDelete', 'Value': 'true'}
            ]
        )
        
        print(f"✓ Created SNS topic: {topic_arn}")
        return topic_arn
    except Exception as e:
        print(f"✓ SNS topic exists: {e}")
        return None

def create_msk_cluster():
    """Create MSK cluster (reuse from anomaly detection if exists)"""
    print("\n📊 Checking MSK cluster...")
    
    try:
        clusters = msk.list_clusters()['ClusterInfoList']
        existing = [c for c in clusters if c['ClusterName'] == 'mcp-anomaly-cluster']
        
        if existing:
            cluster_arn = existing[0]['ClusterArn']
            print(f"✓ Using existing MSK cluster: {cluster_arn}")
            
            if existing[0]['State'] == 'ACTIVE':
                bootstrap = msk.get_bootstrap_brokers(ClusterArn=cluster_arn)
                return cluster_arn, bootstrap['BootstrapBrokerString']
            else:
                print(f"⏳ Cluster state: {existing[0]['State']}")
                return cluster_arn, None
        else:
            print("⚠️  No MSK cluster found. Run anomaly detection deployment first.")
            return None, None
            
    except Exception as e:
        print(f"✗ Error checking MSK: {e}")
        return None, None

def main():
    """Deploy complete solution"""
    print("=" * 60)
    print("Sports Perimeter Security - Deployment")
    print("=" * 60)
    
    # Step 1: S3 bucket
    bucket = create_s3_bucket()
    
    # Step 2: DynamoDB
    create_dynamodb_table()
    
    # Step 3: SNS
    topic_arn = create_sns_topic()
    
    # Step 4: MSK (reuse existing)
    cluster_arn, bootstrap_servers = create_msk_cluster()
    
    print("\n" + "=" * 60)
    print("✓ Deployment Complete!")
    print("=" * 60)
    print(f"\nS3 Bucket: {bucket}")
    print(f"DynamoDB Table: sports-violations")
    print(f"SNS Topic: {topic_arn}")
    
    if bootstrap_servers:
        print(f"MSK Bootstrap: {bootstrap_servers}")
    else:
        print("MSK: Waiting for cluster to be ACTIVE")
    
    print("\n📝 Next Steps:")
    print("1. Subscribe to SNS topic for alerts")
    print("2. Create Kafka topics: game-frames, violations")
    print("3. Start security agent: python security_agent.py <bootstrap> baseball")
    print("4. Extract frames: python frame_extractor.py <bootstrap> video.mp4 30")
    print("5. Monitor violations in DynamoDB")

if __name__ == "__main__":
    main()
