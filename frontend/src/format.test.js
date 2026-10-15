import { test } from 'node:test';
import assert from 'node:assert/strict';
import { suggestedReorder, timeAgo } from './format.js';

test('suggested reorder refills to twice the reorder level', () => {
  assert.equal(suggestedReorder({ quantity: 3, reorder_level: 10 }), 17);
  assert.equal(suggestedReorder({ quantity: 0, reorder_level: 4 }), 8);
  assert.equal(suggestedReorder({ quantity: 50, reorder_level: 10 }), 1);
});

test('timeAgo treats timestamps without an offset as UTC', () => {
  const now = Date.parse('2026-01-01T10:00:00Z');
  assert.equal(timeAgo('2026-01-01T09:58:00', now), '2 min ago');
  assert.equal(timeAgo('2026-01-01T09:59:50+00:00', now), 'just now');
  assert.equal(timeAgo('2025-12-30T10:00:00Z', now), '2 d ago');
});
