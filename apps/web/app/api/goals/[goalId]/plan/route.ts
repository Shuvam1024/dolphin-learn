import { proxyApi } from "@/lib/upstream";

export async function GET(_request: Request, context: { params: Promise<{ goalId: string }> }) {
  const { goalId } = await context.params;
  return proxyApi(`/api/v1/goals/${goalId}/plan`, "GET");
}
