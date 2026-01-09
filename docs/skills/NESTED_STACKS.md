# Nested Stack Patterns

Patterns for organizing CloudFormation stacks with parent-child relationships.

## Parent Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Parent SAM template that includes individual service stacks.

Parameters:
  # Common parameters shared across all child stacks
  AWSAccountName:
    Description: AWS account name for resource naming
    Type: String

  ApplicationName:
    Description: Application name
    Type: String
    Default: myapp-services

  AWSAccountShortName:
    Description: Short account name (without alic prefix)
    Type: String

  Environment:
    Description: Technical environment
    Type: String
    AllowedValues:
      - development
      - test
      - model
      - production

  # Networking parameters
  LambdaSubnet1ID:
    Type: String
    Description: Subnet ID for Lambda function

  LambdaSubnet2ID:
    Type: String
    Description: Subnet ID for Lambda function

  LambdaSecurityGroupID1:
    Type: String
    Description: Security Group ID for Lambda functions

  LambdaSecurityGroupID2:
    Type: String
    Description: Security Group ID for Lambda functions

  # IAM parameters
  LambdaIAMRoleARN:
    Type: String
    Description: IAM Role ARN for Lambda functions

  EventBridgeIAMRoleARN:
    Type: String
    Description: ARN of IAM role for EventBridge

  FileProcessingStepFunctionIAMRole:
    Type: String
    Description: IAM role ARN for Step Functions

  # Storage parameters
  FileProcessingEfsAccessPointArn:
    Type: String
    Description: ARN of EFS access point

  PrimaryS3BucketName:
    Type: String
    Description: S3 bucket for primary storage

  # Service-specific parameters
  DocumentAuditTableName:
    Type: String
    Description: DynamoDB table for document audit

  NotificationEmailId:
    Type: String
    Description: Email for notifications
    Default: ''

Resources:
  # Shared resources created by parent
  DocumentAuditTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Properties:
      TableName: !Ref DocumentAuditTableName
      AttributeDefinitions:
        - AttributeName: document_id
          AttributeType: S
      KeySchema:
        - AttributeName: document_id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST
    Metadata:
      SamResourceId: DocumentAuditTable

  SharedQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub ${AWSAccountName}-${ApplicationName}-shared-queue.fifo
      FifoQueue: true
      ContentBasedDeduplication: true
      VisibilityTimeout: 90
    Metadata:
      SamResourceId: SharedQueue

  # Child stack: Service A
  ServiceA:
    Type: AWS::Serverless::Application
    Properties:
      Location: https://s3.us-east-2.amazonaws.com/deployment-bucket/service-a-template.yaml
      Parameters:
        AWSAccountName: !Ref AWSAccountName
        AWSAccountShortName: !Ref AWSAccountShortName
        Environment: !Ref Environment
        LambdaSubnet1ID: !Ref LambdaSubnet1ID
        LambdaSubnet2ID: !Ref LambdaSubnet2ID
        LambdaSecurityGroupID1: !Ref LambdaSecurityGroupID1
        LambdaSecurityGroupID2: !Ref LambdaSecurityGroupID2
        LambdaIAMRoleARN: !Ref LambdaIAMRoleARN
        EventBridgeIAMRoleARN: !Ref EventBridgeIAMRoleARN
        FileProcessingEfsAccessPointArn: !Ref FileProcessingEfsAccessPointArn
        PrimaryS3BucketName: !Ref PrimaryS3BucketName
        DocumentAuditTableName: !Ref DocumentAuditTableName
    Metadata:
      SamResourceId: ServiceA

  # Child stack: Service B
  ServiceB:
    Type: AWS::Serverless::Application
    Properties:
      Location: https://s3.us-east-2.amazonaws.com/deployment-bucket/service-b-template.yaml
      Parameters:
        AWSAccountName: !Ref AWSAccountName
        AWSAccountShortName: !Ref AWSAccountShortName
        Environment: !Ref Environment
        LambdaSubnet1ID: !Ref LambdaSubnet1ID
        LambdaSubnet2ID: !Ref LambdaSubnet2ID
        LambdaSecurityGroupID1: !Ref LambdaSecurityGroupID1
        LambdaSecurityGroupID2: !Ref LambdaSecurityGroupID2
        LambdaIAMRoleARN: !Ref LambdaIAMRoleARN
        FileProcessingStepFunctionIAMRole: !Ref FileProcessingStepFunctionIAMRole
        FileProcessingEfsAccessPointArn: !Ref FileProcessingEfsAccessPointArn
        SharedQueueUrl: !Ref SharedQueue
    Metadata:
      SamResourceId: ServiceB

  # Child stack: Service C (depends on Service A output)
  ServiceC:
    Type: AWS::Serverless::Application
    DependsOn: ServiceA
    Properties:
      Location: https://s3.us-east-2.amazonaws.com/deployment-bucket/service-c-template.yaml
      Parameters:
        AWSAccountName: !Ref AWSAccountName
        Environment: !Ref Environment
        LambdaSubnet1ID: !Ref LambdaSubnet1ID
        LambdaSubnet2ID: !Ref LambdaSubnet2ID
        LambdaSecurityGroupID1: !Ref LambdaSecurityGroupID1
        LambdaSecurityGroupID2: !Ref LambdaSecurityGroupID2
        LambdaIAMRoleARN: !Ref LambdaIAMRoleARN
        # Reference output from ServiceA
        ServiceAFunctionArn: !GetAtt ServiceA.Outputs.ProcessingFunctionArn
    Metadata:
      SamResourceId: ServiceC

Outputs:
  SharedQueueUrl:
    Description: URL of the shared SQS queue
    Value: !Ref SharedQueue

  DocumentAuditTableName:
    Description: Name of the document audit table
    Value: !Ref DocumentAuditTable
```

## Child Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Child service template for Service A

Globals:
  Function:
    Tracing: Active
    Runtime: python3.12
    Architectures:
      - x86_64
    LoggingConfig:
      LogFormat: JSON

Parameters:
  # Inherited from parent
  AWSAccountName:
    Type: String
    Description: AWS Account Name

  AWSAccountShortName:
    Type: String
    Description: Short account name

  Environment:
    Type: String
    Description: Environment name

  LambdaSubnet1ID:
    Type: String
    Description: Subnet ID for Lambda

  LambdaSubnet2ID:
    Type: String
    Description: Subnet ID for Lambda

  LambdaSecurityGroupID1:
    Type: String
    Description: Security Group ID

  LambdaSecurityGroupID2:
    Type: String
    Description: Security Group ID

  LambdaIAMRoleARN:
    Type: String
    Description: IAM Role ARN for Lambda

  EventBridgeIAMRoleARN:
    Type: String
    Description: IAM Role ARN for EventBridge

  FileProcessingEfsAccessPointArn:
    Type: String
    Description: EFS Access Point ARN

  PrimaryS3BucketName:
    Type: String
    Description: Primary S3 bucket

  DocumentAuditTableName:
    Type: String
    Description: Audit table name

Resources:
  # Service-specific resources
  ServiceAFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub ${AWSAccountName}-${AWS::StackName}-processor
      Handler: app.lambda_handler
      Runtime: python3.12
      CodeUri: s3://deployment-bucket/code-hash
      Role: !Ref LambdaIAMRoleARN
      MemorySize: 1024
      Timeout: 300
      VpcConfig:
        SecurityGroupIds:
          - !Ref LambdaSecurityGroupID1
          - !Ref LambdaSecurityGroupID2
        SubnetIds:
          - !Ref LambdaSubnet1ID
          - !Ref LambdaSubnet2ID
      Environment:
        Variables:
          AWS_ACCOUNT_NAME: !Ref AWSAccountName
          AWS_ENV_NAME: !Ref Environment
          S3_BUCKET: !Ref PrimaryS3BucketName
          AUDIT_TABLE: !Ref DocumentAuditTableName
      FileSystemConfigs:
        - Arn: !Ref FileProcessingEfsAccessPointArn
          LocalMountPath: /mnt/efs
    Metadata:
      SamResourceId: ServiceAFunction

  ServiceAQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub ${AWSAccountName}-${AWS::StackName}-input-queue.fifo
      FifoQueue: true
      ContentBasedDeduplication: true
      VisibilityTimeout: 360
    Metadata:
      SamResourceId: ServiceAQueue

  ServiceAEventRule:
    Type: AWS::Events::Rule
    Properties:
      Name: !Sub ${AWSAccountName}-${AWS::StackName}-s3-trigger
      EventPattern:
        source:
          - aws.s3
        detail-type:
          - Object Created
        detail:
          bucket:
            name:
              - !Ref PrimaryS3BucketName
          object:
            key:
              - prefix: raw/service-a/
      Targets:
        - Arn: !GetAtt ServiceAQueue.Arn
          Id: ServiceAQueueTarget
          RoleArn: !Ref EventBridgeIAMRoleARN
          SqsParameters:
            MessageGroupId: !Sub ${AWSAccountName}-${AWS::StackName}-msg-id
    Metadata:
      SamResourceId: ServiceAEventRule

Outputs:
  ProcessingFunctionArn:
    Description: ARN of the processing function
    Value: !GetAtt ServiceAFunction.Arn

  QueueUrl:
    Description: URL of the service queue
    Value: !Ref ServiceAQueue
```

## Best Practices for Nested Stacks

### Parameter Organization

Group parameters by category in parent template:

```yaml
Parameters:
  # === Account & Environment ===
  AWSAccountName:
    Type: String
  Environment:
    Type: String

  # === Networking ===
  LambdaSubnet1ID:
    Type: String
  LambdaSubnet2ID:
    Type: String
  LambdaSecurityGroupID1:
    Type: String
  LambdaSecurityGroupID2:
    Type: String

  # === IAM ===
  LambdaIAMRoleARN:
    Type: String
  EventBridgeIAMRoleARN:
    Type: String
  FileProcessingStepFunctionIAMRole:
    Type: String

  # === Storage ===
  FileProcessingEfsAccessPointArn:
    Type: String
  PrimaryS3BucketName:
    Type: String

  # === Service-Specific ===
  DocumentAuditTableName:
    Type: String
```

### Cross-Stack References

Use `!GetAtt` to reference outputs from nested stacks:

```yaml
# In parent template
ServiceB:
  Type: AWS::Serverless::Application
  Properties:
    Parameters:
      ServiceAQueueArn: !GetAtt ServiceA.Outputs.QueueArn
```

### Dependency Management

Use `DependsOn` for explicit ordering:

```yaml
ServiceC:
  Type: AWS::Serverless::Application
  DependsOn:
    - ServiceA
    - ServiceB
  Properties:
    Location: ...
```

### Conditional Child Stacks

```yaml
Conditions:
  CreateServiceC: !Equals [!Ref Environment, 'production']

Resources:
  ServiceC:
    Type: AWS::Serverless::Application
    Condition: CreateServiceC
    Properties:
      Location: ...
```

### Template Location Pattern

Store templates in S3 with version hashes:

```yaml
Location: https://s3.us-east-2.amazonaws.com/alic-aio-m-github-deploy/abc123def456.template
```

## Stack Organization Guidelines

### When to Use Nested Stacks

1. **Service boundaries**: Each microservice or domain gets its own child stack
2. **Team ownership**: Different teams own different child stacks
3. **Deployment independence**: Services that deploy at different frequencies
4. **Resource limits**: Approaching CloudFormation resource limits (~500 resources)

### Parent Stack Responsibilities

- Shared infrastructure (DynamoDB tables, SQS queues used by multiple services)
- Cross-service IAM roles
- VPC and networking resources
- Parameter aggregation and distribution

### Child Stack Responsibilities

- Service-specific Lambda functions
- Service-specific Step Functions
- Service-specific EventBridge rules
- Service-specific SNS topics
- Service-specific CloudWatch alarms

### Naming Convention for Nested Stacks

| Level | Pattern | Example |
|-------|---------|---------|
| Parent | `{app}-parent` | `aicoe-aiservices-parent` |
| Child | `{app}-{service}` | `aicoe-aiservices-idp` |
| Child | `{app}-{service}` | `aicoe-aiservices-email-parser` |
| Child | `{app}-{service}` | `aicoe-aiservices-summarization` |

### Resource Sharing Patterns

**Shared via Parent Output:**
```yaml
# Parent creates and exports
Outputs:
  SharedTableArn:
    Value: !GetAtt SharedTable.Arn
    Export:
      Name: !Sub ${AWS::StackName}-SharedTableArn
```

**Child imports:**
```yaml
# Child references export
Environment:
  Variables:
    TABLE_ARN: !ImportValue parent-stack-SharedTableArn
```

**Or pass as parameter:**
```yaml
# Parent passes to child
ChildStack:
  Parameters:
    SharedTableArn: !GetAtt SharedTable.Arn
```
