# Context7 MCP - 모든 프롬프트를 위한 최신 코드 문서

[![Website](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com) [![smithery badge](https://smithery.ai/badge/@upstash/context7-mcp)](https://smithery.ai/server/@upstash/context7-mcp) [<img alt="Install in VS Code (npx)" src="https://img.shields.io/badge/VS_Code-VS_Code?style=flat-square&label=Install%20Context7%20MCP&color=0098FF">](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%7B%22name%22%3A%22context7%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40upstash%2Fcontext7-mcp%40latest%22%5D%7D)

[![繁體中文](https://img.shields.io/badge/docs-繁體中文-yellow)](./docs/README.zh-TW.md) [![简体中文](https://img.shields.io/badge/docs-简体中文-yellow)](./docs/README.zh-CN.md) [![日本語](https://img.shields.io/badge/docs-日本語-b7003a)](./docs/README.ja.md) [![한국어 문서](https://img.shields.io/badge/docs-한국어-green)](./docs/README.ko.md) [![Documentación en Español](https://img.shields.io/badge/docs-Español-orange)](./docs/README.es.md) [![Documentation en Français](https://img.shields.io/badge/docs-Français-blue)](./docs/README.fr.md) [![Documentação em Português (Brasil)](<https://img.shields.io/badge/docs-Português%20(Brasil)-purple>)](./docs/README.pt-BR.md) [![Documentazione in italiano](https://img.shields.io/badge/docs-Italian-red)](./docs/README.it.md) [![Dokumentasi Bahasa Indonesia](https://img.shields.io/badge/docs-Bahasa%20Indonesia-pink)](./docs/README.id-ID.md) [![Dokumentation auf Deutsch](https://img.shields.io/badge/docs-Deutsch-darkgreen)](./docs/README.de.md) [![Документация на русском языке](https://img.shields.io/badge/docs-Русский-darkblue)](./docs/README.ru.md) [![Türkçe Doküman](https://img.shields.io/badge/docs-Türkçe-blue)](./docs/README.tr.md) [![Arabic Documentation](https://img.shields.io/badge/docs-Arabic-white)](./docs/README.ar.md)

## ❌ Context7 없이

LLM은 사용하는 라이브러리에 대한 오래되거나 일반적인 정보에 의존하면 다음과 같은 문제가 발생할 수 있습니다:

- ❌ 1년 전 학습 데이터를 기반으로 한 오래된 코드 예제
- ❌ 실제로 존재하지 않는 API에 대한 환각
- ❌ 구 버전 패키지에 대한 일반적인 답변

## ✅ Context7 사용 시

Context7 MCP는 최신 버전별 문서와 코드 예제를 소스에서 직접 가져와 프롬프트에 즉시 적용합니다.

Cursor에서 프롬프트에 `use context7`을 추가하세요:

```txt
쿠키에서 유효한 JWT를 확인하고 인증되지 않은 사용자를 /login으로 리디렉션하는 Next.js 미들웨어를 만들어주세요. use context7
```

```txt
JSON API 응답을 5분 동안 캐시하도록 Cloudflare Worker 스크립트를 구성해주세요. use context7
```

Context7은 최신 코드 예제와 문서를 LLM의 컨텍스트에 즉시 가져옵니다.

- 1️⃣ 평소처럼 자연스럽게 프롬프트 작성
- 2️⃣ `use context7` 키워드 추가
- 3️⃣ 실제 동작하는 코드 답변 받기

탭 전환도, 존재하지 않는 API도, 오래된 코드 생성도 없습니다.

## 📚 프로젝트 추가하기

Context7에 여러분이 좋아하는 라이브러리를 추가(또는 업데이트)하는 방법을 알아보려면 [프로젝트 추가 가이드](./adding-projects.md)를 확인하세요.

## 🛠️ 시작하기

### 요구사항

- Node.js >= v18.0.0
- Cursor, Windsurf, Claude Desktop 또는 다른 MCP 클라이언트

<details>
<summary><b>Smithery를 통한 설치</b></summary>

[Smithery](https://smithery.ai/server/@upstash/context7-mcp)를 통해 모든 클라이언트에 Context7 MCP 서버를 자동으로 설치하려면:

```bash
npx -y @smithery/cli@latest install @upstash/context7-mcp --client <CLIENT_NAME> --key <YOUR_SMITHERY_KEY>
```

Smithery 키는 [Smithery.ai 웹페이지](https://smithery.ai/server/@upstash/context7-mcp)에서 찾을 수 있습니다.

</details>

<details>
<summary><b>Cursor에 설치</b></summary>

다음으로 이동: `Settings` -> `Cursor Settings` -> `MCP` -> `Add new global MCP server`

다음 설정을 Cursor의 `~/.cursor/mcp.json` 파일에 붙여넣는 것이 권장됩니다. 프로젝트 폴더에 `.cursor/mcp.json`을 생성하여 특정 프로젝트에 설치할 수도 있습니다. 자세한 내용은 [Cursor MCP 문서](https://docs.cursor.com/context/model-context-protocol)를 참조하세요.

> Cursor 1.0부터는 아래 설치 버튼으로 한 번에 설치할 수 있습니다.

#### Cursor 원격 서버 연결

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=context7&config=eyJ1cmwiOiJodHRwczovL21jcC5jb250ZXh0Ny5jb20vbWNwIn0%3D)

```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

#### Cursor 로컬 서버 연결

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=context7&config=eyJjb21tYW5kIjoibnB4IC15IEB1cHN0YXNoL2NvbnRleHQ3LW1jcCJ9)

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

<details>
<summary>대안: Bun 사용</summary>

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=context7&config=eyJjb21tYW5kIjoiYnVueCAteSBAdXBzdGFzaC9jb250ZXh0Ny1tY3AifQ%3D%3D)

```json
{
  "mcpServers": {
    "context7": {
      "command": "bunx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary>대안: Deno 사용</summary>

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=context7&config=eyJjb21tYW5kIjoiZGVubyBydW4gLS1hbGxvdy1lbnYgLS1hbGxvdy1uZXQgbnBtOkB1cHN0YXNoL2NvbnRleHQ3LW1jcCJ9)

```json
{
  "mcpServers": {
    "context7": {
      "command": "deno",
      "args": [
        "run",
        "--allow-env=NO_DEPRECATION,TRACE_DEPRECATION",
        "--allow-net",
        "npm:@upstash/context7-mcp"
      ]
    }
  }
}
```

</details>

</details>

<details>
<summary><b>Windsurf에 설치</b></summary>

Windsurf MCP 설정 파일에 다음을 추가하세요. 자세한 내용은 [Windsurf MCP 문서](https://docs.windsurf.com/windsurf/mcp)를 참조하세요.

#### Windsurf 원격 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "serverUrl": "https://mcp.context7.com/sse"
    }
  }
}
```

#### Windsurf 로컬 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Trae에 설치</b></summary>

수동 추가 기능을 사용하여 해당 MCP 서버의 JSON 설정 정보를 입력하세요.
자세한 내용은 [Trae 문서](https://docs.trae.ai/ide/model-context-protocol?_lang=en)를 참조하세요.

#### Trae 원격 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

#### Trae 로컬 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>VS Code에 설치</b></summary>

[<img alt="Install in VS Code (npx)" src="https://img.shields.io/badge/VS_Code-VS_Code?style=flat-square&label=Install%20Context7%20MCP&color=0098FF">](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%7B%22name%22%3A%22context7%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40upstash%2Fcontext7-mcp%40latest%22%5D%7D)
[<img alt="Install in VS Code Insiders (npx)" src="https://img.shields.io/badge/VS_Code_Insiders-VS_Code_Insiders?style=flat-square&label=Install%20Context7%20MCP&color=24bfa5">](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%7B%22name%22%3A%22context7%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40upstash%2Fcontext7-mcp%40latest%22%5D%7D)

VS Code MCP 설정 파일에 다음을 추가하세요. 자세한 내용은 [VS Code MCP 문서](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)를 참조하세요.

#### VS Code 원격 서버 연결

```json
"mcp": {
  "servers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

#### VS Code 로컬 서버 연결

```json
"mcp": {
  "servers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Visual Studio 2022에 설치</b></summary>

[Visual Studio MCP 서버 문서](https://learn.microsoft.com/visualstudio/ide/mcp-servers?view=vs-2022)에 따라 Visual Studio 2022에서 Context7 MCP를 설정할 수 있습니다.

Visual Studio MCP 설정 파일에 다음을 추가하세요(자세한 내용은 [Visual Studio 문서](https://learn.microsoft.com/visualstudio/ide/mcp-servers?view=vs-2022) 참조):

```json
{
  "mcp": {
    "servers": {
      "context7": {
        "type": "http",
        "url": "https://mcp.context7.com/mcp"
      }
    }
  }
}
```

또는 로컬 서버의 경우:

```json
{
  "mcp": {
    "servers": {
      "context7": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"]
      }
    }
  }
}
```

자세한 정보 및 문제 해결은 [Visual Studio MCP 서버 문서](https://learn.microsoft.com/visualstudio/ide/mcp-servers?view=vs-2022)를 참조하세요.

</details>

<details>
<summary><b>Zed에 설치</b></summary>

[Zed 확장 프로그램](https://zed.dev/extensions?query=Context7)을 통해 설치하거나 Zed `settings.json`에 다음을 추가할 수 있습니다. 자세한 내용은 [Zed 컨텍스트 서버 문서](https://zed.dev/docs/assistant/context-servers)를 참조하세요.

```json
{
  "context_servers": {
    "Context7": {
      "command": {
        "path": "npx",
        "args": ["-y", "@upstash/context7-mcp"]
      },
      "settings": {}
    }
  }
}
```

</details>

<details>
<summary><b>Gemini CLI에 설치</b></summary>

자세한 내용은 [Gemini CLI 설정](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md)을 참조하세요.

1.  Gemini CLI 설정 파일을 엽니다. 위치는 `~/.gemini/settings.json`입니다 (`~`는 홈 디렉토리).
2.  `settings.json` 파일의 `mcpServers` 객체에 다음을 추가합니다:

```json
{
  "mcpServers": {
    "context7": {
      "httpUrl": "https://mcp.context7.com/mcp"
    }
  }
}
```

또는 로컬 서버의 경우:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

`mcpServers` 객체가 없으면 새로 만드세요.

</details>

<details>
<summary><b>Claude Code에 설치</b></summary>

이 명령을 실행하세요. 자세한 내용은 [Claude Code MCP 문서](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials#set-up-model-context-protocol-mcp)를 참조하세요.

#### Claude Code 원격 서버 연결

```sh
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

또는 SSE 전송 사용:

```sh
claude mcp add --transport sse context7 https://mcp.context7.com/sse
```

#### Claude Code 로컬 서버 연결

```sh
claude mcp add context7 -- npx -y @upstash/context7-mcp
```

</details>

<details>
<summary><b>Claude Desktop에 설치</b></summary>

Claude Desktop의 `claude_desktop_config.json` 파일에 다음을 추가하세요. 자세한 내용은 [Claude Desktop MCP 문서](https://modelcontextprotocol.io/quickstart/user)를 참조하세요.

```json
{
  "mcpServers": {
    "Context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary>
<b>Cline에 설치</b>
</summary>

다음 지침에 따라 [Cline MCP 서버 마켓플레이스](https://cline.bot/mcp-marketplace)를 통해 Context7을 쉽게 설치할 수 있습니다:

1. **Cline**을 엽니다.
2. 햄버거 메뉴 아이콘(☰)을 클릭하여 **MCP 서버** 섹션으로 들어갑니다.
3. **마켓플레이스** 탭 내의 검색창을 사용하여 *Context7*을 찾습니다.
4. **설치** 버튼을 클릭합니다.

</details>

<details>
<summary><b>BoltAI에 설치</b></summary>

앱의 "설정" 페이지를 열고 "플러그인"으로 이동한 후 다음 JSON을 입력합니다:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

저장되면 채팅에 `get-library-docs`를 입력한 다음 Context7 문서 ID(예: `get-library-docs /nuxt/ui`)를 입력합니다. 자세한 정보는 [BoltAI 문서 사이트](https://docs.boltai.com/docs/plugins/mcp-servers)에서 확인할 수 있습니다. iOS용 BoltAI의 경우 [이 가이드](https://docs.boltai.com/docs/boltai-mobile/mcp-servers)를 참조하세요.

</details>

<details>
<summary><b>Copilot Coding Agent 설치</b></summary>

아래 설정을 Copilot Coding Agent의 `mcp` 섹션(Repository->Settings->Copilot->Coding agent->MCP configuration)에 추가하세요:

```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp",
      "tools": ["get-library-docs", "resolve-library-id"]
    }
  }
}
```

자세한 내용은 [공식 GitHub 문서](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-mcp)를 참고하세요.

</details>

<details>
<summary><b>Docker 사용하기</b></summary>

MCP 서버를 Docker 컨테이너에서 실행하려면:

1. **Docker 이미지 빌드:**

   먼저 프로젝트 루트(또는 원하는 위치)에 `Dockerfile`을 만듭니다:

   <details>
   <summary>Dockerfile 내용 보기</summary>

   ```Dockerfile
   FROM node:18-alpine

   WORKDIR /app

   # 최신 버전 전역 설치
   RUN npm install -g @upstash/context7-mcp

   # 필요한 경우 기본 포트 노출 (선택 사항, MCP 클라이언트 상호 작용에 따라 다름)
   # EXPOSE 3000

   # 서버 실행 기본 명령어
   CMD ["context7-mcp"]
   ```

   </details>

   그런 다음 태그(예: `context7-mcp`)를 사용하여 이미지를 빌드합니다. **Docker Desktop (또는 Docker 데몬)이 실행 중인지 확인하세요.** `Dockerfile`을 저장한 디렉토리에서 다음 명령을 실행합니다:

   ```bash
   docker build -t context7-mcp .
   ```

2. **MCP 클라이언트 설정:**

   MCP 클라이언트 설정을 업데이트하여 Docker 명령을 사용하도록 합니다.

   _cline_mcp_settings.json 예시:_

   ```json
   {
     "mcpServers": {
       "Сontext7": {
         "autoApprove": [],
         "disabled": false,
         "timeout": 60,
         "command": "docker",
         "args": ["run", "-i", "--rm", "context7-mcp"],
         "transportType": "stdio"
       }
     }
   }
   ```

   _참고: 이것은 예시 설정입니다. 이 README의 앞부분에 있는 특정 MCP 클라이언트(Cursor, VS Code 등) 예시를 참조하여 구조를 조정하세요(예: `mcpServers` 대 `servers`). 또한 `args`의 이미지 이름이 `docker build` 명령 중 사용된 태그와 일치하는지 확인하세요._

</details>

<details>
<summary><b>Windows에 설치</b></summary>

Windows에서의 설정은 Linux나 macOS와 약간 다릅니다 (_예시에서는 `Cline` 사용_). 다른 편집기에도 동일한 원칙이 적용됩니다. `command`와 `args` 설정을 참조하세요.

```json
{
  "mcpServers": {
    "github.com/upstash/context7-mcp": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@upstash/context7-mcp@latest"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

</details>

<details>
<summary><b>Augment Code에 설치</b></summary>

Augment Code에서 Context7 MCP를 설정하려면 그래픽 인터페이스 또는 수동 설정을 사용할 수 있습니다.

### **A. Augment Code UI 사용**

1. 햄버거 메뉴를 클릭합니다.
2. **설정**을 선택합니다.
3. **도구** 섹션으로 이동합니다.
4. **+ MCP 추가** 버튼을 클릭합니다.
5. 다음 명령을 입력합니다:

   ```
   npx -y @upstash/context7-mcp@latest
   ```

6. MCP 이름을 **Context7**으로 지정합니다.
7. **추가** 버튼을 클릭합니다.

MCP 서버가 추가되면 Augment Code 내에서 직접 Context7의 최신 코드 문서 기능을 사용할 수 있습니다.

---

### **B. 수동 설정**

1. Cmd/Ctrl Shift P를 누르거나 Augment 패널의 햄버거 메뉴로 이동합니다.
2. 설정 편집을 선택합니다.
3. 고급 아래에서 settings.json에서 편집을 클릭합니다.
4. `augment.advanced` 객체의 `mcpServers` 배열에 서버 설정을 추가합니다.

"augment.advanced": {
"mcpServers": [
{
"name": "context7",
"command": "npx",
"args": ["-y", "@upstash/context7-mcp"]
}
]
}

MCP 서버가 추가되면 편집기를 다시 시작하세요. 오류가 발생하면 닫는 괄호나 쉼표가 누락되지 않았는지 구문을 확인하세요.

</details>

<details>
<summary><b>Roo Code에 설치</b></summary>

Roo Code MCP 설정 파일에 다음을 추가하세요. 자세한 내용은 [Roo Code MCP 문서](https://docs.roocode.com/features/mcp/using-mcp-in-roo)를 참조하세요.

#### Roo Code 원격 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "type": "streamable-http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

#### Roo Code 로컬 서버 연결

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Zencoder에 설치</b></summary>

Zencoder에서 Context7 MCP를 설정하려면 다음 단계를 따르세요:

1. Zencoder 메뉴(...)로 이동합니다.
2. 드롭다운 메뉴에서 에이전트 도구를 선택합니다.
3. 사용자 지정 MCP 추가를 클릭합니다.
4. 아래에서 이름과 서버 설정을 추가하고 설치 버튼을 누릅니다.

```json
{
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp@latest"]
}
```

MCP 서버가 추가되면 쉽게 계속 사용할 수 있습니다.

</details>

<details>
<summary><b>Amazon Q Developer CLI에 설치</b></summary>

Amazon Q Developer CLI 설정 파일에 다음을 추가하세요. 자세한 내용은 [Amazon Q Developer CLI 문서](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-mcp-configuration.html)를 참조하세요.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

</details>

<details>
<summary><b>Qodo Gen에 설치</b></summary>

자세한 내용은 [Qodo Gen 문서](https://docs.qodo.ai/qodo-documentation/qodo-gen/qodo-gen-chat/agentic-mode/agentic-tools-mcps)를 참조하세요.

1. VSCode 또는 IntelliJ에서 Qodo Gen 채팅 패널을 엽니다.
2. 더 많은 도구 연결을 클릭합니다.
3. - 새 MCP 추가를 클릭합니다.
4. 다음 설정을 추가합니다:

```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

</details>

<details>
<summary><b>JetBrains AI Assistant에 설치</b></summary>

자세한 내용은 [JetBrains AI Assistant 문서](https://www.jetbrains.com/help/ai-assistant/configure-an-mcp-server.html)를 참조하세요.

1. JetBrains IDE에서 `Settings` -> `Tools` -> `AI Assistant` -> `Model Context Protocol (MCP)`로 이동합니다.
2. `+ 추가`를 클릭합니다.
3. 대화 상자 왼쪽 상단의 `Command`를 클릭하고 목록에서 JSON으로 옵션을 선택합니다.
4. 이 설정을 추가하고 `OK`를 클릭합니다.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

5. `Apply`를 클릭하여 변경 사항을 저장합니다.

</details>

<details>
<summary><b>Warp에 설치</b></summary>

자세한 내용은 [Warp 모델 컨텍스트 프로토콜 문서](https://docs.warp.dev/knowledge-and-collaboration/mcp#adding-an-mcp-server)를 참조하세요.

1. `Settings` > `AI` > `Manage MCP servers`로 이동합니다.
2. `+ Add` 버튼을 클릭하여 새 MCP 서버를 추가합니다.
3. 아래 주어진 설정을 붙여넣습니다:

```json
{
  "Context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp"],
    "env": {},
    "working_directory": null,
    "start_on_launch": true
  }
}
```

4. `Save`를 클릭하여 변경 사항을 적용합니다.

</details>

<details>
<summary><b>Opencode에 설치</b></summary>

Opencode 설정 파일에 다음을 추가하세요. 자세한 내용은 [Opencode MCP 문서](https://opencode.ai/docs/mcp-servers)를 참조하세요.

#### Opencode 원격 서버 연결

```json
"mcp": {
  "context7": {
    "type": "remote",
    "url": "https://mcp.context7.com/mcp",
    "enabled": true
  }
}
```

#### Opencode 로컬 서버 연결

```json
{
  "mcp": {
    "context7": {
      "type": "local",
      "command": ["npx", "-y", "@upstash/context7-mcp"],
      "enabled": true
    }
  }
}
```

</details>
<details>

<summary><b>Kiro에 설치</b></summary>

자세한 내용은 [Kiro 모델 컨텍스트 프로토콜 문서](https://kiro.dev/docs/mcp/configuration/)를 참조하세요.

1. `Kiro` > `MCP Servers`로 이동합니다.
2. `+ Add` 버튼을 클릭하여 새 MCP 서버를 추가합니다.
3. 아래에 주어진 설정을 붙여넣습니다:

```json
{
  "mcpServers": {
    "Context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

4. `Save`을 클릭하여 변경 사항을 적용합니다.

</details>
<details>
<summary><b>OpenAI Codex에 설치</b></summary>

자세한 내용은 [OpenAI Codex](https://github.com/openai/codex)를 참조하세요.

OpenAI Codex MCP 서버 설정에 다음 설정을 추가하세요:

```toml
[mcp_servers.context7]
args = ["-y", "@upstash/context7-mcp"]
command = "npx"
```

</details>

## 🔨 사용 가능한 도구

Context7 MCP는 LLM이 사용할 수 있는 다음 도구들을 제공합니다:

- `resolve-library-id`: 일반적인 라이브러리 이름을 Context7이 인식할 수 있는 라이브러리 ID로 변환합니다.

  - `libraryName` (필수): 검색할 라이브러리의 이름

- `get-library-docs`: Context7이 인식하는 라이브러리 ID를 사용하여 해당 라이브러리의 문서를 가져옵니다.
  - `context7CompatibleLibraryID` (필수): 정확한 Context7 호환 라이브러리 ID (예: `/mongodb/docs`, `/vercel/next.js`)
  - `topic` (선택): 특정 주제에 대한 문서에 집중합니다 (예: "routing", "hooks")
  - `tokens` (선택, 기본값 10000): 가져올 문서의 최대 토큰 수. 기본값인 10000보다 작은 값은 자동으로 10000으로 증가합니다.

## 🛟 팁

### 규칙 추가

> 모든 프롬프트에 `use context7`을 추가하고 싶지 않다면, Windsurf의 `.windsurfrules` 파일이나 Cursor의 `Cursor Settings > Rules` 섹션(또는 사용 중인 MCP 클라이언트의 해당 기능)에서 간단한 규칙을 정의하여 코드 관련 질문에 Context7을 자동으로 호출할 수 있습니다:
>
> ```toml
> [[calls]]
> match = "when the user requests code examples, setup or configuration steps, or library/API documentation"
> tool  = "context7"
> ```
>
> 그러면 추가 입력 없이도 관련 대화에서 Context7의 문서를 얻을 수 있습니다. match 부분에 여러분의 사용 사례를 추가할 수 있습니다.

### 라이브러리 ID 사용

> 사용하려는 라이브러리를 이미 정확히 알고 있다면, 프롬프트에 해당 라이브러리의 Context7 ID를 추가하세요. 이렇게 하면 Context7 MCP 서버가 라이브러리 매칭 단계를 건너뛰고 바로 문서 검색을 진행할 수 있습니다.
>
> ```txt
> supabase로 기본 인증을 구현해줘. API와 문서는 /supabase/supabase 라이브러리를 사용해줘
> ```
>
> 슬래시 구문은 MCP 도구에게 어떤 라이브러리의 문서를 로드할지 정확히 알려줍니다.

## 💻 개발

프로젝트를 복제하고 의존성을 설치하세요:

```bash
bun i
```

빌드:

```bash
bun run build
```

서버 실행:

```bash
bun run dist/index.js
```

### CLI 인수

`context7-mcp`는 다음 CLI 플래그를 지원합니다:

- `--transport <stdio|http|sse>` – 사용할 전송 방식 (`stdio`가 기본값).
- `--port <number>` – `http` 또는 `sse` 전송 방식 사용 시 수신 대기할 포트 (기본값 `3000`).

http 전송과 포트 8080을 사용하는 예시:

```bash
bun run dist/index.js --transport http --port 8080
```

<details>
<summary><b>로컬 설정 예시</b></summary>

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["tsx", "/path/to/folder/context7-mcp/src/index.ts"]
    }
  }
}
```

</details>

<details>
<summary><b>MCP Inspector로 테스트</b></summary>

```bash
npx -y @modelcontextprotocol/inspector npx @upstash/context7-mcp
```

</details>

## 🚨 문제 해결

<details>
<summary><b>Module Not Found Errors</b></summary>

`ERR_MODULE_NOT_FOUND` 오류가 발생하면 `npx` 대신 `bunx`를 사용해 보세요:

```json
{
  "mcpServers": {
    "context7": {
      "command": "bunx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

이 방법은 `npx`가 패키지를 제대로 설치하거나 확인하지 못하는 환경에서 모듈 확인 문제를 해결하는 경우가 많습니다.

</details>

<details>
<summary><b>ESM Resolution 문제</b></summary>

`Error: Cannot find module 'uriTemplate.js'`와 같은 오류의 경우 `--experimental-vm-modules` 플래그를 사용해 보세요:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "--node-options=--experimental-vm-modules", "@upstash/context7-mcp@1.0.6"]
    }
  }
}
```

</details>

<details>
<summary><b>TLS/인증서 문제</b></summary>

`--experimental-fetch` 플래그를 사용하여 TLS 관련 문제를 우회하세요:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "--node-options=--experimental-fetch", "@upstash/context7-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>일반적인 MCP 클라이언트 오류</b></summary>

1. 패키지 이름에 `@latest`를 추가해 보세요.
2. `npx` 대신 `bunx`를 사용해 보세요.
3. 또 다른 대안으로 `deno` 사용을 고려해 보세요.
4. 네이티브 fetch 지원을 위해 Node.js v18 이상을 사용하고 있는지 확인하세요.

</details>

## ⚠️ 면책 조항

Context7 프로젝트는 커뮤니티 기여로 이루어지며, 높은 품질을 유지하기 위해 노력하지만 모든 라이브러리 문서의 정확성, 완전성 또는 보안을 보장할 수는 없습니다. Context7에 등록된 프로젝트는 Context7이 아닌 각 소유자에 의해 개발되고 유지 관리됩니다. 의심스럽거나, 부적절하거나, 잠재적으로 유해한 콘텐츠를 발견하면 프로젝트 페이지의 "신고" 버튼을 사용하여 즉시 저희에게 알려주십시오. 저희는 모든 신고를 심각하게 받아들이고 플랫폼의 무결성과 안전을 유지하기 위해 신고된 콘텐츠를 신속하게 검토할 것입니다. Context7을 사용함으로써 귀하는 자신의 재량과 책임 하에 사용함을 인정하는 것입니다.

## 🤝 소통하기

최신 정보를 받고 커뮤니티에 참여하세요:

- 📢 [X](https://x.com/contextai)에서 저희를 팔로우하고 최신 소식과 업데이트를 받아보세요.
- 🌐 저희 [웹사이트](https://context7.com)를 방문하세요.
- 💬 저희 [디스코드 커뮤니티](https://upstash.com/discord)에 참여하세요.

## 📺 미디어 속 Context7

- [Better Stack: "Free Tool Makes Cursor 10x Smarter"](https://youtu.be/52FC3qObp9E)
- [Cole Medin: "This is Hands Down the BEST MCP Server for AI Coding Assistants"](https://www.youtube.com/watch?v=G7gK8H6u7Rs)
- [Income Stream Surfers: "Context7 + SequentialThinking MCPs: Is This AGI?"](https://www.youtube.com/watch?v=-ggvzyLpK6o)
- [Julian Goldie SEO: "Context7: New MCP AI Agent Update"](https://www.youtube.com/watch?v=CTZm6fBYisc)
- [JeredBlu: "Context 7 MCP: Get Documentation Instantly + VS Code Setup"](https://www.youtube.com/watch?v=-ls0D-rtET4)
- [Income Stream Surfers: "Context7: The New MCP Server That Will CHANGE AI Coding"](https://www.youtube.com/watch?v=PS-2Azb-C3M)
- [AICodeKing: "Context7 + Cline & RooCode: This MCP Server Makes CLINE 100X MORE EFFECTIVE!"](https://www.youtube.com/watch?v=qZfENAPMnyo)
- [Sean Kochel: "5 MCP Servers For Vibe Coding Glory (Just Plug-In & Go)"](https://www.youtube.com/watch?v=LqTQi8qexJM)

## ⭐ Star History

[![Star 기록 차트](https://api.star-history.com/svg?repos=upstash/context7&type=Date)](https://www.star-history.com/#upstash/context7&Date)

## 라이선스

MIT
