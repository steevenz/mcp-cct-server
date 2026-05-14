#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const readline = require("readline");
const crypto = require("crypto");
const os = require("os");

const PRD_ID = "20260509-multi-ide-single-server";
const WRAPPER_NAME = "cct-mcp";
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const VENV_DIR = fs.existsSync(path.join(PROJECT_ROOT, ".venv"))
  ? path.join(PROJECT_ROOT, ".venv")
  : path.join(PROJECT_ROOT, "venv");
const IS_WINDOWS = process.platform === "win32";
const VENV_PYTHON = IS_WINDOWS
  ? path.join(VENV_DIR, "Scripts", "python.exe")
  : path.join(VENV_DIR, "bin", "python");

const SERVER_STATE_DIR = path.join(PROJECT_ROOT, "database", "config");
const SERVER_STATE_PATH = path.join(SERVER_STATE_DIR, "cct_shared_server.json");
const SERVER_LOCK_PATH = path.join(SERVER_STATE_DIR, "cct_shared_server.lock");
const SERVER_REGISTRY_PATH = path.join(SERVER_STATE_DIR, "mcp_server_registry.json");

let serverProcess = null;
let shuttingDown = false;
let sharedServerBaseUrl = null;
let apiKeyHeader = null;
let authConfig = null;

// ============================================================================
// CLI ARGS
// ============================================================================
function parseCliArgs() {
  const args = process.argv.slice(2);
  const opts = {
    ide: process.env.CCT_IDE || "unknown",
    transport: process.env.CCT_TRANSPORT || "stdio",
    port: parseInt(process.env.CCT_PORT, 10) || 8001,
    host: process.env.CCT_HOST || "127.0.0.1",
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--ide": opts.ide = args[++i] || opts.ide; break;
      case "--transport": opts.transport = args[++i] || opts.transport; break;
      case "--port": opts.port = parseInt(args[++i], 10) || opts.port; break;
      case "--host": opts.host = args[++i] || opts.host; break;
    }
  }
  return opts;
}

const CLI_OPTS = parseCliArgs();

// ============================================================================
// CONNECTION REGISTRY — tracks which IDEs connected (lightweight, no process mgmt)
// ============================================================================
function readRegistry() {
  try { return JSON.parse(fs.readFileSync(SERVER_REGISTRY_PATH, "utf-8")); }
  catch { return { prd_id: PRD_ID, connections: [] }; }
}

function writeRegistry(data) {
  fs.mkdirSync(SERVER_STATE_DIR, { recursive: true });
  fs.writeFileSync(SERVER_REGISTRY_PATH, JSON.stringify(data, null, 2), "utf-8");
}

function registerConnection() {
  const reg = readRegistry();
  reg.connections = reg.connections.filter(c => c.ide !== CLI_OPTS.ide);
  reg.connections.push({
    ide: CLI_OPTS.ide,
    transport: CLI_OPTS.transport,
    port: CLI_OPTS.port,
    pid: process.pid,
    connectedAt: new Date().toISOString(),
  });
  reg.total = reg.connections.length;
  writeRegistry(reg);
}

function unregisterConnection() {
  const reg = readRegistry();
  reg.connections = reg.connections.filter(c => !(c.ide === CLI_OPTS.ide && c.pid === process.pid));
  reg.total = reg.connections.length;
  writeRegistry(reg);
}

// ============================================================================
// HELPERS
// ============================================================================
function logStderr(message) { process.stderr.write(`${message}\n`); }

function runSyncCommand(command, args, label) {
  logStderr(`[${WRAPPER_NAME}][${PRD_ID}] ${label}: ${command} ${args.join(" ")}`);
  const result = spawnSync(command, args, { cwd: PROJECT_ROOT, env: process.env, stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" });
  if (result.stdout) process.stderr.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.error) throw result.error;
  if (typeof result.status === "number" && result.status !== 0) throw new Error(`${label} failed with exit code ${result.status}`);
}

function resolveBootstrapPython() {
  const candidates = [];
  if (process.env.PYTHON && process.env.PYTHON.trim()) candidates.push([process.env.PYTHON.trim(), []]);
  if (IS_WINDOWS) { candidates.push(["python", []]); candidates.push(["py", ["-3"]]); }
  else { candidates.push(["python3", []]); candidates.push(["python", []]); }
  for (const [cmd, prefix] of candidates) {
    const probe = spawnSync(cmd, [...prefix, "--version"], { cwd: PROJECT_ROOT, env: process.env, stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" });
    if (!probe.error && probe.status === 0) return { cmd, prefix };
  }
  throw new Error("No system Python interpreter found for initial bootstrap.");
}

function ensureVirtualEnvironment() {
  if (fs.existsSync(VENV_DIR)) return;
  const bp = resolveBootstrapPython();
  runSyncCommand(bp.cmd, [...bp.prefix, "-m", "venv", "venv"], "create-venv");
  runSyncCommand(VENV_PYTHON, ["-m", "pip", "install", "-r", "requirements.txt"], "install-requirements");
}

function readDotenvValue(key) {
  const envPath = path.join(PROJECT_ROOT, ".env");
  if (!fs.existsSync(envPath)) return null;
  const content = fs.readFileSync(envPath, "utf-8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const normalized = line.startsWith("export ") ? line.slice("export ".length).trim() : line;
    const eq = normalized.indexOf("=");
    if (eq <= 0) continue;
    if (normalized.slice(0, eq).trim() !== key) continue;
    return normalized.slice(eq + 1).trim().replace(/^"(.*)"$/, "$1").replace(/^'(.*)'$/, "$1") || null;
  }
  return null;
}

function loadAuthConfig() {
  const envClientKey = (process.env.CCT_CLIENT_API_KEY || "").trim();
  const dotenvClientKey = (readDotenvValue("CCT_CLIENT_API_KEY") || "").trim();
  const envBootstrapKey = (process.env.CCT_BOOTSTRAP_API_KEY || "").trim();
  const dotenvBootstrapKey = (readDotenvValue("CCT_BOOTSTRAP_API_KEY") || "").trim();
  const envLegacyKey = (process.env.CCT_DASHBOARD_API_KEY || "").trim();
  const dotenvLegacyKey = (readDotenvValue("CCT_DASHBOARD_API_KEY") || "").trim();
  const expiresAt = (process.env.CCT_CLIENT_KEY_EXPIRES_AT || readDotenvValue("CCT_CLIENT_KEY_EXPIRES_AT") || "").trim();
  const instanceId = (
    process.env.CCT_CLIENT_INSTANCE_ID
    || readDotenvValue("CCT_CLIENT_INSTANCE_ID")
    || `cct-${CLI_OPTS.ide}-${os.hostname()}-${process.pid}`
  ).trim();
  const bootstrapKey = envBootstrapKey || dotenvBootstrapKey || envLegacyKey || dotenvLegacyKey;
  if (!bootstrapKey && !(envClientKey || dotenvClientKey)) throw new Error("CCT_BOOTSTRAP_API_KEY (or CCT_CLIENT_API_KEY) is required in environment/.env.");
  if (!envBootstrapKey && !dotenvBootstrapKey && (envLegacyKey || dotenvLegacyKey))
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] DEPRECATED_ENV_VAR: CCT_DASHBOARD_API_KEY is deprecated. Use CCT_BOOTSTRAP_API_KEY.`);
  return { clientKey: envClientKey || dotenvClientKey || "", bootstrapKey: bootstrapKey || "", clientKeyExpiresAt: expiresAt || "", clientInstanceId: instanceId, ide: CLI_OPTS.ide };
}

function isNearExpiry(isoTimestamp, windowMs = 86400000) {
  if (!isoTimestamp) return false;
  const expiresMs = Date.parse(isoTimestamp);
  return Number.isNaN(expiresMs) ? false : expiresMs - Date.now() <= windowMs;
}

function persistClientKey(apiKey, expiresAt, instanceId) {
  if (!apiKey) return;
  try {
    upsertDotenvValues({
      CCT_CLIENT_API_KEY: apiKey,
      CCT_CLIENT_KEY_EXPIRES_AT: expiresAt || "",
      CCT_CLIENT_INSTANCE_ID: instanceId || ""
    });
    process.env.CCT_CLIENT_API_KEY = apiKey;
    if (expiresAt) process.env.CCT_CLIENT_KEY_EXPIRES_AT = expiresAt;
    if (instanceId) process.env.CCT_CLIENT_INSTANCE_ID = instanceId;
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Persisted issued client key (Expires: ${expiresAt || "N/A"})`);
  } catch (err) {
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] WARNING: Failed to persist client key to .env: ${err.message}`);
  }
}

function upsertDotenvValues(updates) {
  const envPath = path.join(PROJECT_ROOT, ".env");
  const tmpPath = `${envPath}.tmp`;
  const existing = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf-8") : "";
  const lines = existing ? existing.split(/\r?\n/) : [];
  const remaining = new Map(Object.entries(updates).filter(([_, v]) => typeof v === "string" && v.length > 0));
  const updatedLines = lines.map((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) return line;
    const normalized = trimmed.startsWith("export ") ? trimmed.slice("export ".length).trim() : trimmed;
    const eq = normalized.indexOf("=");
    if (eq <= 0) return line;
    const name = normalized.slice(0, eq).trim();
    if (!remaining.has(name)) return line;
    const value = remaining.get(name);
    remaining.delete(name);
    return `${name}=${value}`;
  });
  for (const [name, value] of remaining.entries()) updatedLines.push(`${name}=${value}`);
  // Atomic-like write via rename
  fs.writeFileSync(tmpPath, updatedLines.join("\n").replace(/\n*$/, "\n"), "utf-8");
  fs.renameSync(tmpPath, envPath);
}

function buildApiKeyHeader(apiKey) { return { "X-API-KEY": apiKey }; }

async function fetchJson(url, options, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs).unref();
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const contentType = response.headers.get("content-type") || "";
    const text = await response.text();
    const json = contentType.includes("application/json") ? JSON.parse(text) : null;
    return { ok: response.ok, status: response.status, json, text };
  } catch (error) {
    if (error && error.name === "AbortError") throw new Error(`Request timeout after ${timeoutMs}ms`);
    throw error;
  } finally { clearTimeout(timer); }
}

async function validateApiKeyForSync(baseUrl, apiKey) {
  if (!apiKey) return false;
  try {
    const probe = await fetchJson(`${baseUrl}/cognitive-api/v1/sync`, {
      method: "POST", headers: { ...buildApiKeyHeader(apiKey), "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" }),
    }, 5000);
    return probe.ok && probe.json && typeof probe.json === "object" && probe.json.jsonrpc === "2.0" && Object.prototype.hasOwnProperty.call(probe.json, "result");
  } catch { return false; }
}

async function issueClientKeyViaHandshake(baseUrl) {
  if (!authConfig || !authConfig.bootstrapKey) throw new Error("Bootstrap key is required for handshake");
  const bootstrapHeader = { "X-BOOTSTRAP-KEY": authConfig.bootstrapKey, "content-type": "application/json" };
  const clientNonce = crypto.randomBytes(16).toString("hex");
  const initResp = await fetchJson(`${baseUrl}/cognitive-api/v1/auth/handshake/init`, {
    method: "POST", headers: bootstrapHeader,
    body: JSON.stringify({ llm_instance_id: authConfig.clientInstanceId, client_nonce: clientNonce }),
  }, 8000);
  const initData = initResp?.json?.data || {};
  const handshakeId = String(initData.handshake_id || "").trim();
  const challenge = String(initData.challenge || "").trim();
  if (!initResp.ok || !handshakeId || !challenge) throw new Error("Handshake init failed");
  const clientProof = crypto.createHmac("sha256", authConfig.bootstrapKey)
    .update(`${handshakeId}:${authConfig.clientInstanceId}:${challenge}`, "utf-8").digest("hex");
  const completeResp = await fetchJson(`${baseUrl}/cognitive-api/v1/auth/handshake/complete`, {
    method: "POST", headers: bootstrapHeader,
    body: JSON.stringify({ handshake_id: handshakeId, client_proof: clientProof }),
  }, 8000);
  const issued = completeResp?.json?.data || {};
  const apiKey = String(issued.api_key || "").trim();
  const expiresAt = String(issued.expires_at || "").trim();
  if (!completeResp.ok || !apiKey) throw new Error("Handshake complete failed");
  authConfig.clientKey = apiKey;
  authConfig.clientKeyExpiresAt = expiresAt;
  persistClientKey(apiKey, expiresAt, authConfig.clientInstanceId);
  return apiKey;
}

async function rotateClientKey(baseUrl, currentApiKey) {
  if (!currentApiKey) return null;
  try {
    const resp = await fetchJson(`${baseUrl}/cognitive-api/v1/auth/keys/rotate`, {
      method: "POST",
      headers: { ...buildApiKeyHeader(currentApiKey), "content-type": "application/json" },
      body: JSON.stringify({}),
    }, 8000);
    const rotated = resp?.json?.data || {};
    const apiKey = String(rotated.api_key || "").trim();
    const expiresAt = String(rotated.expires_at || "").trim();
    if (!resp.ok || !apiKey) {
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Key rotation failed: ${resp.status} ${resp.text}`);
      return null;
    }
    authConfig.clientKey = apiKey;
    authConfig.clientKeyExpiresAt = expiresAt;
    persistClientKey(apiKey, expiresAt, authConfig.clientInstanceId);
    return apiKey;
  } catch (err) {
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Key rotation error: ${err.message}`);
    return null;
  }
}

let rotationTimer = null;
function scheduleAutomaticRotation(baseUrl) {
  if (rotationTimer) clearInterval(rotationTimer);
  // Check every 30 minutes
  rotationTimer = setInterval(async () => {
    if (isNearExpiry(authConfig.clientKeyExpiresAt, 12 * 3600000)) { // Rotate 12h before expiry
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Triggering proactive key rotation...`);
      await rotateClientKey(baseUrl, authConfig.clientKey);
    }
  }, 1800000).unref();
}

async function establishClientAuth(baseUrl, forceRefresh = false) {
  const currentKey = authConfig?.clientKey || "";
  if (!forceRefresh && currentKey) {
    if (await validateApiKeyForSync(baseUrl, currentKey)) {
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Existing client key is valid.`);
      if (isNearExpiry(authConfig.clientKeyExpiresAt)) {
        logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Client key near expiry, rotating...`);
        apiKeyHeader = buildApiKeyHeader((await rotateClientKey(baseUrl, currentKey)) || currentKey);
      } else {
        apiKeyHeader = buildApiKeyHeader(currentKey);
      }
      scheduleAutomaticRotation(baseUrl);
      return;
    }
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Existing client key is invalid or expired.`);
  }

  if (authConfig?.bootstrapKey) {
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Initiating handshake via bootstrap key...`);
    const newKey = await issueClientKeyViaHandshake(baseUrl);
    apiKeyHeader = buildApiKeyHeader(newKey);
    scheduleAutomaticRotation(baseUrl);
    return;
  }

  if (currentKey) throw new Error("CCT_CLIENT_API_KEY is invalid and no bootstrap key is available for refresh.");
  throw new Error("No usable auth key found.");
}

function tryAcquireLock(timeoutMs = 8000) {
  fs.mkdirSync(SERVER_STATE_DIR, { recursive: true });
  const start = Date.now();
  while (true) {
    try { return fs.openSync(SERVER_LOCK_PATH, "wx"); } catch {
      if (Date.now() - start > timeoutMs) throw new Error("Failed to acquire shared server lock.");
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 50);
    }
  }
}

function releaseLock(fd) {
  try { fs.closeSync(fd); } catch {}
  try { fs.unlinkSync(SERVER_LOCK_PATH); } catch {}
}

function readServerState() {
  try { return JSON.parse(fs.readFileSync(SERVER_STATE_PATH, "utf-8")); } catch { return null; }
}

function writeServerState(state) {
  fs.mkdirSync(SERVER_STATE_DIR, { recursive: true });
  fs.writeFileSync(SERVER_STATE_PATH, JSON.stringify(state, null, 2), "utf-8");
}

async function probeStatusSignature(baseUrl) {
  try {
    const probe = await fetchJson(`${baseUrl}/status`, { method: "GET" }, 1200);
    return probe.ok && probe.json && Boolean(probe.json.server && probe.json.transport);
  } catch { return false; }
}

async function detectActiveServerBaseUrl() {
  const ports = [8000, 8001, 8002, 8080, 3000, 5000, 3001, 5001];
  for (const host of ["http://localhost", "http://127.0.0.1"]) {
    for (const port of ports) {
      try { if (await probeStatusSignature(`${host}:${port}`)) return `${host}:${port}`; } catch { continue; }
    }
  }
  return null;
}

async function ensureSharedServer() {
  const lockFd = tryAcquireLock();
  try {
    const preferredPortRaw = process.env.CCT_PORT || readDotenvValue("CCT_PORT") || "8001";
    const preferredPort = /^\d+$/.test(preferredPortRaw) ? Number(preferredPortRaw) : 8001;
    const preferredBaseUrl = `http://127.0.0.1:${preferredPort}`;

    // 1. Try existing server at preferred port (with auth)
    if (await probeStatusSignature(preferredBaseUrl)) {
      await establishClientAuth(preferredBaseUrl, false);
      sharedServerBaseUrl = preferredBaseUrl;
      registerConnection();
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Connected to existing server at ${preferredBaseUrl}`);
      return;
    }

    // 2. Try any discovered server
    const discovered = await detectActiveServerBaseUrl();
    if (discovered) {
      await establishClientAuth(discovered, false);
      sharedServerBaseUrl = discovered;
      registerConnection();
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Connected to discovered server at ${discovered}`);
      return;
    }

    // 3. Spawn new server
    const childEnv = { ...process.env, CCT_TRANSPORT: "sse", CCT_HOST: "127.0.0.1", CCT_PORT: String(preferredPort), PYTHONPATH: PROJECT_ROOT };
    serverProcess = spawn(VENV_PYTHON, ["-u", "src/main.py"], { cwd: PROJECT_ROOT, env: childEnv, stdio: ["ignore", "pipe", "pipe"], detached: false });
    serverProcess.stdout.on("data", (chunk) => process.stderr.write(chunk));
    serverProcess.stderr.on("data", (chunk) => process.stderr.write(chunk));

    writeServerState({ prd_id: PRD_ID, pid: serverProcess.pid, baseUrl: preferredBaseUrl, startedAt: new Date().toISOString(), refCount: 1 });

    for (let i = 0; i < 60; i++) {
      if (serverProcess.exitCode !== null) break;
      if (await probeStatusSignature(preferredBaseUrl)) {
        await establishClientAuth(preferredBaseUrl, false);
        sharedServerBaseUrl = preferredBaseUrl;
        registerConnection();
        logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Started new server at ${preferredBaseUrl}`);
        return;
      }
      await new Promise((r) => setTimeout(r, 250));
    }
    throw new Error("Server failed to become ready within 15s");
  } finally { releaseLock(lockFd); }
}

async function forwardJsonRpcToServer(message) {
  if (!sharedServerBaseUrl || !apiKeyHeader) throw new Error("Server not available.");
  const url = `${sharedServerBaseUrl}/cognitive-api/v1/sync`;
  const method = String(message?.method || "").trim();
  const timeoutMs = method === "tools/call" ? 120000 : 15000;
  const headers = { ...apiKeyHeader, "content-type": "application/json" };

  // Attach IDE context for server-side routing
  if (CLI_OPTS.ide) headers["X-IDE-ORIGIN"] = CLI_OPTS.ide;

  let response = await fetchJson(url, { method: "POST", headers, body: JSON.stringify(message) }, timeoutMs);

  if ((response.status === 401 || response.status === 403) && authConfig?.bootstrapKey) {
    await establishClientAuth(sharedServerBaseUrl, true);
    response = await fetchJson(url, { method: "POST", headers: { ...apiKeyHeader, "content-type": "application/json" }, body: JSON.stringify(message) }, timeoutMs);
  }
  return response;
}

function writeJsonRpcResponse(payload) { process.stdout.write(`${JSON.stringify(payload)}\n`); }

async function terminateWrapper(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  unregisterConnection();
  if (serverProcess && serverProcess.exitCode === null) {
    try { serverProcess.kill("SIGTERM"); } catch {}
  }
  process.exit(exitCode);
}

function registerStdioProxy() {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  rl.on("line", async (line) => {
    const trimmed = String(line || "").trim();
    if (!trimmed) return;
    let message;
    try { message = JSON.parse(trimmed); } catch (error) {
      logStderr(`[${WRAPPER_NAME}][${PRD_ID}] invalid JSON on stdin: ${String(error)}`);
      return;
    }
    const rpcId = Object.prototype.hasOwnProperty.call(message, "id") ? message.id : undefined;
    const isNotification = rpcId === undefined || rpcId === null;
    try {
      const forwarded = await forwardJsonRpcToServer(message);
      if (isNotification) return;
      if (forwarded.json) { writeJsonRpcResponse(forwarded.json); return; }
      writeJsonRpcResponse({ jsonrpc: "2.0", id: rpcId, error: { code: -32000, message: "Upstream returned non-JSON response" } });
    } catch (error) {
      if (isNotification) return;
      writeJsonRpcResponse({ jsonrpc: "2.0", id: rpcId, error: { code: -32000, message: String(error?.message || error) } });
    }
  });
  rl.on("close", () => terminateWrapper(0));
}

function registerShutdownHooks() {
  process.on("SIGINT", () => terminateWrapper(0));
  process.on("SIGTERM", () => terminateWrapper(0));
  process.on("uncaughtException", (error) => { logStderr(`[${WRAPPER_NAME}][${PRD_ID}] uncaught exception: ${String(error?.stack || error)}`); terminateWrapper(1); });
  process.on("unhandledRejection", (reason) => { logStderr(`[${WRAPPER_NAME}][${PRD_ID}] unhandled rejection: ${String(reason)}`); terminateWrapper(1); });
}

function main() {
  try {
    registerShutdownHooks();
    ensureVirtualEnvironment();
    authConfig = loadAuthConfig();

    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] Starting IDE=${CLI_OPTS.ide} transport=${CLI_OPTS.transport} port=${CLI_OPTS.port}`);

    Promise.resolve()
      .then(async () => {
        await ensureSharedServer();
        registerStdioProxy();
      })
      .catch((error) => { logStderr(`[${WRAPPER_NAME}][${PRD_ID}] startup failed: ${String(error?.stack || error)}`); process.exit(1); });
  } catch (error) {
    logStderr(`[${WRAPPER_NAME}][${PRD_ID}] startup failed: ${String(error?.stack || error)}`);
    process.exit(1);
  }
}

main();
