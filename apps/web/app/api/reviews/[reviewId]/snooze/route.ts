import { redirectToPath } from "@/lib/session";
import { proxyApi } from "@/lib/upstream";

export async function POST(request: Request, context: { params: Promise<{ reviewId: string }> }) {
  const { reviewId } = await context.params;
  const form = await request.formData();
  const hours = Number(form.get("hours") ?? "24");
  const result = await proxyApi(
    `/api/v1/reviews/${reviewId}/snooze`,
    "POST",
    JSON.stringify({ hours }),
  );
  if (result.status >= 400) {
    return result;
  }
  return redirectToPath("/app/review");
}
