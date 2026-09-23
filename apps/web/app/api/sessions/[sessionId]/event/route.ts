import { proxyApi } from "@/lib/upstream";
import { redirectToPath } from "@/lib/session";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const eventType = form.get("event_type");
  const kind = eventType === "resume" ? "resume" : "pause";
  const result = await proxyApi(
    `/api/v1/sessions/${sessionId}`,
    "PATCH",
    JSON.stringify({
      event: {
        client_event_id: crypto.randomUUID(),
        event_type: kind,
        payload: {},
      },
    }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
