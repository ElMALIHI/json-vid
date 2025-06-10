import { auth } from "@clerk/nextjs";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";

export default async function EditorPage() {
  const { userId } = auth();

  if (!userId) {
    redirect("/sign-in");
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <header className="border-b">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">Untitled Project</h2>
            <Button variant="outline" size="sm">Save</Button>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">Preview</Button>
            <Button size="sm">Export</Button>
          </div>
        </div>
      </header>

      <div className="grid flex-1 grid-cols-[300px_1fr_300px]">
        {/* Assets Panel */}
        <div className="border-r p-4">
          <div className="space-y-4">
            <h3 className="font-semibold">Assets</h3>
            <div className="rounded-lg border bg-card p-4">
              <Button variant="outline" className="w-full">Upload Media</Button>
            </div>
          </div>
        </div>

        {/* Preview Area */}
        <div className="flex flex-col items-center justify-center bg-black/5 p-4">
          <div className="aspect-video w-full max-w-[800px] rounded-lg bg-black shadow-lg">
            {/* Video preview will go here */}
          </div>
          {/* Timeline will go here */}
          <div className="mt-4 w-full max-w-[800px] rounded-lg border bg-card p-4">
            <div className="h-20 w-full rounded bg-accent/10"></div>
          </div>
        </div>

        {/* Properties Panel */}
        <div className="border-l p-4">
          <div className="space-y-4">
            <h3 className="font-semibold">Properties</h3>
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm text-muted-foreground">Select an element to edit its properties</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
