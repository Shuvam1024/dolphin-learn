import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(_request: Request, context: { params: Promise<{ goalId: string }> }) {
  const { goalId } = await context.params;
  const result = await proxyApi(`/api/v1/goals/${goalId}/replan`, "POST", "{}");
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath(`/app/goals/${goalId}`);
}
