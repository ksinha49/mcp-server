---
name: ameritas-cloudformation
description: |
  Ameritas-specific CloudFormation and SAM template generation, editing, and standardization skill. 
  Use when: (1) Creating new CloudFormation or SAM templates, (2) Reviewing or refactoring existing templates, 
  (3) Adding new resources to existing stacks, (4) Generating infrastructure for Lambda, Step Functions, 
  SQS, SNS, DynamoDB, EventBridge, EC2, ALB, or Auto Scaling, (5) Ensuring naming convention compliance,
  (6) Creating nested stacks or parent templates. Follows Ameritas cloud naming standards and architectural patterns.
---

# Ameritas CloudFormation & SAM Template Skill

Generate CloudFormation and SAM templates following Ameritas enterprise standards, naming conventions, and architectural patterns.

## Quick Reference

### Template Selection
- **SAM templates**: Lambda functions, Step Functions, API Gateway, event-driven architectures
- **CloudFormation templates**: EC2, ALB, Auto Scaling, VPC, pure infrastructure

### Required Template Header

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31  # Only for SAM templates
Description: |
  Brief description of stack purpose.
  Managed by: Team/Owner Name
```

## Naming Convention Standards

All resources follow pattern: `${AWSAccountName}-${AWS::StackName}-{resource-purpose}`

### Environment Codes
| Code | Environment |
|------|-------------|
| `d` | Development |
| `t` | Test |
| `m` | Model/UAT |
| `p` | Production |

### Resource Naming Patterns

| Resource | Pattern | Example |
|----------|---------|---------|
| Lambda | `${AWSAccountName}-${AWS::StackName}-{function-purpose}` | `alic-aio-m-mystack-email-parser` |
| Step Function | `${AWSAccountName}-${AWS::StackName}-{workflow}-sm` | `alic-aio-m-mystack-file-process-sm` |
| SQS Queue | `${AWSAccountName}-${AWS::StackName}-{purpose}-queue` | `alic-aio-m-mystack-email-queue.fifo` |
| SQS DLQ | `${AWSAccountName}-${AWS::StackName}-{purpose}-dlq` | `alic-aio-m-mystack-email-dlq` |
| SNS Topic | `${AWSAccountName}-${AWS::StackName}-{purpose}-topic` | `alic-aio-m-mystack-notify-topic` |
| EventBridge Rule | `${AWSAccountName}-${AWS::StackName}-{trigger}-rule` | `alic-aio-m-mystack-s3-event-rule` |
| DynamoDB Table | `${AWSAccountName}-${AWS::StackName}-{entity}-table` | `alic-aio-m-mystack-audit-table` |
| CloudWatch Alarm | `${AWSAccountName}-${AWS::StackName}-{metric}-alarm` | `alic-aio-m-mystack-failure-alarm` |
| Lambda Layer | `${AWSAccountName}-${AWS::StackName}-{lib}-layer` | `alic-aio-m-mystack-pandas-layer` |
| Target Group | `${AWS::StackName}-{service}-tg` | `mystack-ollama-tg` |
| Load Balancer | `${AWS::StackName}-{service}-lb` | `mystack-openwebui-lb` |
| Auto Scaling Group | `${AWS::StackName}-{service}-asg` | `mystack-ollama-asg` |
| Launch Template | `${AWS::StackName}-{service}-launch-template` | `mystack-ollama-launch-template` |

## Standard Parameters Block

Always include these base parameters for SAM templates:

```yaml
Parameters:
  AWSAccountName:
    Type: String
    Description: AWS Account Name for resource naming
  
  EnvironmentName:
    Type: String
    Description: Environment name (development, test, model, production)
    AllowedValues:
      - development
      - test
      - model
      - production
  
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
  
  LambdaIAMRoleARN:
    Type: String
    Description: IAM Role ARN for Lambda functions
  
  EventBridgeIAMRoleARN:
    Type: String
    Description: IAM Role ARN for EventBridge rules
  
  FileProcessingStepFunctionIAMRole:
    Type: String
    Description: IAM role ARN for Step Functions
```

### EFS Parameters (when needed)
```yaml
  EFSBasePath:
    Type: String
    Description: Base path in EFS to use for this project
  
  MyEfsAccessPointArn:
    Type: String
    Description: ARN of the EFS Access Point
```

### S3 Bucket Parameters
```yaml
  InputS3BucketName:
    Type: String
    Description: S3 bucket for input files
  
  OutputS3BucketName:
    Type: String
    Description: S3 bucket for output files
```

## SAM Globals Block

Standard globals for serverless applications:

```yaml
Globals:
  Function:
    Tracing: Active
    Runtime: python3.12
    Architectures:
      - x86_64
    LoggingConfig:
      LogFormat: JSON
```

## Resource Templates

### Lambda Function (Standard)

```yaml
  MyLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub ${AWSAccountName}-${AWS::StackName}-my-function
      Handler: app.lambda_handler
      Runtime: python3.12
      CodeUri: s3://deployment-bucket/code-hash
      Role: !Ref LambdaIAMRoleARN
      MemorySize: 1024
      Timeout: 300
      EphemeralStorage:
        Size: 512
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
          AWS_ENV_NAME: !Ref EnvironmentName
      FileSystemConfigs:  # Include only if EFS needed
        - Arn: !Ref MyEfsAccessPointArn
          LocalMountPath: /mnt/efs
    Metadata:
      SamResourceId: MyLambdaFunction
```

### Lambda with SQS Trigger

```yaml
  SQSTriggeredLambda:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub ${AWSAccountName}-${AWS::StackName}-sqs-processor
      Handler: app.lambda_handler
      Runtime: python3.12
      CodeUri: s3://deployment-bucket/code-hash
      Role: !Ref LambdaIAMRoleARN
      MemorySize: 1024
      Timeout: 60
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
          AWS_ENV_NAME: !Ref EnvironmentName
      Events:
        SQSTrigger:
          Type: SQS
          Properties:
            Queue: !GetAtt MyInputQueue.Arn
            BatchSize: 1
    Metadata:
      SamResourceId: SQSTriggeredLambda
```

### Lambda Layer

```yaml
  MyLambdaLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub ${AWSAccountName}-${AWS::StackName}-my-layer
      Description: Layer description
      ContentUri: s3://deployment-bucket/layer-hash
      RetentionPolicy: Delete
      CompatibleRuntimes:
        - python3.12
        - python3.13
    Metadata:
      SamResourceId: MyLambdaLayer
```

### SQS Queue (FIFO)

```yaml
  MyFifoQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub ${AWSAccountName}-${AWS::StackName}-input-queue.fifo
      FifoQueue: true
      ContentBasedDeduplication: true
      VisibilityTimeout: 300
    Metadata:
      SamResourceId: MyFifoQueue
```

### SQS Queue (Standard with DLQ)

```yaml
  MyStandardQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub ${AWSAccountName}-${AWS::StackName}-input-queue
      VisibilityTimeout: 720
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt MyDeadLetterQueue.Arn
        maxReceiveCount: 3
    Metadata:
      SamResourceId: MyStandardQueue

  MyDeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub ${AWSAccountName}-${AWS::StackName}-sqs-dlq
    Metadata:
      SamResourceId: MyDeadLetterQueue
```

### EventBridge Rule (S3 Trigger)

```yaml
  S3EventRule:
    Type: AWS::Events::Rule
    Properties:
      Name: !Sub ${AWSAccountName}-${AWS::StackName}-s3-event-rule
      EventPattern:
        source:
          - aws.s3
        detail-type:
          - Object Created
        detail:
          bucket:
            name:
              - !Ref InputS3BucketName
          object:
            key:
              - prefix: raw/my-prefix/
      Targets:
        - Arn: !GetAtt MyInputQueue.Arn
          Id: MyInputQueueTarget
          RoleArn: !Ref EventBridgeIAMRoleARN
          DeadLetterConfig:
            Arn: !GetAtt MyEventBridgeDLQ.Arn
          SqsParameters:
            MessageGroupId: !Sub ${AWSAccountName}-${AWS::StackName}-msg-id
    Metadata:
      SamResourceId: S3EventRule
```

### EventBridge Rule (Schedule)

```yaml
  ScheduledRule:
    Type: AWS::Events::Rule
    Properties:
      Name: !Sub ${AWSAccountName}-${AWS::StackName}-schedule-rule
      Description: Triggers Lambda on schedule
      ScheduleExpression: cron(0 0 10 1 ? *)  # Jan 10 at midnight UTC
      State: ENABLED
      Targets:
        - Arn: !GetAtt MyLambdaFunction.Arn
          Id: MyLambdaTarget
          RoleArn: !Ref EventBridgeIAMRoleARN
    Metadata:
      SamResourceId: ScheduledRule
```

### SNS Topic

```yaml
  NotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub ${AWSAccountName}-${AWS::StackName}-notify-topic
      Subscription:
        - Endpoint: team-email@ameritas.com
          Protocol: email
    Metadata:
      SamResourceId: NotificationTopic

  ErrorNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub ${AWSAccountName}-${AWS::StackName}-err-topic
      Subscription:
        - Endpoint: team-email@ameritas.com
          Protocol: email
    Metadata:
      SamResourceId: ErrorNotificationTopic
```

### DynamoDB Table

```yaml
  AuditTable:
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
      SamResourceId: AuditTable
```

### CloudWatch Alarm

```yaml
  WorkflowFailureAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${AWSAccountName}-${AWS::StackName}-failure-alarm
      AlarmDescription: Monitors State Machine for execution failures
      MetricName: ExecutionsFailed
      Namespace: AWS/States
      Dimensions:
        - Name: StateMachineArn
          Value: !Ref MyStateMachine
      Statistic: Sum
      Period: 60
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      AlarmActions:
        - !Ref ErrorNotificationTopic
    Metadata:
      SamResourceId: WorkflowFailureAlarm
```

### Step Function State Machine

```yaml
  MyStateMachine:
    Type: AWS::Serverless::StateMachine
    Properties:
      Name: !Sub ${AWSAccountName}-${AWS::StackName}-workflow-sm
      Tracing:
        Enabled: true
      Definition:
        StartAt: FirstStep
        TimeoutSeconds: 14400
        States:
          FirstStep:
            Type: Task
            Resource: !GetAtt FirstLambda.Arn
            InputPath: $
            ResultPath: $.first_output
            Next: SecondStep
            Retry:
              - ErrorEquals:
                  - States.ALL
                IntervalSeconds: 2
                MaxAttempts: 3
                BackoffRate: 2
                JitterStrategy: FULL
            Catch:
              - ErrorEquals:
                  - States.ALL
                ResultPath: $.error_info
                Next: NotifyError
          SecondStep:
            Type: Task
            Resource: !GetAtt SecondLambda.Arn
            Next: NotifySuccess
            Retry:
              - ErrorEquals:
                  - States.ALL
                IntervalSeconds: 2
                MaxAttempts: 3
                BackoffRate: 2
                JitterStrategy: FULL
            Catch:
              - ErrorEquals:
                  - States.ALL
                ResultPath: $.error_info
                Next: NotifyError
          NotifySuccess:
            Type: Task
            Resource: arn:aws:states:::sns:publish
            Parameters:
              TopicArn: !Ref NotificationTopic
              Subject: Workflow Completed Successfully
              Message.$: States.Format('Workflow completed. Result: {}', $.second_output)
            Next: WorkflowSuccess
          WorkflowSuccess:
            Type: Succeed
          NotifyError:
            Type: Task
            Resource: arn:aws:states:::sns:publish
            Parameters:
              TopicArn: !Ref ErrorNotificationTopic
              Subject: Workflow Error
              Message.$: States.Format('Error occurred: {}', $.error_info)
            Next: WorkflowFailure
          WorkflowFailure:
            Type: Fail
            Error: WorkflowFailed
            Cause: Workflow execution failed
      Role: !Ref FileProcessingStepFunctionIAMRole
    Metadata:
      SamResourceId: MyStateMachine
```

## EC2 & Auto Scaling Patterns

See [EC2_PATTERNS.md](EC2_PATTERNS.md) for complete EC2, ALB, and Auto Scaling resource patterns.

## Nested Stack Patterns

See [NESTED_STACKS.md](NESTED_STACKS.md) for parent-child stack organization patterns.

## Step Function Workflow Patterns

See [STEPFUNCTION_PATTERNS.md](STEPFUNCTION_PATTERNS.md) for advanced workflow patterns including:
- Parallel execution
- Map states
- Choice states
- Error handling

## Critical Rules

### Always Include
1. `Metadata.SamResourceId` on every SAM resource
2. `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain` on stateful resources (DynamoDB, S3)
3. VPC configuration on all Lambda functions
4. Retry policies with `JitterStrategy: FULL` on Step Function tasks
5. Dead letter queues for SQS and EventBridge
6. CloudWatch alarms for critical state machines

### Never Do
1. Hardcode account IDs, ARNs, or bucket names
2. Use underscores in resource names (use hyphens)
3. Skip error handling in Step Functions
4. Omit tracing configuration on Lambda and Step Functions
5. Create Lambda functions without VPC configuration
6. Use inline Lambda code (always use CodeUri to S3)

### Timeout Guidelines
| Resource | Recommended Timeout |
|----------|---------------------|
| Simple Lambda | 60-180 seconds |
| Processing Lambda | 300-600 seconds |
| Heavy Processing Lambda | 720-900 seconds |
| SQS Visibility (match Lambda) | Lambda timeout + buffer |
| Step Function | 14400 seconds (4 hours) |

### Memory Guidelines
| Workload | MemorySize | EphemeralStorage |
|----------|------------|------------------|
| Light processing | 512-1024 | 512 |
| Standard processing | 1024-2048 | 1024 |
| Heavy processing | 2048-3008 | 2048-4096 |

## Outputs Section

Always include outputs for cross-stack references:

```yaml
Outputs:
  StateMachineArn:
    Description: ARN of the State Machine
    Value: !Ref MyStateMachine
  
  QueueUrl:
    Description: URL of the input queue
    Value: !Ref MyInputQueue
  
  TopicArn:
    Description: ARN of notification topic
    Value: !Ref NotificationTopic
```
