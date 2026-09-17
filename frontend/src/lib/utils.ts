/**
 * Copyright (c) 2023-2026 JunSu - AI
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License; see the LICENSE file at the repository root.
 * Based on langchain-ai/deep-agents-ui (MIT, Copyright (c) 2025 LangChain).
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
