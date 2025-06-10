import { auth } from "@clerk/nextjs";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function DashboardPage() {
  const { userId } = auth();

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Your Projects</h2>
        <div className="flex items-center space-x-2">
          <Button asChild>
            <Link href="/dashboard/editor">Create New Project</Link>
          </Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Example project card - we'll implement the real data fetching later */}
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="p-6 space-y-3">
            <h3 className="text-2xl font-semibold">Project Title</h3>
            <p className="text-sm text-muted-foreground">Last edited: 2 days ago</p>
            <div className="flex items-center space-x-2 pt-4">
              <Button variant="outline" size="sm" asChild>
                <Link href="/dashboard/editor/123">Edit</Link>
              </Button>
              <Button variant="outline" size="sm">Share</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
