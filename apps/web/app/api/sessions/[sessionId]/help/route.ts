import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const kind = form.get("kind") === "solution" ? "solution" : "hint";
  const result = await proxyApi(
    `/api/v1/sessions/${sessionId}/${kind}`,
    "POST",
    JSON.stringify({ mode: "guided" }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
