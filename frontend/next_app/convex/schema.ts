import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  chatSessions: defineTable({
    sessionId: v.string(),
    name: v.string(),
    createdAt: v.string(),
    lastMessageAt: v.string(),
    messageCount: v.number(),
    workspacePath: v.string(),
    configJson: v.optional(v.string()),
    pendingInputJson: v.optional(v.string()),
    agentMessagesJson: v.optional(v.string()),
    agentPendingStateJson: v.optional(v.string()),
    promptTokens: v.number(),
    completionTokens: v.number(),
    totalTokens: v.number(),
    turnPromptTokens: v.optional(v.number()),
    cachedTokens: v.optional(v.number()),
    cacheWriteTokens: v.optional(v.number()),
    contextTokensEst: v.optional(v.number()),
    compactionThreshold: v.optional(v.number()),
  })
    .index("by_session_id", ["sessionId"])
    .index("by_last_message_at", ["lastMessageAt"]),

  chatMessages: defineTable({
    sessionId: v.string(),
    order: v.number(),
    messageId: v.string(),
    role: v.string(),
    timestamp: v.string(),
    streaming: v.boolean(),
    partsJson: v.string(),
  }).index("by_session_and_order", ["sessionId", "order"]),
});
