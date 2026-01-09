# Enterprise MCP Registry Infrastructure Plan

## Objective
Evaluate the current ECS/Fargate infrastructure setup, design cross-account integration with LiteLLM at `api.ai.inbison.com/v1/mcp`, and define requirements for an enterprise MCP registry.

---

## Executive Summary

### Does the Current Setup Make Practical Sense?

**Partial Yes, But Significant Gaps Exist**

| Aspect | Status | Assessment |
|--------|--------|------------|
| Container Configuration | ✅ Solid | 9 task definitions, multi-stage Dockerfiles, health checks |
| Secrets Management | ✅ Solid | 15 secrets + 7 SSM parameters, proper separation |
| MCP 2025-06-18 Compliance | ✅ Complete | OAuth 2.1/PKCE, protected resource metadata |
| Code Execution Layer | ✅ Complete | Dual-sandbox (Deno/Docker) just implemented |
| Infrastructure as Code | ❌ Missing | No Terraform/CloudFormation - manual deployment only |
| Load Balancer | ❌ Missing | Documented but not provisioned |
| Auto-Scaling | ❌ Missing | No scaling policies defined |
| Service Discovery | ❌ Missing | Hard-coded URLs, no Cloud Map |
| Cross-Account Ready | ❌ Not Ready | No PrivateLink/Transit Gateway configuration |

**Bottom Line**: The application layer is production-ready; the infrastructure layer needs significant work before cross-account LiteLLM integration.

---

## Current State Analysis

### 1. ECS Task Definitions (Complete)

```
Service                  │ CPU  │ Memory │ Port │ Status
─────────────────────────┼──────┼────────┼──────┼────────
OAuth Gateway            │ 512  │ 1024MB │ 8000 │ ✅ Defined
Outlook MCP              │ 256  │ 512MB  │ 8001 │ ✅ Defined
SharePoint MCP           │ 256  │ 512MB  │ 8002 │ ✅ Defined
Teams MCP                │ 256  │ 512MB  │ 8003 │ ✅ Defined
Azure DevOps MCP         │ 256  │ 512MB  │ 8004 │ ✅ Defined
Snowflake MCP            │ 256  │ 512MB  │ 8005 │ ✅ Defined
Context7 MCP             │ 256  │ 512MB  │ 8006 │ ✅ Defined
Combined MCP             │ 512  │ 1024MB │ 8000 │ ✅ Defined
```

### 2. What's Actually Deployed vs Documented

| Resource | In Task Definitions | Actually Provisioned |
|----------|---------------------|----------------------|
| ECS Cluster | Referenced (`mcp-cluster`) | ❓ Unknown |
| ECS Services | Not defined | ❓ Unknown |
| ALB | Documented in SECURITY.md | ❌ Not in IaC |
| Target Groups | Referenced | ❌ Not in IaC |
| Security Groups | Referenced (`sg-0dd2ea27864c7af6d`) | ❓ Exists |
| VPC/Subnets | Referenced in github.properties | ❓ Exists |
| Cloud Map | Not configured | ❌ No |
| Auto-Scaling | Not configured | ❌ No |

### 3. Network Architecture (Current)

```
Internet
    ↓
[No WAF] ← Gap
    ↓
[ALB - Assumed to exist externally]
    ↓
┌─────────────────────────────────────────────────┐
│ VPC (presumably existing)                        │
│  ┌────────────────────────────────────────────┐ │
│  │ Private Subnets                             │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │ │
│  │  │OAuth GW │ │Outlook  │ │SharePt  │ ...   │ │
│  │  │:8000    │ │:8001    │ │:8002    │       │ │
│  │  └─────────┘ └─────────┘ └─────────┘       │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [No Service Discovery] ← Gap                   │
│  [No Cross-Account Config] ← Gap                │
└─────────────────────────────────────────────────┘
```

---

## Cross-Account LiteLLM Integration Architecture

### Target Architecture: api.ai.inbison.com/v1/mcp

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONSUMER ACCOUNT (LiteLLM)                       │
│                     api.ai.inbison.com                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Route 53 + CloudFront                     │    │
│  │                    api.ai.inbison.com                        │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Application Load Balancer (ALB)                 │    │
│  │              TLS 1.3, WAF Integration                        │    │
│  │              /v1/* → LiteLLM                                 │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   LiteLLM Proxy (ECS)                        │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │  MCP Gateway Module                                   │   │    │
│  │  │  - Auto-discovers tools from MCP servers              │   │    │
│  │  │  - Routes tool calls to appropriate server            │   │    │
│  │  │  - OpenAI-compatible API                              │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         VPC Endpoints (PrivateLink Consumer)                 │    │
│  │         Connects to MCP Provider Account                     │    │
│  └────────────────────────────┬────────────────────────────────┘    │
└───────────────────────────────┼─────────────────────────────────────┘
                                │
          AWS PrivateLink (Private, No Internet)
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                     PROVIDER ACCOUNT (MCP Servers)                   │
│                     Your Current Repository                          │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         VPC Endpoint Service (PrivateLink Provider)          │    │
│  │         Exposes NLB to Consumer Account                      │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Network Load Balancer (Private)                 │    │
│  │              Internal-only, no internet access               │    │
│  │  ┌─────────────────────────────────────────────────────────┐│    │
│  │  │ Target Groups                                           ││    │
│  │  │  :8000 → OAuth Gateway / Combined Service               ││    │
│  │  │  :8001 → Outlook MCP                                    ││    │
│  │  │  :8002 → SharePoint MCP                                 ││    │
│  │  │  :8003 → Teams MCP                                      ││    │
│  │  │  :8004 → Azure DevOps MCP                               ││    │
│  │  │  :8005 → Snowflake MCP                                  ││    │
│  │  │  :8006 → Context7 MCP                                   ││    │
│  │  └─────────────────────────────────────────────────────────┘│    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    ECS Cluster (Fargate)                     │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │    │
│  │  │Combined │ │Outlook  │ │SharePt  │ │Teams    │ ...        │    │
│  │  │Service  │ │MCP      │ │MCP      │ │MCP      │            │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   AWS Cloud Map (Service Discovery)          │    │
│  │                   Shared via AWS RAM                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cross-Account Method | **AWS PrivateLink** | Most secure, no internet exposure, works with CIDR overlaps |
| Internal LB | **NLB (not ALB)** | Required for PrivateLink endpoint services |
| Service Discovery | **Cloud Map + RAM** | Native ECS integration, cross-account sharing |
| MCP Gateway | **LiteLLM** | Native MCP support, OpenAI-compatible, multi-provider |
| External API | **api.ai.inbison.com** | Custom domain on consumer account's ALB |

### Alternative: Transit Gateway (If More Services Needed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Hub Account                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              AWS Transit Gateway                             │    │
│  │              (Shared via RAM to all accounts)                │    │
│  └────────────────────────┬────────────────────────────────────┘    │
│                           │                                          │
│           ┌───────────────┼───────────────┐                         │
│           ↓               ↓               ↓                         │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐                    │
│   │ LiteLLM   │   │   MCP     │   │  Other    │                    │
│   │ Account   │   │ Provider  │   │ Services  │                    │
│   └───────────┘   └───────────┘   └───────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Use Transit Gateway if:**
- You need bidirectional communication between many accounts
- You have 4+ accounts that need mesh connectivity
- Cost is less concern than simplicity

**Use PrivateLink if:**
- One-way service exposure (MCP provider → LiteLLM consumer)
- Maximum security isolation required
- Selective API exposure

---

## LiteLLM MCP Integration Details

### LiteLLM Configuration for MCP Servers

```yaml
# litellm_config.yaml
model_list:
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: gpt-4
    litellm_params:
      model: gpt-4-turbo
      api_key: os.environ/OPENAI_API_KEY

# MCP Server Configuration
mcp_servers:
  - name: enterprise-combined
    url: "http://mcp-combined.internal:8000/mcp"  # Via PrivateLink
    transport: streamable-http
    description: "Combined MCP server with all enterprise tools"

  - name: outlook
    url: "http://mcp-outlook.internal:8001/mcp"
    transport: streamable-http

  - name: snowflake
    url: "http://mcp-snowflake.internal:8005/mcp"
    transport: streamable-http

# Rate limiting
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL

litellm_settings:
  drop_params: true
  set_verbose: false
```

### How LiteLLM + MCP Works

```
Client Request (api.ai.inbison.com/v1/chat/completions)
    ↓
┌────────────────────────────────────────────────┐
│ LiteLLM Proxy                                   │
│  1. Validate API key                           │
│  2. Fetch tools from MCP servers               │
│  3. Convert MCP tools → OpenAI format          │
│  4. Send to LLM with tools                     │
└────────────────────────────────────────────────┘
    ↓
LLM Response (with tool_calls)
    ↓
┌────────────────────────────────────────────────┐
│ LiteLLM MCP Router                              │
│  1. Parse tool_call arguments                  │
│  2. Route to correct MCP server                │
│  3. Execute tool via MCP protocol              │
│  4. Return result to LLM                       │
└────────────────────────────────────────────────┘
    ↓
Final Response to Client
```

### Benefits of LiteLLM Layer

| Benefit | Description |
|---------|-------------|
| **Model Agnostic** | Same MCP tools work with Claude, GPT-4, Bedrock, etc. |
| **OpenAI Compatible** | Standard API, works with existing clients |
| **Cost Tracking** | Per-user, per-project spend management |
| **Rate Limiting** | Protect MCP servers from abuse |
| **Caching** | Reduce redundant MCP calls |
| **Virtual Keys** | Secure access without exposing real credentials |
| **Fallbacks** | Automatic failover between models |

---

## Gap Analysis & Implementation Roadmap

### Phase 1: Infrastructure as Code (Required First)

**Current Gap**: No CloudFormation exists

**Create**: `infrastructure/cloudformation/`

```
infrastructure/
├── cloudformation/
│   ├── templates/
│   │   ├── vpc-stack.yaml              # VPC, Subnets, NAT Gateway
│   │   ├── ecs-cluster-stack.yaml      # ECS Cluster, Capacity Providers
│   │   ├── mcp-services-stack.yaml     # All MCP ECS Services
│   │   ├── nlb-stack.yaml              # Internal NLB + Target Groups
│   │   ├── privatelink-stack.yaml      # VPC Endpoint Service
│   │   ├── cloud-map-stack.yaml        # Service Discovery Namespace
│   │   ├── security-groups-stack.yaml  # Security Groups
│   │   ├── iam-stack.yaml              # IAM Roles + Policies
│   │   └── autoscaling-stack.yaml      # Auto-scaling Policies
│   │
│   ├── nested/                         # Reusable nested stacks
│   │   ├── ecs-service.yaml            # Single ECS Service template
│   │   └── target-group.yaml           # Single Target Group template
│   │
│   ├── parameters/
│   │   ├── prod.json                   # Production parameters
│   │   └── staging.json                # Staging parameters
│   │
│   └── scripts/
│       ├── deploy.sh                   # Deploy all stacks
│       ├── validate.sh                 # Validate templates
│       └── package.sh                  # Package nested stacks to S3
```

**CloudFormation Stacks to Create**:
- [ ] `mcp-vpc-stack` - VPC (if not using existing)
- [ ] `mcp-iam-stack` - IAM Roles + Policies
- [ ] `mcp-security-groups-stack` - Security Groups
- [ ] `mcp-ecs-cluster-stack` - ECS Cluster
- [ ] `mcp-cloud-map-stack` - Service Discovery Namespace
- [ ] `mcp-nlb-stack` - Network Load Balancer (internal) + Target Groups
- [ ] `mcp-services-stack` - All MCP ECS Services (nested)
- [ ] `mcp-autoscaling-stack` - Auto-scaling Policies
- [ ] `mcp-privatelink-stack` - VPC Endpoint Service

---

## Enterprise MCP Registry Requirements

### What Makes an Enterprise MCP Registry?

| Capability | Description | Your Current Status |
|------------|-------------|---------------------|
| **Service Catalog** | Discoverable list of available MCP servers | ❌ Manual, hard-coded |
| **Governance** | Allowlisting, approval workflows | ❌ None |
| **Authentication** | OAuth 2.1, API keys, mTLS | ✅ OAuth Gateway exists |
| **Authorization** | Per-user, per-team tool access | ⚠️ Basic (token-based) |
| **Rate Limiting** | Protect services from abuse | ❌ Not implemented |
| **Audit Logging** | Who accessed what, when | ⚠️ CloudWatch only |
| **Versioning** | Multiple versions of same tool | ❌ Not implemented |
| **Health Monitoring** | Service availability dashboard | ⚠️ Health checks exist |
| **Documentation** | Auto-generated API docs | ❌ Manual only |

### Enterprise Registry Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Enterprise MCP Registry                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Registry API                              │   │
│  │  GET  /registry/servers     → List available MCP servers     │   │
│  │  GET  /registry/servers/:id → Get server details + tools     │   │
│  │  POST /registry/servers     → Register new server (admin)    │   │
│  │  GET  /registry/tools       → Search all tools               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Governance Layer                          │   │
│  │  - Allowlist policies (which servers approved)               │   │
│  │  - Access control (which teams can use which tools)          │   │
│  │  - Audit trail (all registry operations logged)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Service Discovery                         │   │
│  │  - AWS Cloud Map integration                                 │   │
│  │  - Health status aggregation                                 │   │
│  │  - Version management                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Additional Components Needed

1. **Registry Service** (New microservice)
   - Database: DynamoDB or PostgreSQL for server metadata
   - API: FastAPI endpoints for registry operations
   - Integration: AWS Cloud Map for live service discovery

2. **Admin Portal** (New frontend)
   - Server registration and approval
   - Tool browser and documentation
   - Access policy management

3. **SDK/CLI** (New tooling)
   - `mcp-registry list` - List available servers
   - `mcp-registry install <server>` - Configure client for server
   - `mcp-registry publish` - Register new server

4. **Governance Policies** (IAM + Custom)
   - AWS Service Control Policies for account boundaries
   - Custom allowlist enforcement in registry API
   - Per-team tool access matrices

---

## Shortfalls & Risks

### 1. Immediate Blockers

| Issue | Impact | Resolution |
|-------|--------|------------|
| No IaC | Can't reliably deploy | Create CloudFormation stacks |
| No NLB | Can't use PrivateLink | Provision internal NLB |
| No Service Discovery | Hard to manage at scale | Implement Cloud Map |
| No Auto-scaling | Can't handle load spikes | Add scaling policies |

### 2. Security Gaps

| Gap | Risk | Mitigation |
|-----|------|------------|
| No WAF | DDoS, injection attacks | Add AWS WAF to ALB |
| No mTLS | Service-to-service spoofing | Implement mTLS or use PrivateLink |
| Root containers | Container escape risk | Add non-root users to Dockerfiles |
| No rate limiting | Resource exhaustion | Add per-user limits in LiteLLM |

### 3. Operational Gaps

| Gap | Impact | Solution |
|-----|--------|----------|
| No dashboards | Blind to issues | CloudWatch dashboards |
| No alerting | Slow incident response | CloudWatch alarms + PagerDuty |
| No runbooks | Inconsistent troubleshooting | Document operational procedures |
| No DR plan | Extended downtime | Multi-AZ + backup procedures |

---

## Implementation Priority

### Immediate (Week 1-2)
1. Create CloudFormation stacks for core infrastructure
2. Provision NLB and target groups
3. Create ECS Services (not just task definitions)
4. Enable Cloud Map service discovery

### Short-term (Week 3-4)
5. Configure PrivateLink endpoint service
6. Deploy LiteLLM in consumer account
7. Configure VPC endpoint in consumer account
8. Test end-to-end MCP tool discovery

### Medium-term (Week 5-8)
9. Add WAF to external ALB
10. Implement auto-scaling policies
11. Build registry API service
12. Create admin portal

### Long-term (Month 3+)
13. Implement governance policies
14. Build SDK/CLI tooling
15. Add multi-region support
16. Implement DR procedures

---

## Verification Plan

### Test PrivateLink Connectivity
```bash
# From LiteLLM consumer account
curl http://vpce-xxx.vpce-svc-xxx.us-east-2.vpce.amazonaws.com:8000/health
# Expected: {"status": "healthy", "service": "mcp-combined-service"}
```

### Test LiteLLM MCP Integration
```bash
# List discovered MCP tools
curl http://localhost:4000/mcp/tools \
  -H "Authorization: Bearer sk-xxx"

# Execute chat with MCP tools
curl http://api.ai.inbison.com/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus",
    "messages": [{"role": "user", "content": "Search my emails for urgent messages"}],
    "tools": "auto"
  }'
```

### Verify Cross-Account Security
```bash
# Should fail from unauthorized account
aws ec2 describe-vpc-endpoint-services \
  --service-names com.amazonaws.vpce.us-east-2.vpce-svc-xxx \
  --profile unauthorized-account
# Expected: Access Denied
```

---

## Summary

### Does This Make Practical Sense?

**Yes, with the right architecture:**

1. **LiteLLM as MCP Gateway** - Native support, battle-tested, adds value (multi-model, cost tracking)
2. **PrivateLink for Cross-Account** - Most secure, no internet exposure
3. **Your MCP Servers** - Well-designed, MCP 2025-06-18 compliant, ready for integration

### What's Missing?

1. **Infrastructure as Code** - Critical blocker, must create CloudFormation stacks first
2. **Network Load Balancer** - Required for PrivateLink
3. **Service Discovery** - Needed for scalable operations
4. **Registry Service** - Required for enterprise governance

### Recommended Path

```
Current State → Add IaC → Deploy NLB → Enable PrivateLink → Deploy LiteLLM → Build Registry
     ↓              ↓           ↓              ↓                ↓              ↓
  Manual       CloudFormation Internal    Cross-Account      Gateway      Enterprise
 Deployment      Stacks     Load Balancer  Connectivity       Ready        Ready
```

### CloudFormation Stack Deployment Order

```bash
# 1. Foundation stacks (Provider Account)
aws cloudformation deploy --stack-name mcp-iam --template-file iam-stack.yaml
aws cloudformation deploy --stack-name mcp-security-groups --template-file security-groups-stack.yaml
aws cloudformation deploy --stack-name mcp-cloud-map --template-file cloud-map-stack.yaml

# 2. Networking (Provider Account)
aws cloudformation deploy --stack-name mcp-nlb --template-file nlb-stack.yaml

# 3. Services (Provider Account)
aws cloudformation deploy --stack-name mcp-services --template-file mcp-services-stack.yaml

# 4. PrivateLink (Provider Account)
aws cloudformation deploy --stack-name mcp-privatelink --template-file privatelink-stack.yaml

# 5. Consumer Account stacks
aws cloudformation deploy --stack-name mcp-vpc-endpoint --template-file vpc-endpoint-stack.yaml
aws cloudformation deploy --stack-name litellm --template-file litellm-stack.yaml
aws cloudformation deploy --stack-name api-alb --template-file api-alb-stack.yaml
```

**Estimated Effort**: 4-6 weeks for basic cross-account integration, 2-3 months for full enterprise registry
