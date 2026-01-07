/**
 * Code Execution Server
 *
 * HTTP server for the code execution layer.
 * Compatible with both Deno and Node.js runtimes.
 */

import { Executor, getExecutor } from './executor.ts';
import { getRegistry } from './providers/index.ts';

// Environment configuration
const PYTHON_BACKEND_URL = (
  typeof Deno !== 'undefined'
    ? Deno.env.get('PYTHON_BACKEND_URL')
    : process.env.PYTHON_BACKEND_URL
) || 'http://localhost:8000';

const PORT = parseInt(
  (typeof Deno !== 'undefined' ? Deno.env.get('DENO_PORT') : process.env.DENO_PORT) || '8001'
);

// Initialize executor
const executor = new Executor(PYTHON_BACKEND_URL);
const registry = getRegistry();

/**
 * Request body types
 */
interface ExecuteRequest {
  code: string;
  timeout_ms?: number;
  variables?: Record<string, unknown>;
  auth_token?: string;
}

interface ValidateRequest {
  code: string;
}

/**
 * Parse JSON body from request
 */
async function parseJsonBody<T>(request: Request): Promise<T> {
  const text = await request.text();
  return JSON.parse(text) as T;
}

/**
 * Create JSON response
 */
function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

/**
 * Handle CORS preflight
 */
function handleCors(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

/**
 * Request handler
 */
async function handleRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname;

  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return handleCors();
  }

  try {
    // Health check
    if (request.method === 'GET' && path === '/health') {
      return jsonResponse({
        status: 'ok',
        providers: registry.listProviders(),
        tool_count: registry.getToolCount(),
        python_backend: PYTHON_BACKEND_URL,
      });
    }

    // List tools
    if (request.method === 'GET' && path === '/tools') {
      const tools = await executor.listAllTools();
      return jsonResponse({ tools });
    }

    // Execute code
    if (request.method === 'POST' && path === '/execute') {
      const body = await parseJsonBody<ExecuteRequest>(request);

      if (!body.code) {
        return jsonResponse({ error: 'Missing required field: code' }, 400);
      }

      const result = await executor.execute(body.code, {
        timeout: body.timeout_ms || 60000,
        variables: body.variables || {},
        authToken: body.auth_token,
      });

      return jsonResponse(result);
    }

    // Validate code
    if (request.method === 'POST' && path === '/validate') {
      const body = await parseJsonBody<ValidateRequest>(request);

      if (!body.code) {
        return jsonResponse({ error: 'Missing required field: code' }, 400);
      }

      const result = executor.validate(body.code);
      return jsonResponse(result);
    }

    // Not found
    return jsonResponse({ error: 'Not found' }, 404);
  } catch (error) {
    console.error('Request error:', error);
    return jsonResponse(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      500
    );
  }
}

/**
 * Start server based on runtime
 */
async function startServer(): Promise<void> {
  // Check if running in Deno
  if (typeof Deno !== 'undefined') {
    console.log(`Starting Deno server on port ${PORT}`);
    console.log(`Python backend: ${PYTHON_BACKEND_URL}`);

    // @ts-ignore - Deno.serve is available in Deno runtime
    Deno.serve({ port: PORT }, handleRequest);
  } else {
    // Node.js runtime
    const http = await import('http');

    const server = http.createServer(async (req, res) => {
      // Convert Node.js request to fetch Request
      const url = `http://localhost:${PORT}${req.url}`;
      const headers = new Headers();
      for (const [key, value] of Object.entries(req.headers)) {
        if (value) {
          headers.set(key, Array.isArray(value) ? value[0] : value);
        }
      }

      let body: string | undefined;
      if (req.method === 'POST') {
        body = await new Promise<string>((resolve) => {
          let data = '';
          req.on('data', (chunk) => (data += chunk));
          req.on('end', () => resolve(data));
        });
      }

      const request = new Request(url, {
        method: req.method,
        headers,
        body,
      });

      const response = await handleRequest(request);

      res.statusCode = response.status;
      response.headers.forEach((value, key) => {
        res.setHeader(key, value);
      });
      res.end(await response.text());
    });

    server.listen(PORT, () => {
      console.log(`Starting Node.js server on port ${PORT}`);
      console.log(`Python backend: ${PYTHON_BACKEND_URL}`);
    });
  }
}

// Start the server
startServer().catch(console.error);
