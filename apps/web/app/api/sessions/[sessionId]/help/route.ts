import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await context.params;
  const form = await request.formData();
  const raw = String(form.get("kind") ?? "hint");
  const kind = raw === "solution" ? "solution" : raw === "explain" ? "explain" : "hint";
  const path =
    kind === "explain"
      ? `/api/v1/sessions/${sessionId}/explain`
      : `/api/v1/sessions/${sessionId}/${kind}`;
  const body = kind === "explain" ? undefined : JSON.stringify({ mode: "guided" });
  const result = await proxyApi(path, "POST", body);
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/learn/${sessionId}`);
}
