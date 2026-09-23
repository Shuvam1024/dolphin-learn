import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request) {
  const form = await request.formData();
  const goalId = String(form.get("goal_id") ?? "");
  const result = await proxyApi("/api/v1/sessions", "POST", JSON.stringify({ goal_id: goalId }));
  if (result.status >= 400) {
    return result;
  }
  const body = (await result.json()) as { id: string };
  return redirectToPath(`/app/learn/${body.id}`);
}
