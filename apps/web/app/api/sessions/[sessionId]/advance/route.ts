import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(_request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const result = await proxyApi(`/api/v1/sessions/${sessionId}/advance`, "POST");
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
