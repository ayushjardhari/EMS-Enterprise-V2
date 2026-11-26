import { api } from "./api";
import type { MatchRequestPayload, MatchResponse } from "../types/matching";

export const matchingService = {
  search: (payload: MatchRequestPayload) => api.post<MatchResponse>("/matching/search", payload),
};
