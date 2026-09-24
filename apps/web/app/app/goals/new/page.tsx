import { GoalChat } from "./chat";

export default async function NewGoalPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; tool?: string }>;
}) {
  const params = await searchParams;
  return (
    <GoalChat
      initialPrompt={params.q ?? ""}
      tool={params.tool === "quick" ? "quick" : "plan"}
    />
  );
}
