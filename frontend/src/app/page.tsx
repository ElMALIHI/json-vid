import Link from "next/link";
import { Navbar } from "@/components/shared/navbar";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Navbar />
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                  Professional Video Editing Made Simple
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                  Transform your content with our powerful video editing platform.
                  Easy to use, professional features, and real-time collaboration.
                </p>
              </div>
              <div className="space-x-4">
                <Link href="/sign-up">
                  <Button size="lg">Get Started</Button>
                </Link>
                <Link href="/features">
                  <Button variant="outline" size="lg">
                    Learn More
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="w-full py-12 md:py-24 lg:py-32 bg-gray-50 dark:bg-gray-800">
          <div className="container px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col justify-center space-y-4">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">
                    Professional Features
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400">
                    Access powerful editing tools designed for professional content
                    creators
                  </p>
                </div>
              </div>
              <div className="grid gap-6 lg:col-span-2 lg:grid-cols-2">
                <div className="flex flex-col justify-center space-y-4">
                  <h3 className="text-xl font-bold">Advanced Transitions</h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Choose from a wide range of professional transitions and effects
                  </p>
                </div>
                <div className="flex flex-col justify-center space-y-4">
                  <h3 className="text-xl font-bold">Real-time Collaboration</h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Work together with your team in real-time
                  </p>
                </div>
                <div className="flex flex-col justify-center space-y-4">
                  <h3 className="text-xl font-bold">Cloud Storage</h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Access your projects from anywhere with secure cloud storage
                  </p>
                </div>
                <div className="flex flex-col justify-center space-y-4">
                  <h3 className="text-xl font-bold">Export Options</h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Export in multiple formats and resolutions
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">
                  Ready to Start Creating?
                </h2>
                <p className="max-w-[600px] text-gray-500 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed dark:text-gray-400">
                  Join thousands of content creators who trust our platform
                </p>
              </div>
              <Link href="/sign-up">
                <Button size="lg">Get Started Now</Button>
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
