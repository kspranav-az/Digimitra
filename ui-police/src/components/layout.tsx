import Link from 'next/link';

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="p-4 border-b">
        <nav className="flex items-center gap-4">
          <Link href="/">Dashboard</Link>
          <Link href="/map">Map</Link>
          <Link href="/events">Events</Link>
          <Link href="/search">Search</Link>
        </nav>
      </header>
      <main className="p-8">
        {children}
      </main>
    </div>
  )
}
