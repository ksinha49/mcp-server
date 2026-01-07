# Security Guide - MCP Snowflake Service

## Overview

This MCP server provides access to Snowflake data warehouses, enabling SQL query execution and schema exploration. This document covers security considerations, best practices, and compliance requirements for handling enterprise data.

## Security Architecture

### Authentication Methods

| Method | Security Level | Use Case |
|--------|----------------|----------|
| Password | Basic | Development only |
| Key-Pair | High | Production recommended |
| OAuth | High | Enterprise SSO |
| External OAuth | High | Third-party IdP |

### Recommended Authentication

```
Production: Key-Pair Authentication
├── Private key stored in secrets manager
├── Public key registered with Snowflake user
├── No password transmission
└── Key rotation supported
```

## Snowflake Security Features

### Role-Based Access Control

This service should use a dedicated role with minimum privileges:

```sql
-- Create restricted role
CREATE ROLE mcp_readonly_role;

-- Grant only necessary privileges
GRANT USAGE ON WAREHOUSE compute_wh TO ROLE mcp_readonly_role;
GRANT USAGE ON DATABASE analytics TO ROLE mcp_readonly_role;
GRANT USAGE ON SCHEMA analytics.public TO ROLE mcp_readonly_role;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics.public TO ROLE mcp_readonly_role;

-- No ACCOUNTADMIN, SECURITYADMIN, or SYSADMIN access
```

### Row Access Policies

Snowflake row access policies are respected:

```sql
-- Example: User can only see their department's data
CREATE ROW ACCESS POLICY dept_policy AS (department VARCHAR) RETURNS BOOLEAN ->
  CURRENT_ROLE() = 'ADMIN' OR department = CURRENT_USER_DEPARTMENT();
```

### Column Masking

Snowflake masking policies are respected:

```sql
-- Example: Mask SSN for non-privileged roles
CREATE MASKING POLICY ssn_mask AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('HR_ADMIN') THEN val
    ELSE 'XXX-XX-' || RIGHT(val, 4)
  END;
```

## Data Security

### Data Handled

| Data Type | Sensitivity | Retention |
|-----------|-------------|-----------|
| Query results | Variable (High) | Not stored |
| Schema metadata | Low | Not stored |
| SQL queries | Medium | Logged |
| Credentials | Critical | Encrypted |

### Query Result Security

- Results streamed directly to client
- No persistent storage of query results
- Large result sets paginated
- Memory cleared after response

### Data Classification

Query results may contain:
- Personally Identifiable Information (PII)
- Protected Health Information (PHI)
- Financial data
- Trade secrets
- Customer data

**Important**: Snowflake's built-in data governance features (masking, row access policies) are the primary controls. This service does not add additional classification.

## Credential Security

### Password Authentication (Development Only)

```bash
# Never use in production
SNOWFLAKE_PASSWORD=your-password  # Insecure
```

### Key-Pair Authentication (Recommended)

```bash
# Generate strong key
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out rsa_key.p8

# Store securely
SNOWFLAKE_PRIVATE_KEY_PATH=/secure/path/rsa_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=stored-in-secrets-manager
```

### Credential Storage

| Environment | Method |
|-------------|--------|
| Development | Environment variables |
| Production | AWS Secrets Manager |
| Enterprise | HashiCorp Vault |

**Never**:
- Commit credentials to source control
- Log credentials
- Pass credentials in URLs
- Store in plain text files

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → Snowflake Service (private subnet)
                              ↓
                       Snowflake (via PrivateLink)
```

### Snowflake Network Policies

Configure network policies in Snowflake:

```sql
-- Allow only from specific IPs
CREATE NETWORK POLICY mcp_policy
  ALLOWED_IP_LIST = ('10.0.0.0/8', '172.16.0.0/12');

-- Apply to user
ALTER USER mcp_service_user SET NETWORK_POLICY = mcp_policy;
```

### AWS PrivateLink (Recommended)

Use PrivateLink for production deployments:
- Traffic stays within AWS network
- No internet exposure
- Lower latency

## Query Security

### SQL Injection Prevention

This service:
- Uses parameterized queries where possible
- Validates query structure
- Limits query complexity

### Query Restrictions

Recommended restrictions for the service role:

```sql
-- No DDL operations
-- No account-level operations
-- No user management
-- Read-only on specified schemas
```

### Dangerous Query Patterns

The service should block or warn on:

| Pattern | Risk | Action |
|---------|------|--------|
| `DROP` | Data loss | Block |
| `DELETE` | Data loss | Block |
| `TRUNCATE` | Data loss | Block |
| `CREATE USER` | Privilege escalation | Block |
| `GRANT` | Privilege escalation | Block |
| `SELECT *` on large tables | Resource exhaustion | Warn/limit |

## Rate Limiting

### Snowflake Resource Limits

Configure warehouse limits:

```sql
-- Set statement timeout
ALTER WAREHOUSE compute_wh SET STATEMENT_TIMEOUT_IN_SECONDS = 300;

-- Set query concurrency
ALTER WAREHOUSE compute_wh SET MAX_CONCURRENCY_LEVEL = 8;
```

### Application Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Queries | 30 | per minute |
| Schema discovery | 60 | per minute |
| Table describes | 60 | per minute |

## Audit Logging

### Snowflake Query History

Snowflake maintains comprehensive query history:

```sql
-- View recent queries by service user
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE USER_NAME = 'MCP_SERVICE_USER'
ORDER BY START_TIME DESC
LIMIT 100;
```

### Application Events to Log

| Event | Level | Data |
|-------|-------|------|
| Query execution | INFO | query hash, rows returned |
| Schema discovery | INFO | database, schema |
| Auth failure | WARN | reason, user |
| Query timeout | WARN | query hash, duration |
| Large result set | WARN | query hash, row count |

### Sensitive Data in Logs

**Never log**:
- Full SQL queries (may contain data)
- Query results
- Credentials
- PII discovered in queries

**Safe to log**:
- Query hashes
- Row counts
- Execution times
- Error codes

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Mitigation |
|------|------------|
| SQL Injection | Parameterized queries, input validation |
| Broken Auth | Key-pair auth, network policies |
| Sensitive Data | Masking policies, RBAC |
| Security Misconfiguration | Minimum privilege role |
| Insufficient Logging | Query history enabled |

### Data Warehouse Risks

| Risk | Mitigation |
|------|------------|
| Data exfiltration | Query limits, audit logging |
| Resource exhaustion | Warehouse limits, timeouts |
| Credential theft | Key-pair auth, rotation |
| Privilege escalation | Restricted role |

## Incident Response

### Compromised Credentials

1. **Immediately disable** the user in Snowflake
   ```sql
   ALTER USER mcp_service_user SET DISABLED = TRUE;
   ```
2. Rotate key pair or password
3. Review query history for unauthorized access
4. Re-enable with new credentials

### Suspicious Query Activity

1. Review Snowflake query history
2. Check for data exfiltration patterns
3. Disable user if confirmed malicious
4. Preserve audit logs
5. Notify security team

### Data Breach

1. Identify affected data via query history
2. Disable service access
3. Assess scope using Snowflake audit logs
4. Follow organizational incident response
5. Notify affected parties as required

## Compliance

### Supported Standards

- **SOC 2**: Query auditing, access controls
- **HIPAA**: PHI masking, audit logs (with additional controls)
- **GDPR**: Data subject access, audit trails
- **PCI DSS**: Cardholder data masking

### Snowflake Compliance Features

This service respects:
- Data masking policies
- Row access policies
- Object tagging
- Access history
- Data retention policies

## Security Checklist

### Pre-Production

- [ ] Service role with minimum privileges created
- [ ] Key-pair authentication configured
- [ ] Private key in secrets manager
- [ ] Network policy applied to user
- [ ] Warehouse resource limits set
- [ ] Query timeout configured
- [ ] Audit logging verified
- [ ] TLS enabled for all connections

### Ongoing

- [ ] Rotate key pair (quarterly)
- [ ] Review query history (weekly)
- [ ] Audit role permissions (quarterly)
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
