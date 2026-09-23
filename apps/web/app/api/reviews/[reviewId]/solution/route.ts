import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(_request: Request, context: { params: Promise<{ reviewId: string }> }) {
  const { reviewId } = await context.params;
  const result = await proxyApi(
    `/api/v1/reviews/${reviewId}/solution`,
    "POST",
    JSON.stringify({ mode: "guided" }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath("/app/review");
}
