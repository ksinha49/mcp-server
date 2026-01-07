# Security Guide - MCP Teams Service

## Overview

This MCP server provides access to Microsoft Teams chats, channels, and meetings. This document covers security considerations, best practices, and compliance requirements for handling communication data.

## Security Architecture

### Authentication Flow

```
1. MCP Client sends request with OAuth token
2. Service validates token via OAuth Gateway
3. Service uses delegated token to call Microsoft Graph
4. Response returned to MCP Client
```

### Token Delegation

This service uses **delegated permissions** - it acts on behalf of the authenticated user. Users can only access Teams content they have permissions to access in the native Teams interface.

## Microsoft Graph API Permissions

### Minimum Required Permissions

| Permission | Purpose | Risk Level |
|------------|---------|------------|
| `User.Read` | User profile | Low |
| `Team.ReadBasic.All` | List teams | Low |
| `Channel.ReadBasic.All` | List channels | Low |
| `ChannelMessage.Read.All` | Read messages | Medium |
| `ChannelMessage.Send` | Send messages | High |
| `Chat.Read` | Read chats | Medium |
| `Chat.ReadWrite` | Send chats | High |
| `OnlineMeetings.Read` | Meeting details | Medium |

### Permission Recommendations

1. **Start with read-only**: Begin with read permissions only
2. **Add send when needed**: Only add send permissions for specific use cases
3. **Audit messaging**: Log all sent messages
4. **User consent**: Consider whether user or admin consent is appropriate

## Data Security

### Data Handled

| Data Type | Sensitivity | Retention |
|-----------|-------------|-----------|
| Chat messages | High | Not stored |
| Channel messages | Medium | Not stored |
| Team membership | Low | Not stored |
| Meeting details | Medium | Not stored |
| OAuth tokens | High | Encrypted |

### Communication Privacy

Teams messages may contain:
- Confidential business discussions
- Personal information
- File attachments (links only)
- Sensitive project details

**Important**: This service provides access to communication content. Ensure compliance with data handling and privacy policies.

### Data Handling Principles

- **No storage**: Message content is never persisted
- **Pass-through**: Data flows from Graph API to MCP client
- **Token encryption**: OAuth tokens encrypted at rest
- **No message modification**: Cannot edit or delete messages

## Token Security

### Token Validation

Every request validates:
- Token signature (via OAuth Gateway)
- Token expiration
- Audience claim (must match this service)
- Issuer (must be expected identity provider)

### Teams-Specific Considerations

- Team membership enforced by Teams, not this service
- Channel access requires team membership
- Private channel access restricted to members

## Network Security

### Recommended Deployment

```
Internet → ALB (TLS) → Teams Service (private subnet)
                              ↓
                       OAuth Gateway (private subnet)
                              ↓
                       Microsoft Graph API (external)
```

### TLS Requirements

- **Inbound**: TLS 1.2+ required
- **Outbound to Graph**: TLS 1.2+ (Microsoft enforced)
- **Outbound to OAuth Gateway**: TLS 1.2+ recommended

### Firewall Rules

| Direction | Destination | Port | Purpose |
|-----------|-------------|------|---------|
| Outbound | graph.microsoft.com | 443 | Graph API |
| Outbound | login.microsoftonline.com | 443 | Token validation |
| Outbound | OAuth Gateway | 8000 | Token operations |
| Inbound | Load Balancer | 8003 | Service traffic |

## Input Validation

### MCP Tool Inputs

| Tool | Validation |
|------|------------|
| `list_teams` | Max results limited |
| `get_team` | Team ID format validated |
| `list_channels` | Team ID validated, max results limited |
| `list_messages` | Channel ID validated, pagination enforced |
| `send_message` | Content sanitized, length limited |
| `list_chat_messages` | Chat ID validated, pagination enforced |
| `send_chat_message` | Content sanitized, length limited |
| `get_meeting` | Meeting ID format validated |

### Message Content Security

- Message length limits enforced
- HTML/markdown content validated
- Mention formats validated
- No script injection possible (Graph API sanitizes)

## Rate Limiting

### Microsoft Graph Limits

Microsoft Graph enforces rate limits:
- Per-user throttling
- Per-tenant throttling
- Teams-specific limits

### Recommended Application Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Team listings | 30 | per minute |
| Message reads | 60 | per minute |
| Message sends | 20 | per minute |
| Chat operations | 30 | per minute |

## Audit Logging

### Events to Log

| Event | Level | Data |
|-------|-------|------|
| Team access | INFO | team ID, user |
| Channel access | INFO | channel ID, message count |
| Message sent | INFO | channel/chat ID, length |
| Chat access | INFO | chat ID, user |
| Auth failure | WARN | reason, client info |
| Permission denied | WARN | operation, team/channel ID |

### Sensitive Data in Logs

**Never log**:
- Message content
- Chat participants' names
- Meeting attendees
- OAuth tokens

**Safe to log**:
- Team/channel IDs
- Operation types
- Message counts
- Timestamps
- Error codes

## Vulnerability Mitigations

### OWASP Considerations

| Risk | Mitigation |
|------|------------|
| Injection | SDK parameterization, input validation |
| Broken Auth | OAuth 2.1, token validation |
| Sensitive Data | No storage, encryption in transit |
| XXE | No XML processing |
| Access Control | Teams permissions enforced |

### Communication-Specific Risks

| Risk | Mitigation |
|------|------------|
| Message impersonation | Messages sent as authenticated user |
| Chat snooping | Delegated access only |
| Spam via send | Rate limiting, audit logging |
| Data exfiltration | No bulk export, pagination limits |

## Incident Response

### Unauthorized Message Access

1. Identify affected teams/chats via logs
2. Check user's Teams membership
3. Review OAuth token grants
4. Revoke tokens if compromised
5. Audit message access patterns

### Unauthorized Message Sends

1. Identify sent messages via logs
2. Check if user initiated sends
3. Revoke active sessions
4. Notify affected team/chat members
5. Work with Teams admin to review/delete if needed

### Compromised OAuth Token

1. Revoke token via OAuth Gateway
2. Force user re-authentication
3. Audit recent message access/sends
4. Review sent messages for unauthorized activity

## Compliance

### Supported Standards

- **OAuth 2.1**: Authentication standard
- **MCP 2025-06-18**: Protocol compliance
- **RFC 8707**: Token audience binding

### Data Protection Considerations

- **GDPR**: No message storage; consider eDiscovery requirements
- **HIPAA**: Not recommended for PHI without additional controls
- **SOC 2**: Compatible with proper logging and access controls
- **Legal Hold**: Service does not interfere with Microsoft compliance features

### Teams Compliance Features

This service respects native Teams compliance:
- Data retention policies
- eDiscovery holds
- Communication compliance
- Information barriers

## Security Checklist

### Pre-Production

- [ ] OAuth Gateway configured and secured
- [ ] TLS enabled for all endpoints
- [ ] Minimum Graph permissions granted
- [ ] Admin consent for required permissions
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Network isolation configured
- [ ] Message send logging enabled

### Ongoing

- [ ] Review Teams access patterns (weekly)
- [ ] Review Azure AD permissions (quarterly)
- [ ] Rotate client secrets (quarterly)
- [ ] Update dependencies (monthly)
- [ ] Security assessment (annually)

## Reporting Security Issues

Report security vulnerabilities privately to the security team. Do not open public issues for security concerns.
