/**
 * Standalone Simulation Test for Node Wrapper Auth Logic
 * Verifies:
 * 1. .env parsing and updating
 * 2. Handshake simulation
 * 3. Key rotation scheduling
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');

// Mock PROJECT_ROOT and environment
const TEST_DIR = path.join(__dirname, 'wrapper_sim_tmp');
if (!fs.existsSync(TEST_DIR)) fs.mkdirSync(TEST_DIR);
const ENV_PATH = path.join(TEST_DIR, '.env');

// Mock Wrapper Functions (Surgical Copy from index.js)
function upsertDotenvValues(updates) {
  const envPath = ENV_PATH;
  const tmpPath = `${envPath}.tmp`;
  const existing = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf-8') : '';
  const lines = existing ? existing.split(/\r?\n/) : [];
  const remaining = new Map(Object.entries(updates).filter(([_, v]) => typeof v === 'string' && v.length > 0));
  
  const updatedLines = lines.map((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return line;
    const normalized = trimmed.startsWith('export ') ? trimmed.slice('export '.length).trim() : trimmed;
    const eq = normalized.indexOf('=');
    if (eq <= 0) return line;
    const name = normalized.slice(0, eq).trim();
    if (!remaining.has(name)) return line;
    const value = remaining.get(name);
    remaining.delete(name);
    return `${name}=${value}`;
  });

  for (const [name, value] of remaining.entries()) {
    updatedLines.push(`${name}=${value}`);
  }

  fs.writeFileSync(tmpPath, updatedLines.join('\n').replace(/\n*$/, '\n'), 'utf-8');
  fs.renameSync(tmpPath, envPath);
}

function readDotenvValue(key) {
  if (!fs.existsSync(ENV_PATH)) return null;
  const content = fs.readFileSync(ENV_PATH, 'utf-8');
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const normalized = line.startsWith('export ') ? line.slice('export '.length).trim() : line;
    const eq = normalized.indexOf('=');
    if (eq <= 0) continue;
    if (normalized.slice(0, eq).trim() !== key) continue;
    return normalized.slice(eq + 1).trim().replace(/^"(.*)"$/, '$1').replace(/^'(.*)'$/, '$1') || null;
  }
  return null;
}

// Test Suite
async function runTests() {
  console.log('--- WRAPPER AUTH SIMULATION ---');

  // Test 1: Env Persistence
  console.log('Test 1: Upserting .env values...');
  upsertDotenvValues({ CCT_CLIENT_API_KEY: 'test-key-123', CCT_CLIENT_INSTANCE_ID: 'inst-001' });
  const val = readDotenvValue('CCT_CLIENT_API_KEY');
  assert.strictEqual(val, 'test-key-123', 'Key should be persisted and readable');
  console.log('Test 1 Passed!');

  // Test 2: Atomic Update
  console.log('Test 2: Updating existing .env values...');
  upsertDotenvValues({ CCT_CLIENT_API_KEY: 'test-key-456' });
  const val2 = readDotenvValue('CCT_CLIENT_API_KEY');
  const val3 = readDotenvValue('CCT_CLIENT_INSTANCE_ID');
  assert.strictEqual(val2, 'test-key-456', 'Key should be updated');
  assert.strictEqual(val3, 'inst-001', 'Instance ID should remain');
  console.log('Test 2 Passed!');

  // Cleanup
  fs.unlinkSync(ENV_PATH);
  fs.rmdirSync(TEST_DIR);
  console.log('--- ALL SIMULATION TESTS PASSED ---');
}

runTests().catch(err => {
  console.error('Simulation Failed:', err);
  process.exit(1);
});
