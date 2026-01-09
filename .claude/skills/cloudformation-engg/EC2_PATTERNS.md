# EC2, ALB & Auto Scaling Patterns

Reference patterns for EC2 infrastructure with load balancing and auto scaling.

## Standard Parameters for EC2 Stacks

```yaml
Parameters:
  EC2InstanceType:
    Description: EC2 instance type
    Type: String
    Default: m5.large
    AllowedValues:
      - m5.large
      - m5.xlarge
      - g4dn.xlarge
      - g4dn.2xlarge
      - g5.2xlarge

  KeyName:
    Description: Name of existing EC2 key pair for SSH access
    Type: AWS::EC2::KeyPair::KeyName

  AmiId:
    Description: AMI ID for EC2 instances
    Type: String

  OperatorEmail:
    Description: Email for scaling notifications
    Type: String
    Default: 'team-support@ameritas.com'

  Subnets:
    Type: List<AWS::EC2::Subnet::Id>
    Description: At least two subnets in different AZs

  VPC:
    Type: AWS::EC2::VPC::Id
    Description: VPC for resources

  ELBSecurityGroupId:
    Description: Load Balancer Security Group
    Type: AWS::EC2::SecurityGroup::Id

  EC2SecurityGroupId:
    Description: EC2 Security Group
    Type: AWS::EC2::SecurityGroup::Id

  EC2InstanceIAMRole:
    Description: EC2 IAM role name
    Type: String
    AllowedValues:
      - alic-aio-d-service-ec2-iam-role
      - alic-aio-m-service-ec2-iam-role
      - alic-aio-p-service-ec2-iam-role

  ELBCustomDomainName:
    Description: Custom DNS Host Name for load balancer
    Type: String
    AllowedValues:
      - service.inbison.com
      - service-m.inbison.com
      - service-d.inbison.com

  ELBCustomDomainSSLCertArn:
    Description: ARN of SSL certificate
    Type: String

  AutoScalingDesiredCapacity:
    Description: Desired capacity of Auto Scaling group
    Type: String
    Default: '2'

  AutoScalingMinimumSize:
    Description: Minimum size of Auto Scaling group
    Type: String
    Default: '1'

  AutoScalingMaximumSize:
    Description: Maximum size of Auto Scaling group
    Type: String
    Default: '4'

  CPUPolicyTargetValue:
    Type: String
    Description: CPU utilization target for scaling (1-100)
    Default: '85'

  ELBSSLSecurityPolicy:
    Description: SSL security policy for load balancer
    Type: String
    Default: ELBSecurityPolicy-TLS13-1-2-2021-06
    AllowedValues:
      - ELBSecurityPolicy-TLS13-1-2-2021-06
```

## Target Group

```yaml
  EC2TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      HealthCheckIntervalSeconds: 5
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckTimeoutSeconds: 3
      HealthyThresholdCount: 5
      Matcher:
        HttpCode: '200'
      Name: !Sub ${AWS::StackName}-service-tg
      Port: 8080
      Protocol: HTTP
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: '180'
        - Key: stickiness.enabled
          Value: true
        - Key: stickiness.type
          Value: lb_cookie
        - Key: stickiness.lb_cookie.duration_seconds
          Value: 86400
      UnhealthyThresholdCount: 3
      VpcId: !Ref VPC
```

## Application Load Balancer

```yaml
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      LoadBalancerAttributes:
        - Key: idle_timeout.timeout_seconds
          Value: '120'
        - Key: deletion_protection.enabled
          Value: true
      Name: !Sub ${AWS::StackName}-service-lb
      Scheme: internal
      Subnets: !Ref Subnets
      SecurityGroups:
        - !Ref ELBSecurityGroupId
```

## ALB Listeners

```yaml
  ALBHTTPListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: 443
            Host: !Ref ELBCustomDomainName
            Path: "/#{path}"
            Query: "#{query}"
            StatusCode: HTTP_301
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  ALBHTTPSListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref EC2TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: !Ref ELBCustomDomainSSLCertArn
      SslPolicy: !Ref ELBSSLSecurityPolicy
```

## Launch Template

```yaml
  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub ${AWS::StackName}-service-launch-template
      LaunchTemplateData:
        IamInstanceProfile:
          Name: !Ref EC2InstanceIAMRole
        ImageId: !Ref AmiId
        InstanceType: !Ref EC2InstanceType
        KeyName: !Ref KeyName
        SecurityGroupIds:
          - !Ref EC2SecurityGroupId
        Monitoring:
          Enabled: true
        MetadataOptions:
          HttpTokens: required
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            source /etc/environment
            # Add initialization commands here
```

## Auto Scaling Group

```yaml
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: !Sub ${AWS::StackName}-service-asg
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MaxSize: !Ref AutoScalingMaximumSize
      MinSize: !Ref AutoScalingMinimumSize
      DesiredCapacity: !Ref AutoScalingDesiredCapacity
      DefaultInstanceWarmup: 30
      NotificationConfigurations:
        - TopicARN: !Ref AutoScalingNotificationTopic
          NotificationTypes:
            - autoscaling:EC2_INSTANCE_LAUNCH
            - autoscaling:EC2_INSTANCE_LAUNCH_ERROR
            - autoscaling:EC2_INSTANCE_TERMINATE
            - autoscaling:EC2_INSTANCE_TERMINATE_ERROR
      TargetGroupARNs:
        - !Ref EC2TargetGroup
      VPCZoneIdentifier: !Ref Subnets
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-service-ec2-asg
          PropagateAtLaunch: true
```

## Scaling Policies

### CPU-Based Target Tracking

```yaml
  CPUScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: !Ref AutoScalingGroup
      PolicyType: TargetTrackingScaling
      TargetTrackingConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: ASGAverageCPUUtilization
        TargetValue: !Ref CPUPolicyTargetValue
```

### Step Scaling with CloudWatch Alarms (GPU Example)

```yaml
  GPUHighScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: !Ref AutoScalingGroup
      PolicyType: StepScaling
      AdjustmentType: ChangeInCapacity
      StepAdjustments:
        - MetricIntervalLowerBound: 0
          ScalingAdjustment: 1

  GPULowScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: !Ref AutoScalingGroup
      PolicyType: StepScaling
      AdjustmentType: ChangeInCapacity
      StepAdjustments:
        - MetricIntervalUpperBound: 0
          ScalingAdjustment: -1

  HighGPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${AWS::StackName}-high-gpu-alarm
      AlarmDescription: Scale out when GPU > 85% for 3 minutes
      MetricName: nvidia_smi_utilization_gpu
      Namespace: CWAgent
      Statistic: Average
      Period: '60'
      EvaluationPeriods: '3'
      Threshold: '85'
      AlarmActions:
        - !Ref GPUHighScalingPolicy
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: AutoScalingGroupName
          Value: !Ref AutoScalingGroup

  LowGPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${AWS::StackName}-low-gpu-alarm
      AlarmDescription: Scale in when GPU < 30% for 10 minutes
      MetricName: nvidia_smi_utilization_gpu
      Namespace: CWAgent
      Statistic: Average
      Period: '60'
      EvaluationPeriods: '10'
      Threshold: '30'
      AlarmActions:
        - !Ref GPULowScalingPolicy
      ComparisonOperator: LessThanThreshold
      Dimensions:
        - Name: AutoScalingGroupName
          Value: !Ref AutoScalingGroup
```

### Scheduled Scaling (Optional)

```yaml
  ScheduledScaleOutPolicy:
    Type: AWS::AutoScaling::ScheduledAction
    Properties:
      AutoScalingGroupName: !Ref AutoScalingGroup
      DesiredCapacity: !Ref AutoScalingDesiredCapacity
      MaxSize: !Ref AutoScalingMaximumSize
      MinSize: !Ref AutoScalingMinimumSize
      Recurrence: '* 6 * * MON-FRI'  # 6 AM Mon-Fri
      TimeZone: 'America/Chicago'

  ScheduledScaleInPolicy:
    Type: AWS::AutoScaling::ScheduledAction
    Properties:
      AutoScalingGroupName: !Ref AutoScalingGroup
      DesiredCapacity: '0'
      MaxSize: '0'
      MinSize: '0'
      Recurrence: '* 19 * * MON-FRI'  # 7 PM Mon-Fri
      TimeZone: 'America/Chicago'
```

## SNS Notification Topic

```yaml
  AutoScalingNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub ${AWS::StackName}-autoscaling-sns-topic
      Subscription:
        - Endpoint: !Ref OperatorEmail
          Protocol: email
```

## Load Balancer Configuration Guidelines

| Attribute | Web App | API | Long-Running |
|-----------|---------|-----|--------------|
| idle_timeout | 60 | 120 | 1200 |
| deletion_protection | true | true | true |
| stickiness.enabled | true | false | true |
| stickiness.duration | 86400 | - | 86400 |
| deregistration_delay | 180 | 60 | 300 |

## Health Check Configuration

| Service Type | Path | Interval | Timeout | Healthy | Unhealthy |
|--------------|------|----------|---------|---------|-----------|
| Web App | /health | 5 | 3 | 5 | 3 |
| API | /api/health | 10 | 5 | 3 | 2 |
| AI Service | / | 5 | 3 | 5 | 3 |
