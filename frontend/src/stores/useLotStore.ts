import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

export type StepInfo = {
  label: string;
  status: "pending" | "running" | "completed" | "error";
  tokens?: number;
  cost?: number;
};

type LotState = {
  // Map of conversationId -> map of stepKey -> StepInfo
  lots: Record<string, Record<string, StepInfo>>;
  setStep: (convId: string, stepKey: string, data: Partial<StepInfo>) => void;
};

export const useLotStore = create<LotState>()(
  immer((set) => ({
    lots: {},
    setStep: (convId, stepKey, data) =>
      set((state) => {
        if (!state.lots[convId]) {
          state.lots[convId] = {};
        }
        const existing = state.lots[convId][stepKey] ?? { label: stepKey, status: "pending" };
        state.lots[convId][stepKey] = { ...existing, ...data };
      }),
  }))
);
