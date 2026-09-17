/**
 * Copyright (c) 2023-2026 JunSu - AI
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License; see the LICENSE file at the repository root.
 * Based on langchain-ai/deep-agents-ui (MIT, Copyright (c) 2025 LangChain).
 */

import { Thread, ThreadStatus } from "@langchain/langgraph-sdk";

/**
 * Human interrupt configuration, specifying allowed actions when interrupted.
 */
export interface HumanInterruptConfig {
  allow_ignore: boolean;
  allow_respond: boolean;
  allow_edit: boolean;
  allow_accept: boolean;
}

/**
 * Action request from agent to human.
 * part of HumanInterrupt.
 */
export interface ActionRequest {
  action: string;
  args: Record<string, any>;
}

/**
 * Human interrupt in agent process.
 * Similar to LangGraph Interrupt type, but with specific human interaction fields.
 */
export interface HumanInterrupt {
  action_request: ActionRequest;
  config: HumanInterruptConfig;
  description?: string;
}

/**
 * Human response to agent interrupt.
 * Matches LangGraph SDK resume interrupt format.
 */
export type HumanResponse =
  | { type: "approve" }
  | { type: "edit"; edited_action: { name: string; args: Record<string, any> } }
  | { type: "reject"; message: string };

/**
 * Enhanced thread status type, including our custom status.
 * Based on LangGraph ThreadStatus.
 */
export type EnhancedThreadStatus = ThreadStatus | "human_response_needed";

/**
 * Base thread data interface, including common attributes.
 * as basis for all thread data types.
 */
interface BaseThreadData<T extends Record<string, any> = Record<string, any>> {
  thread: Thread<T>;
  invalidSchema?: boolean;
}

/**
 * Generic thread data for non-interrupted threads.
 * Follows discriminated union pattern, where status field serves as discriminator.
 */
export interface GenericThreadData<
  T extends Record<string, any> = Record<string, any>
> extends BaseThreadData<T> {
  status: "idle" | "busy" | "error" | "human_response_needed";
  interrupts?: undefined;
}

/**
 * Interrupted thread data.
 * Includes additional fields specific to interrupts.
 */
export interface InterruptedThreadData<
  T extends Record<string, any> = Record<string, any>
> extends BaseThreadData<T> {
  status: "interrupted";
  interrupts?: HumanInterrupt[];
}

/**
 * Union type for all thread data types.
 * Follows discriminated union pattern to ensure type safety.
 */
export type ThreadData<T extends Record<string, any> = Record<string, any>> =
  | GenericThreadData<T>
  | InterruptedThreadData<T>;

/**
 * Enhanced thread status type, including special "all" option for filtering.
 */
export type ThreadStatusWithAll = EnhancedThreadStatus | "all";

/**
 * Agent inbox configuration.
 */
export interface AgentInbox {
  /**
   * Unique identifier for the inbox.
   * Used in UI to identify the inbox.
   */
  id: string;
  /**
   * ID of the graph associated with the inbox.
   */
  graphId: string;
  /**
   * Deployment ID associated with the inbox.
   */
  deploymentId: string;
  /**
   * URL of the deployment.
   * @deprecated Use deploymentId instead.
   */
  deploymentUrl?: string;
  /**
   * Optional name for the inbox, displayed in UI.
   */
  name?: string;
  /**
   * Whether the inbox is selected.
   */
  tenantId?: string;
  createdAt: string;
}

