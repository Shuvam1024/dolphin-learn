import { GoalWizard } from "./wizard";

export default async function NewGoalPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; tool?: string }>;
}) {
  const params = await searchParams;
  return <GoalWizard initialPrompt={params.q ?? ""} tool={params.tool === "quick" ? "quick" : "plan"} />;
}
