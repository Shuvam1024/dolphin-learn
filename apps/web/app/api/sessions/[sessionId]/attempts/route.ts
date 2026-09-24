import { proxyApi } from "@/lib/upstream";
import { redirectToPath } from "@/lib/session";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const idempotencyKey = String(form.get("idempotency_key") ?? "");
  const payload: Record<string, string> = { idempotency_key: idempotencyKey };
  const choice = form.get("choice");
  const text = form.get("text");
  const value = form.get("value");
  if (choice != null && String(choice)) payload.choice = String(choice);
  if (text != null && String(text)) payload.text = String(text);
  if (value != null && String(value)) payload.value = String(value);
  const result = await proxyApi(
    `/api/v1/sessions/${sessionId}/attempts`,
    "POST",
    JSON.stringify(payload),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
