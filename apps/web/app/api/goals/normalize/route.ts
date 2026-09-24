import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request) {
  return proxyApi("/api/v1/goals/normalize", "POST", await request.text());
}
