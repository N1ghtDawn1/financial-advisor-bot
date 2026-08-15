import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("dashboard source contains the finished project shell", async () => {
  const source = await readFile(new URL("app/page.tsx", root), "utf8");
  assert.match(source, /Financial Advisor Bot/);
  assert.match(source, /Transparent simulation lab/);
  assert.match(source, /Simulation only/);
  assert.doesNotMatch(source, /Your site is taking shape/);
});

test("ships the generated evaluation evidence", async () => {
  const data = JSON.parse(await readFile(new URL("public/evaluation.json", root), "utf8"));
  assert.equal(data.metadata.seed, 42);
  assert.equal(data.strategies.length, 3);
  assert.ok(data.strategies.every((strategy) => strategy.records.length > 0));
});
