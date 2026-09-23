import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";

import { GoalWizard } from "./wizard";

export default async function NewGoalPage() {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }

  return <GoalWizard />;
}
