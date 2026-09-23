import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ reviewId: string }> }) {
  const { reviewId } = await context.params;
  const form = await request.formData();
  const choice = String(form.get("choice") ?? "");
  const result = await proxyApi(
    `/api/v1/reviews/${reviewId}/attempts`,
    "POST",
    JSON.stringify({ choice }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath("/app/review");
}
