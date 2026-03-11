import { mutationGeneric, queryGeneric } from "convex/server";
import { v } from "convex/values";

const sessionStateArgs = {
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
  messages: v.array(
    v.object({
      messageId: v.string(),
      role: v.string(),
      timestamp: v.string(),
      streaming: v.boolean(),
      partsJson: v.string(),
    })
  ),
};

function compact<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(
    Object.entries(value).filter(([, entry]) => entry !== undefined)
  ) as T;
}

export const saveSessionState = mutationGeneric({
  args: sessionStateArgs,
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("chatSessions")
      .withIndex("by_session_id", (q) => q.eq("sessionId", args.sessionId))
      .unique();

    const sessionRecord = compact({
      sessionId: args.sessionId,
      name: args.name,
      createdAt: args.createdAt,
      lastMessageAt: args.lastMessageAt,
      messageCount: args.messageCount,
      workspacePath: args.workspacePath,
      configJson: args.configJson,
      pendingInputJson: args.pendingInputJson,
      agentMessagesJson: args.agentMessagesJson,
      agentPendingStateJson: args.agentPendingStateJson,
      promptTokens: args.promptTokens,
      completionTokens: args.completionTokens,
      totalTokens: args.totalTokens,
      turnPromptTokens: args.turnPromptTokens,
      cachedTokens: args.cachedTokens,
      cacheWriteTokens: args.cacheWriteTokens,
      contextTokensEst: args.contextTokensEst,
      compactionThreshold: args.compactionThreshold,
    });

    if (existing) {
      await ctx.db.patch(existing._id, sessionRecord);
    } else {
      await ctx.db.insert("chatSessions", sessionRecord);
    }

    const existingMessages = await ctx.db
      .query("chatMessages")
      .withIndex("by_session_and_order", (q) => q.eq("sessionId", args.sessionId))
      .collect();

    for (const message of existingMessages) {
      await ctx.db.delete(message._id);
    }

    for (let order = 0; order < args.messages.length; order += 1) {
      const message = args.messages[order];
      await ctx.db.insert("chatMessages", {
        sessionId: args.sessionId,
        order,
        messageId: message.messageId,
        role: message.role,
        timestamp: message.timestamp,
        streaming: message.streaming,
        partsJson: message.partsJson,
      });
    }

    return { sessionId: args.sessionId };
  },
});

export const listSessions = queryGeneric({
  args: {},
  handler: async (ctx) => {
    const sessions = await ctx.db
      .query("chatSessions")
      .withIndex("by_last_message_at")
      .order("desc")
      .collect();

    return sessions.map((session) => ({
      id: session.sessionId,
      name: session.name,
      createdAt: session.createdAt,
      lastMessageAt: session.lastMessageAt,
      messageCount: session.messageCount,
      workspacePath: session.workspacePath,
      tokenUsage: {
        promptTokens: session.promptTokens,
        completionTokens: session.completionTokens,
        totalTokens: session.totalTokens,
        turnPromptTokens: session.turnPromptTokens,
        cachedTokens: session.cachedTokens,
        cacheWriteTokens: session.cacheWriteTokens,
        contextTokensEst: session.contextTokensEst,
        compactionThreshold: session.compactionThreshold,
      },
    }));
  },
});

export const getSessionState = queryGeneric({
  args: { sessionId: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_session_id", (q) => q.eq("sessionId", args.sessionId))
      .unique();

    if (!session) {
      return null;
    }

    const messages = await ctx.db
      .query("chatMessages")
      .withIndex("by_session_and_order", (q) => q.eq("sessionId", args.sessionId))
      .collect();

    return {
      id: session.sessionId,
      name: session.name,
      createdAt: session.createdAt,
      lastMessageAt: session.lastMessageAt,
      messageCount: session.messageCount,
      workspacePath: session.workspacePath,
      configJson: session.configJson ?? null,
      pendingInputJson: session.pendingInputJson ?? null,
      agentMessagesJson: session.agentMessagesJson ?? null,
      agentPendingStateJson: session.agentPendingStateJson ?? null,
      tokenUsage: {
        promptTokens: session.promptTokens,
        completionTokens: session.completionTokens,
        totalTokens: session.totalTokens,
        turnPromptTokens: session.turnPromptTokens,
        cachedTokens: session.cachedTokens,
        cacheWriteTokens: session.cacheWriteTokens,
        contextTokensEst: session.contextTokensEst,
        compactionThreshold: session.compactionThreshold,
      },
      messages: messages.map((message) => ({
        id: message.messageId,
        role: message.role,
        timestamp: message.timestamp,
        streaming: message.streaming,
        partsJson: message.partsJson,
      })),
    };
  },
});

export const renameSession = mutationGeneric({
  args: { sessionId: v.string(), name: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_session_id", (q) => q.eq("sessionId", args.sessionId))
      .unique();

    if (!session) {
      return null;
    }

    await ctx.db.patch(session._id, {
      name: args.name,
      lastMessageAt: new Date().toISOString(),
    });

    return { title: args.name };
  },
});

export const deleteSession = mutationGeneric({
  args: { sessionId: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_session_id", (q) => q.eq("sessionId", args.sessionId))
      .unique();

    if (session) {
      await ctx.db.delete(session._id);
    }

    const messages = await ctx.db
      .query("chatMessages")
      .withIndex("by_session_and_order", (q) => q.eq("sessionId", args.sessionId))
      .collect();

    for (const message of messages) {
      await ctx.db.delete(message._id);
    }

    return { deleted: args.sessionId };
  },
});
