import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(
  request: Request,
  context: { params: Promise<{ goalId: string }> },
) {
  const { goalId } = await context.params;
  const form = await request.formData();
  const status = String(form.get("status") ?? "");
  const result = await proxyApi(
    `/api/v1/goals/${goalId}`,
    "PATCH",
    JSON.stringify({ status }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath("/app/learn");
}
