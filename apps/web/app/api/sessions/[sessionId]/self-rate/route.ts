import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const rating = String(form.get("rating") ?? "");
  const result = await proxyApi(
    `/api/v1/sessions/${sessionId}/self-rate`,
    "POST",
    JSON.stringify({ rating }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
