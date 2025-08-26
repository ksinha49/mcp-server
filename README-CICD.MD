
## Directory Structure

```
/
├── mcp-service-1/
│   ├── Dockerfile
│   ├── app
│       ├── main.py
│   ├── requirements.txt
│   ├── environment
|        ├──prod
|             ├──github.properties
|             ├──ecs-task-definition.json
├── mcp-service-2/
│   ├── Dockerfile
│   ├── app
│       ├── main.py
│   ├── requirements.txt
│   ├── environment
|        ├──prod
|             ├──github.properties
|             ├──ecs-task-definition.json
└── .github/workflows/deploy.yml

```
