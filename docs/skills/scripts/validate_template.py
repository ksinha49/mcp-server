#!/usr/bin/env python3
"""
CloudFormation/SAM Template Validator for Ameritas Standards

Validates templates against Ameritas naming conventions and best practices.

Usage:
    python validate_template.py <template_file.yaml>
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple


class TemplateValidator:
    """Validates CloudFormation/SAM templates against Ameritas standards."""

    REQUIRED_PARAMETERS = [
        'AWSAccountName',
        'LambdaSubnet1ID',
        'LambdaSubnet2ID',
        'LambdaSecurityGroupID1',
        'LambdaSecurityGroupID2',
        'LambdaIAMRoleARN',
    ]

    NAMING_PATTERNS = {
        'Lambda': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+',
        'StepFunction': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+-sm',
        'SQS': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+-(queue|dlq)',
        'SNS': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+-topic',
        'EventBridge': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+-rule',
        'Alarm': r'\$\{AWSAccountName\}-\$\{AWS::StackName\}-[\w-]+-alarm',
    }

    STATEFUL_RESOURCES = [
        'AWS::DynamoDB::Table',
        'AWS::S3::Bucket',
        'AWS::RDS::DBInstance',
        'AWS::RDS::DBCluster',
    ]

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.template: Dict[str, Any] = {}

    def load_template(self) -> bool:
        """Load and parse the YAML template."""
        try:
            with open(self.template_path, 'r') as f:
                self.template = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"Template file not found: {self.template_path}")
            return False

    def validate_header(self) -> None:
        """Validate template header and format version."""
        if 'AWSTemplateFormatVersion' not in self.template:
            self.errors.append("Missing AWSTemplateFormatVersion")
        elif self.template['AWSTemplateFormatVersion'] != '2010-09-09':
            self.warnings.append("AWSTemplateFormatVersion should be '2010-09-09'")

        if 'Description' not in self.template:
            self.warnings.append("Template should have a Description")

    def validate_parameters(self) -> None:
        """Validate required parameters are present."""
        parameters = self.template.get('Parameters', {})

        for param in self.REQUIRED_PARAMETERS:
            if param not in parameters:
                self.warnings.append(f"Missing recommended parameter: {param}")

        # Check parameter descriptions
        for param_name, param_def in parameters.items():
            if 'Description' not in param_def:
                self.warnings.append(f"Parameter '{param_name}' missing Description")

    def validate_globals(self) -> None:
        """Validate SAM Globals section."""
        if 'Transform' in self.template and 'AWS::Serverless' in str(self.template.get('Transform', '')):
            globals_section = self.template.get('Globals', {})
            function_globals = globals_section.get('Function', {})

            if 'Tracing' not in function_globals:
                self.warnings.append("Globals.Function should have Tracing: Active")

            if 'LoggingConfig' not in function_globals:
                self.warnings.append("Globals.Function should have LoggingConfig with JSON format")

    def validate_resource_naming(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate resource naming conventions."""
        resource_type = resource.get('Type', '')
        properties = resource.get('Properties', {})

        # Get the name property based on resource type
        name_property = None
        if 'FunctionName' in properties:
            name_property = properties['FunctionName']
        elif 'Name' in properties:
            name_property = properties['Name']
        elif 'QueueName' in properties:
            name_property = properties['QueueName']
        elif 'TopicName' in properties:
            name_property = properties['TopicName']

        if name_property:
            name_str = self._extract_sub_string(name_property)
            if name_str:
                # Check for underscores (should use hyphens)
                if '_' in name_str and '${' not in name_str.replace('${AWSAccountName}', '').replace('${AWS::StackName}', ''):
                    self.warnings.append(
                        f"Resource '{resource_name}': Use hyphens instead of underscores in names"
                    )

                # Check naming pattern includes account and stack name
                if '${AWSAccountName}' not in name_str and '${AWS::StackName}' not in name_str:
                    self.warnings.append(
                        f"Resource '{resource_name}': Name should include ${{AWSAccountName}}-${{AWS::StackName}} prefix"
                    )

    def _extract_sub_string(self, value: Any) -> str:
        """Extract string from Fn::Sub or direct value."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            if 'Fn::Sub' in value:
                sub_value = value['Fn::Sub']
                if isinstance(sub_value, str):
                    return sub_value
                if isinstance(sub_value, list) and len(sub_value) > 0:
                    return sub_value[0]
        return ''

    def validate_lambda_function(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate Lambda function configuration."""
        properties = resource.get('Properties', {})

        # Check VPC config
        if 'VpcConfig' not in properties:
            self.errors.append(f"Lambda '{resource_name}': Missing VpcConfig")

        # Check role
        if 'Role' not in properties:
            self.errors.append(f"Lambda '{resource_name}': Missing Role")

        # Check for inline code (should use CodeUri)
        if 'InlineCode' in properties or 'Code' in properties:
            code = properties.get('Code', {})
            if isinstance(code, dict) and 'ZipFile' in code:
                self.errors.append(f"Lambda '{resource_name}': Use CodeUri to S3 instead of inline code")

        # Check timeout
        timeout = properties.get('Timeout', 3)
        if timeout < 30:
            self.warnings.append(f"Lambda '{resource_name}': Timeout ({timeout}s) may be too short")

        # Check for SamResourceId metadata
        metadata = resource.get('Metadata', {})
        if 'SamResourceId' not in metadata:
            self.warnings.append(f"Lambda '{resource_name}': Missing Metadata.SamResourceId")

    def validate_step_function(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate Step Function configuration."""
        properties = resource.get('Properties', {})

        # Check tracing
        tracing = properties.get('Tracing', {})
        if not tracing.get('Enabled', False):
            self.warnings.append(f"StepFunction '{resource_name}': Tracing should be enabled")

        # Check definition for retry policies
        definition = properties.get('Definition', {})
        states = definition.get('States', {})

        for state_name, state in states.items():
            if state.get('Type') == 'Task':
                if 'Retry' not in state:
                    self.warnings.append(
                        f"StepFunction '{resource_name}' state '{state_name}': Missing Retry configuration"
                    )
                if 'Catch' not in state:
                    self.warnings.append(
                        f"StepFunction '{resource_name}' state '{state_name}': Missing Catch for error handling"
                    )

        # Check for SamResourceId metadata
        metadata = resource.get('Metadata', {})
        if 'SamResourceId' not in metadata:
            self.warnings.append(f"StepFunction '{resource_name}': Missing Metadata.SamResourceId")

    def validate_stateful_resource(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate stateful resources have retention policies."""
        deletion_policy = resource.get('DeletionPolicy')
        update_policy = resource.get('UpdateReplacePolicy')

        if deletion_policy != 'Retain':
            self.warnings.append(
                f"Stateful resource '{resource_name}': Should have DeletionPolicy: Retain"
            )

        if update_policy != 'Retain':
            self.warnings.append(
                f"Stateful resource '{resource_name}': Should have UpdateReplacePolicy: Retain"
            )

    def validate_sqs_queue(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate SQS queue configuration."""
        properties = resource.get('Properties', {})

        # Check for DLQ on standard queues
        queue_name = self._extract_sub_string(properties.get('QueueName', ''))
        is_dlq = 'dlq' in queue_name.lower()
        is_fifo = properties.get('FifoQueue', False)

        if not is_dlq and 'RedrivePolicy' not in properties:
            self.warnings.append(
                f"SQS Queue '{resource_name}': Consider adding RedrivePolicy for dead letter handling"
            )

        # Check visibility timeout
        visibility_timeout = properties.get('VisibilityTimeout', 30)
        if visibility_timeout < 60 and not is_dlq:
            self.warnings.append(
                f"SQS Queue '{resource_name}': VisibilityTimeout ({visibility_timeout}s) may be too short for Lambda processing"
            )

    def validate_eventbridge_rule(self, resource_name: str, resource: Dict[str, Any]) -> None:
        """Validate EventBridge rule configuration."""
        properties = resource.get('Properties', {})
        targets = properties.get('Targets', [])

        for target in targets:
            if 'DeadLetterConfig' not in target:
                self.warnings.append(
                    f"EventBridge Rule '{resource_name}': Target should have DeadLetterConfig"
                )

    def validate_resources(self) -> None:
        """Validate all resources in the template."""
        resources = self.template.get('Resources', {})

        for resource_name, resource in resources.items():
            resource_type = resource.get('Type', '')

            # Validate naming for all resources
            self.validate_resource_naming(resource_name, resource)

            # Type-specific validation
            if resource_type in ['AWS::Serverless::Function', 'AWS::Lambda::Function']:
                self.validate_lambda_function(resource_name, resource)

            elif resource_type == 'AWS::Serverless::StateMachine':
                self.validate_step_function(resource_name, resource)

            elif resource_type in self.STATEFUL_RESOURCES:
                self.validate_stateful_resource(resource_name, resource)

            elif resource_type == 'AWS::SQS::Queue':
                self.validate_sqs_queue(resource_name, resource)

            elif resource_type == 'AWS::Events::Rule':
                self.validate_eventbridge_rule(resource_name, resource)

    def validate_outputs(self) -> None:
        """Validate outputs section."""
        outputs = self.template.get('Outputs', {})

        if not outputs:
            self.warnings.append("Template has no Outputs section")
        else:
            for output_name, output in outputs.items():
                if 'Description' not in output:
                    self.warnings.append(f"Output '{output_name}': Missing Description")

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results."""
        if not self.load_template():
            return False, self.errors, self.warnings

        self.validate_header()
        self.validate_parameters()
        self.validate_globals()
        self.validate_resources()
        self.validate_outputs()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_template.py <template_file.yaml>")
        sys.exit(1)

    template_path = sys.argv[1]
    validator = TemplateValidator(template_path)
    is_valid, errors, warnings = validator.validate()

    print(f"\n{'='*60}")
    print(f"Validation Results for: {template_path}")
    print('='*60)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    if is_valid and not warnings:
        print("\n✅ Template passes all validations!")
    elif is_valid:
        print(f"\n✅ Template is valid with {len(warnings)} warning(s)")
    else:
        print(f"\n❌ Template has {len(errors)} error(s)")

    print('='*60 + '\n')

    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
