import { proxyApi } from "@/lib/upstream";

export async function PATCH(request: Request, context: { params: Promise<{ goalId: string }> }) {
  const { goalId } = await context.params;
  return proxyApi(`/api/v1/goals/${goalId}`, "PATCH", await request.text());
}
