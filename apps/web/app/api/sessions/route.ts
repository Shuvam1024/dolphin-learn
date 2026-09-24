import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request) {
  const form = await request.formData();
  const goalId = String(form.get("goal_id") ?? "");
  const rawTarget = form.get("target_minutes");
  const payload: { goal_id: string; target_minutes?: number } = { goal_id: goalId };
  if (rawTarget != null && String(rawTarget).trim()) {
    payload.target_minutes = Number(rawTarget);
  }
  const result = await proxyApi("/api/v1/sessions", "POST", JSON.stringify(payload));
  if (result.status >= 400) {
    return result;
  }
  const body = (await result.json()) as { id: string };
  return redirectToPath(`/app/learn/${body.id}`);
}
