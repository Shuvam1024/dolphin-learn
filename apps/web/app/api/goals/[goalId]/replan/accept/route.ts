import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ goalId: string }> }) {
  const { goalId } = await context.params;
  return proxyApi(`/api/v1/goals/${goalId}/replan/accept`, "POST", await request.text());
}
