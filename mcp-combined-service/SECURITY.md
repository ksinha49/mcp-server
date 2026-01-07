# Security Guide - MCP Combined Service

## Overview

This MCP server combines access to multiple enterprise services including Microsoft 365 (Outlook, SharePoint, Teams), Azure DevOps, and Snowflake. With the optional **Code Execution** layer, it also allows agent-generated TypeScript code to run in a sandboxed environment. This document covers security considerations for both standard MCP operations and code execution.

## Security Architecture

### Multi-Provider Authentication

```
MCP Client → Combined Service → Provider-specific auth
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
             Microsoft OAuth   Azure DevOps PAT   Snowflake Auth
                    ↓               ↓               ↓
              Graph API      DevOps REST API   Snowflake API
```

### Code Execution Security

```
MCP Client → Combined Service → Code Execution Layer
                                        ↓
                        ┌───────────────┴───────────────┐
                        ↓                               ↓
                 Deno Sandbox                    Docker Sandbox
                 (V8 isolates)                   (Container isolation)
                        ↓                               ↓
              Permission-restricted          cgroups + seccomp + namespaces
                        ↓                               ↓
              Tool Callback Proxy ←──────────→ Tool Callback Proxy
                        ↓                               ↓
                   Provider APIs ←──────────→ Provider APIs
```

### Authentication per Provider

| Provider | Auth Method | Credential Storage |
|----------|-------------|-------------------|
| Outlook | OAuth via Gateway | Encrypted tokens |
| SharePoint | OAuth via Gateway | Encrypted tokens |
| Teams | OAuth via Gateway | Encrypted tokens |
| Azure DevOps | PAT or OAuth | Secrets Manager |
| Snowflake | Password/Key-pair | Secrets Manager |

## Code Execution Security

### Dual Sandbox Architecture

The code execution layer supports two sandbox modes:

| Security Feature | Deno Sandbox | Docker Sandbox |
|-----------------|--------------|----------------|
| Isolation Level | V8 process isolates | Container namespaces |
| Filesystem Access | Denied by default | Read-only, restricted |
| Network Access | Denied except callback | None (host.docker.internal only) |
| Resource Limits | V8 heap limits | cgroups (CPU, memory) |
| Syscall Filtering | N/A | seccomp profile |
| Privilege Escalation | Permission flags | no-new-privileges |
| Best For | Development | Production |

### Static Code Analysis

Before execution, all code is analyzed for dangerous patterns:

| Blocked Pattern | Reason |
|----------------|--------|
| `eval()` | Arbitrary code execution |
| `Function()` | Dynamic function creation |
| `new Function()` | Dynamic function creation |
| `import()` | Dynamic module loading |
| `Deno.*` | Direct runtime access |
| `globalThis` | Global scope access |
| `__proto__` | Prototype pollution |
| `constructor[]` | Prototype chain access |
| `require()` | Node.js module loading |
| `process.*` | Node.js process access |

### Runtime Protections

| Protection | Deno | Docker |
|------------|------|--------|
| Execution Timeout | 60s default | 60s default |
| Memory Limit | V8 heap (128MB) | cgroups (128MB) |
| Tool Call Limit | 50 per execution | 50 per execution |
| Rate Limiting | 30 requests/min | 30 requests/min |
| Token Isolation | Never in user code | Never in user code |

### Token Security in Code Execution

OAuth tokens are **never** exposed to user code:

```
User Code                    Sandbox                    Python Backend
    │                           │                            │
    ├──→ tools.outlook.search() │                            │
    │                           ├──→ HTTP callback ──────────→│
    │                           │    (internal only)         │
    │                           │                            ├──→ Validate token
    │                           │                            ├──→ Call Graph API
    │                           │←── Result ─────────────────┤
    ├←── Filtered result ───────┤                            │
    │                           │                            │
```

- Tokens stored only in Python backend
- Callbacks use internal HTTP (localhost)
- Token re-validated on each tool call
- Results filtered before returning to sandbox

### Docker Sandbox Specifics

#### Seccomp Profile

The Docker executor uses a restrictive seccomp profile that:
- Allows only necessary syscalls for Node.js execution
- Blocks dangerous operations (mount, ptrace, etc.)
- Prevents privilege escalation attempts

#### Container Configuration

```yaml
security_opt:
  - no-new-privileges:true
  - seccomp=seccomp-profile.json
network_mode: none  # No external network
read_only: true     # Read-only filesystem
mem_limit: 128m     # Memory limit
cpus: 0.5          # CPU limit
```

#### Pre-warmed Container Pool

- Containers created at startup
- Recycled after max age (1 hour default)
- Isolated per execution
- No shared state between executions

## Security Considerations

### Combined Attack Surface

Running multiple providers increases:
- Number of credentials to manage
- Potential impact of a breach
- Complexity of security monitoring

With code execution enabled:
- Agent-generated code introduces additional risk
- Sandbox escape is the primary threat vector
- Defense-in-depth is critical

### Credential Isolation

Each provider's credentials should be:
- Stored separately in Secrets Manager
- Accessed with minimum necessary IAM permissions
- Rotated independently
- Never accessible to user code

### Blast Radius

A compromise of one provider's credentials should not affect others:
- Separate secrets per provider
- No shared authentication tokens
- Independent session management
- Code sandbox cannot access credentials

## Data Security

### Combined Data Access

This service can access:

| Provider | Data Types |
|----------|------------|
| Outlook | Email, Calendar, Contacts |
| SharePoint | Documents, Sites, Lists |
| Teams | Chats, Channels, Meetings |
| Azure DevOps | Code, Pipelines, PRs |
| Snowflake | Database queries |

### Data Handling Principles

- **No cross-provider data mixing**: Data from one provider not used with another
- **No persistent storage**: All data is pass-through
- **Provider isolation**: Each provider operates independently
- **Code execution filtering**: Only processed results return to model

### Code Execution Data Flow

```
Provider API ──→ Tool Result ──→ Sandbox Processing ──→ Filtered Result ──→ Model
                                      │
                                      └── Intermediate data stays in sandbox
                                          (never sent to model context)
```

## Credential Management

### Required Secrets by Provider

#### Microsoft Providers (Outlook, SharePoint, Teams)
| Secret | Purpose |
|--------|---------|
| `MICROSOFT_CLIENT_SECRET` | OAuth authentication |
| `TOKEN_ENCRYPTION_KEY` | Token at-rest encryption |

#### Azure DevOps
| Secret | Purpose |
|--------|---------|
| `AZURE_DEVOPS_PAT` | API authentication |

#### Snowflake
| Secret | Purpose |
|--------|---------|
| `SNOWFLAKE_PASSWORD` | Database authentication |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Key-pair auth (if used) |

### Secrets Rotation Schedule

| Provider | Credential | Rotation Frequency |
|----------|------------|-------------------|
| Microsoft | Client Secret | 90 days |
| Microsoft | Encryption Key | Quarterly |
| Azure DevOps | PAT | 90 days |
| Snowflake | Password | 90 days |
| Snowflake | Key-pair | Quarterly |

## Network Security

### Outbound Connections

| Provider | Destination |
|----------|-------------|
| Microsoft | graph.microsoft.com |
| Microsoft | login.microsoftonline.com |
| Azure DevOps | dev.azure.com |
| Snowflake | *.snowflakecomputing.com |

### Code Execution Network

| Component | Network Access |
|-----------|---------------|
| Deno Sandbox | localhost only (callback to Python) |
| Docker Sandbox | none (host.docker.internal for callback) |
| Python Backend | Provider APIs only |

### Firewall Configuration

Allow outbound to all provider APIs:

```
Outbound: 443 → graph.microsoft.com
Outbound: 443 → login.microsoftonline.com
Outbound: 443 → dev.azure.com
Outbound: 443 → *.snowflakecomputing.com
```

For code execution:
```
Internal: 8001 → localhost (Deno callback)
Internal: 9001-900X → localhost (Docker pool callbacks)
```

## Provider Enablement Security

### Principle of Least Privilege

Enable only required providers:

```bash
# Good: Enable only what's needed
ENABLED_PROVIDERS=outlook,sharepoint

# Avoid: Enabling unused providers
ENABLED_PROVIDERS=outlook,sharepoint,teams,azuredevops,snowflake
```

### Code Execution Enablement

Only enable code execution when needed:

```bash
# Standard mode (more secure)
CODE_EXECUTION_ENABLED=false

# Code execution (additional attack surface)
CODE_EXECUTION_ENABLED=true
SANDBOX_MODE=docker  # More isolated than Deno
```

### Runtime Provider Restrictions

Disabled providers:
- Are not initialized
- Cannot be accessed via any endpoint
- Have credentials not loaded into memory

## Audit Logging

### Cross-Provider Audit Trail

| Event | Level | Data |
|-------|-------|------|
| Service startup | INFO | enabled providers, sandbox mode |
| Provider access | INFO | provider, user, operation |
| Cross-provider request | INFO | source provider, target |
| Auth failure | WARN | provider, reason |
| Code execution | INFO | code hash, user, duration |
| Sandbox violation | WARN | pattern detected, blocked |

### Code Execution Logging

| Event | Level | Data |
|-------|-------|------|
| Execution start | INFO | user, timeout, code hash |
| Tool callback | DEBUG | provider, tool, arguments |
| Execution complete | INFO | success, duration, tools called |
| Validation failure | WARN | blocked pattern, code hash |
| Timeout | WARN | user, duration |
| Rate limit | WARN | user, requests count |

### Provider-Specific Logging

Each provider maintains its own audit trail. See:
- [mcp-outlook-service/SECURITY.md](../mcp-outlook-service/SECURITY.md)
- [mcp-sharepoint-service/SECURITY.md](../mcp-sharepoint-service/SECURITY.md)
- [mcp-teams-service/SECURITY.md](../mcp-teams-service/SECURITY.md)
- [mcp-azuredevops-service/SECURITY.md](../mcp-azuredevops-service/SECURITY.md)
- [mcp-snowflake-service/SECURITY.md](../mcp-snowflake-service/SECURITY.md)

## Incident Response

### Multi-Provider Breach

If the combined service is compromised:

1. **Immediate actions**:
   - Disable the service
   - Revoke ALL provider credentials
   - Rotate ALL secrets

2. **Per-provider assessment**:
   - Review Microsoft audit logs (Azure AD, Graph)
   - Review Azure DevOps audit logs
   - Review Snowflake query history

3. **Scope determination**:
   - Which providers were accessed?
   - What data was potentially exposed?
   - What operations were performed?

### Code Execution Security Incident

If sandbox escape or malicious code execution is detected:

1. **Immediate actions**:
   - Disable code execution (`CODE_EXECUTION_ENABLED=false`)
   - Kill all sandbox containers/processes
   - Review execution logs

2. **Investigation**:
   - Identify the malicious code pattern
   - Check if provider APIs were accessed
   - Review tool callback logs

3. **Remediation**:
   - Update static analysis patterns
   - Patch sandbox vulnerabilities
   - Re-enable with enhanced monitoring

### Single Provider Credential Compromise

If one provider's credentials are compromised:

1. Rotate only that provider's credentials
2. Other providers remain unaffected
3. Review that provider's audit logs
4. No need to rotate other credentials

## Vulnerability Mitigations

### Combined Service Risks

| Risk | Mitigation |
|------|------------|
| Single point of failure | Health checks, auto-restart |
| Increased attack surface | Enable only needed providers |
| Complex credential management | Secrets Manager per provider |
| Cross-provider data leak | Provider isolation |

### Code Execution Risks

| Risk | Mitigation |
|------|------------|
| Sandbox escape | V8 isolates (Deno), cgroups+seccomp (Docker) |
| Resource exhaustion | Memory limits, timeouts, rate limiting |
| Credential theft | Tokens never in user code |
| Arbitrary network access | Network disabled, callback-only |
| Malicious code patterns | Static analysis before execution |
| Privilege escalation | no-new-privileges, seccomp |

### Provider-Specific Mitigations

See individual provider security documentation for:
- SQL injection (Snowflake)
- Email spoofing (Outlook)
- Document access (SharePoint)
- Message integrity (Teams)
- Code exposure (Azure DevOps)

## Compliance

### Combined Compliance Considerations

Running multiple providers may affect:
- Data residency (different provider data centers)
- Audit requirements (multiple audit trails)
- Access controls (different permission models)

### Code Execution Compliance

| Requirement | Implementation |
|-------------|----------------|
| Code audit trail | All executions logged with hash |
| Data isolation | Sandbox prevents data exfiltration |
| Access control | Token validation per tool call |
| Rate limiting | Per-user execution limits |

### Per-Provider Compliance

| Provider | Key Compliance Features |
|----------|------------------------|
| Microsoft | Azure AD policies, DLP |
| Azure DevOps | Organization policies |
| Snowflake | Row access, masking |

## Security Checklist

### Pre-Production

- [ ] Enable only required providers
- [ ] Each provider's credentials in separate secrets
- [ ] OAuth Gateway secured (for Microsoft)
- [ ] TLS enabled for all endpoints
- [ ] Per-provider audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured

### Code Execution (If Enabled)

- [ ] Choose appropriate sandbox mode (Docker for production)
- [ ] Static analysis patterns reviewed
- [ ] Execution timeouts configured
- [ ] Memory limits set
- [ ] Rate limiting enabled
- [ ] Seccomp profile deployed (Docker)
- [ ] Container images from trusted source

### Credential Management

- [ ] All secrets in Secrets Manager
- [ ] Rotation schedule documented
- [ ] Rotation alerts configured
- [ ] Emergency revocation procedure per provider

### Ongoing

- [ ] Review all provider access patterns (weekly)
- [ ] Review code execution logs (daily if enabled)
- [ ] Rotate credentials per schedule
- [ ] Update dependencies (monthly)
- [ ] Update sandbox runtime (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
