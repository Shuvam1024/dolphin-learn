import { proxyApi } from "@/lib/upstream";
import { redirectToPath } from "@/lib/session";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const choice = String(form.get("choice") ?? "");
  const idempotencyKey = String(form.get("idempotency_key") ?? "");
  const result = await proxyApi(
    `/api/v1/sessions/${sessionId}/attempts`,
    "POST",
    JSON.stringify({ idempotency_key: idempotencyKey, choice }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
