# Step Function Workflow Patterns

Advanced patterns for AWS Step Functions state machine definitions.

## Standard State Machine Structure

```yaml
  MyStateMachine:
    Type: AWS::Serverless::StateMachine
    Properties:
      Name: !Sub ${AWSAccountName}-${AWS::StackName}-workflow-sm
      Tracing:
        Enabled: true
      Definition:
        StartAt: FirstState
        TimeoutSeconds: 14400  # 4 hours default
        States:
          # State definitions here
      Role: !Ref FileProcessingStepFunctionIAMRole
    Metadata:
      SamResourceId: MyStateMachine
```

## Standard Retry Configuration

Always use this retry block for Task states:

```yaml
Retry:
  - ErrorEquals:
      - States.ALL
    IntervalSeconds: 2
    MaxAttempts: 3
    BackoffRate: 2
    JitterStrategy: FULL
```

For Lambda-specific errors, use expanded retries:

```yaml
Retry:
  - ErrorEquals:
      - Lambda.ServiceException
      - Lambda.AWSLambdaException
      - Lambda.SdkClientException
      - Lambda.TooManyRequestsException
    IntervalSeconds: 1
    MaxAttempts: 3
    BackoffRate: 2
    JitterStrategy: FULL
  - ErrorEquals:
      - States.ALL
    IntervalSeconds: 2
    MaxAttempts: 3
    BackoffRate: 2
    JitterStrategy: FULL
```

## Standard Error Handling Pattern

Every workflow should have error notification:

```yaml
States:
  ProcessingTask:
    Type: Task
    Resource: !GetAtt ProcessingLambda.Arn
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
      Message.$: States.Format('Workflow completed. Output: {}', $.processing_output)
    Next: WorkflowSuccess

  WorkflowSuccess:
    Type: Succeed

  NotifyError:
    Type: Task
    Resource: arn:aws:states:::sns:publish
    Parameters:
      TopicArn: !Ref ErrorNotificationTopic
      Subject: Workflow Error Notification
      Message.$: States.Format('Error occurred in workflow. Error: {}', $.error_info)
    Next: WorkflowFailure

  WorkflowFailure:
    Type: Fail
    Error: WorkflowFailed
    Cause: Workflow execution failed
```

## Sequential Processing Pattern

For workflows that process steps in sequence:

```yaml
Definition:
  StartAt: ExtractMetadata
  TimeoutSeconds: 14400
  States:
    ExtractMetadata:
      Type: Task
      Resource: !GetAtt ExtractMetadataLambda.Arn
      InputPath: $
      ResultPath: $.metadata_output
      Next: ProcessContent
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

    ProcessContent:
      Type: Task
      Resource: !GetAtt ProcessContentLambda.Arn
      Parameters:
        bucket.$: $.bucket
        file_key.$: $.metadata_output.file_key
        metadata.$: $.metadata_output.metadata
      ResultPath: $.processing_output
      Next: GenerateReport
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

    GenerateReport:
      Type: Task
      Resource: !GetAtt GenerateReportLambda.Arn
      Parameters:
        bucket.$: $.bucket
        processing_result.$: $.processing_output
        metadata.$: $.metadata_output
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
```

## Parallel Processing Pattern

For executing multiple tasks simultaneously:

```yaml
Definition:
  StartAt: ExtractMetadata
  TimeoutSeconds: 14400
  States:
    ExtractMetadata:
      Type: Task
      Resource: !GetAtt ExtractMetadataLambda.Arn
      ResultPath: $.metadata_output
      Next: ParallelProcessing
      Catch:
        - ErrorEquals:
            - States.ALL
          ResultPath: $.error_info
          Next: NotifyError

    ParallelProcessing:
      Type: Parallel
      Branches:
        - StartAt: ProcessTypeA
          States:
            ProcessTypeA:
              Type: Task
              Resource: !GetAtt ProcessTypeALambda.Arn
              Parameters:
                bucket.$: $.bucket
                input.$: $.metadata_output.type_a_input
              End: true
              Retry:
                - ErrorEquals:
                    - States.ALL
                  IntervalSeconds: 2
                  MaxAttempts: 3
                  BackoffRate: 2
                  JitterStrategy: FULL

        - StartAt: ProcessTypeB
          States:
            ProcessTypeB:
              Type: Task
              Resource: !GetAtt ProcessTypeBLambda.Arn
              Parameters:
                bucket.$: $.bucket
                input.$: $.metadata_output.type_b_input
              End: true
              Retry:
                - ErrorEquals:
                    - States.ALL
                  IntervalSeconds: 2
                  MaxAttempts: 3
                  BackoffRate: 2
                  JitterStrategy: FULL
      Next: MergeResults
      Catch:
        - ErrorEquals:
            - States.ALL
          ResultPath: $.error_info
          Next: NotifyError

    MergeResults:
      Type: Pass
      ResultPath: $
      Next: GenerateReport
```

## Map State Pattern (Batch Processing)

For processing arrays of items:

```yaml
Definition:
  StartAt: ExtractItems
  TimeoutSeconds: 16200
  States:
    ExtractItems:
      Type: Task
      Resource: !GetAtt ExtractItemsLambda.Arn
      ResultPath: $
      Next: ProcessAllItems
      Catch:
        - ErrorEquals:
            - States.ALL
          ResultPath: $.error_info
          Next: NotifyError

    ProcessAllItems:
      Type: Map
      ItemsPath: $.items
      ResultPath: $.processed_items
      MaxConcurrency: 5
      Iterator:
        StartAt: ProcessSingleItem
        States:
          ProcessSingleItem:
            Type: Task
            Resource: arn:aws:states:::states:startExecution.sync
            Parameters:
              StateMachineArn: !GetAtt ItemProcessingStateMachine.Arn
              Input.$: $
            ResultPath: $.item_result
            Catch:
              - ErrorEquals:
                  - States.Timeout
                ResultPath: $.item_result
                Next: HandleItemTimeout
              - ErrorEquals:
                  - States.ALL
                ResultPath: $.item_result
                Next: HandleItemError
            End: true

          HandleItemTimeout:
            Type: Pass
            Parameters:
              errorType: Timeout
              details.$: $.item_result
            ResultPath: $.timeoutInfo
            End: true

          HandleItemError:
            Type: Pass
            Parameters:
              errorType: OtherError
              details.$: $.item_result
            ResultPath: $.errorInfo
            End: true
      Next: AggregateResults
      Catch:
        - ErrorEquals:
            - States.ALL
          ResultPath: $.error_info
          Next: NotifyError

    AggregateResults:
      Type: Task
      Resource: !GetAtt AggregateResultsLambda.Arn
      Next: NotifySuccess
```

## Choice State Pattern (Conditional Routing)

For routing based on input data:

```yaml
Definition:
  StartAt: ExtractMetadata
  States:
    ExtractMetadata:
      Type: Task
      Resource: !GetAtt ExtractMetadataLambda.Arn
      ResultPath: $.metadata_output
      Next: FlattenOutput

    FlattenOutput:
      Type: Pass
      Parameters:
        bucket.$: $.metadata_output.bucket
        file_type.$: $.metadata_output.file_type
        file_name.$: $.metadata_output.file_name
        should_distribute.$: $.metadata_output.should_distribute
      ResultPath: $
      Next: CheckFileType

    CheckFileType:
      Type: Choice
      Choices:
        - Variable: $.file_type
          StringEquals: docx
          Next: ConvertDocxToExcel
        - Variable: $.file_type
          StringEquals: pdf
          Next: ConvertPdfToExcel
        - Variable: $.should_distribute
          BooleanEquals: true
          Next: DistributeFile
        - Variable: $.should_distribute
          StringEquals: 'yes'
          Next: DistributeFile
      Default: ProcessDirectly

    ConvertDocxToExcel:
      Type: Task
      Resource: !GetAtt DocxToExcelLambda.Arn
      Next: ProcessDirectly

    ConvertPdfToExcel:
      Type: Task
      Resource: !GetAtt PdfToExcelLambda.Arn
      Next: ProcessDirectly

    DistributeFile:
      Type: Task
      Resource: !GetAtt DistributeFileLambda.Arn
      End: true

    ProcessDirectly:
      Type: Task
      Resource: !GetAtt ProcessDirectlyLambda.Arn
      Next: CheckReverseConversion

    CheckReverseConversion:
      Type: Choice
      Choices:
        - Variable: $.file_type
          StringEquals: docx
          Next: ConvertExcelToDocx
        - Variable: $.file_type
          StringEquals: pdf
          Next: ConvertExcelToPdf
      Default: GenerateReport

    ConvertExcelToDocx:
      Type: Task
      Resource: !GetAtt ExcelToDocxLambda.Arn
      Next: GenerateReport

    ConvertExcelToPdf:
      Type: Task
      Resource: !GetAtt ExcelToPdfLambda.Arn
      Next: GenerateReport

    GenerateReport:
      Type: Task
      Resource: !GetAtt GenerateReportLambda.Arn
      End: true
```

## Wait State Pattern (Polling)

For waiting on async operations:

```yaml
Definition:
  StartAt: StartProcessing
  States:
    StartProcessing:
      Type: Task
      Resource: !GetAtt StartProcessingLambda.Arn
      ResultPath: $
      Next: WaitForCompletion

    WaitForCompletion:
      Type: Wait
      Seconds: 260
      Next: CheckStatus

    CheckStatus:
      Type: Task
      Resource: arn:aws:states:::lambda:invoke
      OutputPath: $.Payload
      Parameters:
        Payload.$: $
        FunctionName: !GetAtt CheckStatusLambda.Arn
      Retry:
        - ErrorEquals:
            - Lambda.ServiceException
            - Lambda.AWSLambdaException
            - Lambda.SdkClientException
            - Lambda.TooManyRequestsException
          IntervalSeconds: 1
          MaxAttempts: 3
          BackoffRate: 2
          JitterStrategy: FULL
      Next: EvaluateStatus

    EvaluateStatus:
      Type: Choice
      Choices:
        - Variable: $.status
          StringEquals: COMPLETE
          Next: ProcessResults
        - Variable: $.status
          StringEquals: FAILED
          Next: NotifyError
      Default: WaitForCompletion

    ProcessResults:
      Type: Task
      Resource: !GetAtt ProcessResultsLambda.Arn
      Next: NotifySuccess
```

## Nested State Machine Pattern

For invoking child state machines:

```yaml
Definition:
  StartAt: InvokeChildWorkflow
  States:
    InvokeChildWorkflow:
      Type: Task
      Resource: arn:aws:states:::states:startExecution.sync
      Parameters:
        StateMachineArn: !GetAtt ChildStateMachine.Arn
        Input.$: $
      Catch:
        - ErrorEquals:
            - States.ALL
          Next: HandleChildError
          ResultPath: $.errorInfo
      Next: CheckChildStatus

    CheckChildStatus:
      Type: Choice
      Choices:
        - Variable: $.Status
          StringEquals: SUCCEEDED
          Next: ProcessSuccess
      Default: HandleChildError

    ProcessSuccess:
      Type: Pass
      End: true

    HandleChildError:
      Type: Task
      Resource: !GetAtt ErrorHandlerLambda.Arn
      End: true
```

## ECS Task Integration Pattern

For running ECS tasks from Step Functions:

```yaml
Definition:
  StartAt: RunEcsTask
  TimeoutSeconds: 3600
  States:
    RunEcsTask:
      Type: Task
      Resource: arn:aws:states:::ecs:runTask.sync
      Parameters:
        Cluster: !Ref EcsCluster
        TaskDefinition: !Ref EcsTaskDefinition
        LaunchType: FARGATE
        NetworkConfiguration:
          AwsvpcConfiguration:
            Subnets:
              - !Ref LambdaSubnet1ID
              - !Ref LambdaSubnet2ID
            SecurityGroups:
              - !Ref LambdaSecurityGroupID1
              - !Ref LambdaSecurityGroupID2
            AssignPublicIp: DISABLED
        Overrides:
          ContainerOverrides:
            - Name: !Ref EcsContainerName
              Environment:
                - Name: S3_BUCKET
                  Value.$: $.s3_bucket
                - Name: S3_KEY
                  Value.$: $.s3_key
      ResultPath: $.ecsTaskResult
      Next: NotifySuccess
      Retry:
        - ErrorEquals:
            - States.ALL
          IntervalSeconds: 2
          MaxAttempts: 1
          BackoffRate: 2
          JitterStrategy: FULL
      Catch:
        - ErrorEquals:
            - States.ALL
          ResultPath: $.error_info
          Next: NotifyError
```

## JSONata Query Language Pattern

For modern Step Functions with JSONata:

```yaml
Definition:
  Comment: Workflow using JSONata
  QueryLanguage: JSONata
  StartAt: WaitState
  States:
    WaitState:
      Type: Wait
      Seconds: 10
      Next: InvokeLambda

    InvokeLambda:
      Type: Task
      Arguments:
        FunctionName: !GetAtt MyLambda.Arn
        Payload: '{% $states.input %}'
      Output: '{% $states.result.Payload %}'
      Resource: arn:aws:states:::lambda:invoke
      Retry:
        - BackoffRate: 2
          ErrorEquals:
            - Sandbox.TimedOut
            - States.TaskFailed
            - Lambda.ServiceException
          IntervalSeconds: 1
          JitterStrategy: FULL
          MaxAttempts: 3
      End: true
```

## State Input/Output Manipulation

### InputPath, ResultPath, OutputPath

```yaml
TaskState:
  Type: Task
  Resource: !GetAtt MyLambda.Arn
  InputPath: $              # What goes INTO the task
  ResultPath: $.taskResult  # Where to PUT the result
  OutputPath: $             # What to PASS to next state
  Next: NextState
```

### Parameters (Restructuring Input)

```yaml
TaskState:
  Type: Task
  Resource: !GetAtt MyLambda.Arn
  Parameters:
    bucket.$: $.bucket
    file_key.$: $.metadata.file_key
    static_value: some_constant
    combined.$: States.Format('{}-{}', $.prefix, $.suffix)
  Next: NextState
```

### States.Format Examples

```yaml
# Simple formatting
Message.$: States.Format('Processing file: {}', $.file_name)

# Multiple values
Message.$: States.Format('Report {} for {} is ready.', $.report_id, $.user)

# Error messages
Message.$: States.Format('Error in workflow: {}', $.error_info)
```
