import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/", { headers: { accept: "text/html" } }), { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } }, { waitUntil() {}, passThroughOnException() {} });
}

test("server renders the finished project shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Financial Advisor Bot/);
  assert.match(html, /Transparent Simulation Lab/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/);
});

test("ships the generated evaluation evidence", async () => {
  const data = JSON.parse(await readFile(new URL("public/evaluation.json", root), "utf8"));
  assert.equal(data.metadata.seed, 42);
  assert.equal(data.strategies.length, 3);
  assert.ok(data.strategies.every((strategy) => strategy.records.length > 0));
});
