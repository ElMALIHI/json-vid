import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";

export function DashboardNav() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="font-bold">
            VideoForge
          </Link>
          <nav className="hidden md:flex gap-6">
            <Link
              href="/dashboard"
              className="transition-colors hover:text-foreground/80 text-foreground"
            >
              Projects
            </Link>
            <Link
              href="/dashboard/editor"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              New Project
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline" asChild>
            <Link href="/dashboard/editor">New Video</Link>
          </Button>
          <UserButton afterSignOutUrl="/" />
        </div>
      </div>
    </header>
  );
}
