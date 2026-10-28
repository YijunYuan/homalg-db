import type { ClaimView } from "./types";
/** Client time is compared with the authoritative effective expiry, never recomputed. */
export function claimState(
  claim: ClaimView,
  now: number,
): "unclaimed" | "active" | "expired" {
  return claim.state === "unclaimed"
    ? "unclaimed"
    : Date.parse(claim.effective_expires_at || claim.expires_at || "") > now
      ? "active"
      : "expired";
}
