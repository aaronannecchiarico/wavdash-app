import { useState } from 'react';
import { Music, Menu } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

interface HeaderProps {
  isLoggedIn?: boolean;
}

export function Header({ isLoggedIn = false }: HeaderProps) {
  const [isOpen, setIsOpen] = useState(false);

  const appUrl = import.meta.env.PUBLIC_APP_URL || 'http://localhost:8000';

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#how-it-works', label: 'How it works' },
    { href: '#pricing', label: 'Pricing' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-[--border]">
      <div className="w-full px-6 md:px-12 py-4">
        <div className="flex items-center justify-between relative">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[--amber] group-hover:opacity-80 transition-opacity">
              <Music size={14} className="text-foreground" />
            </div>
            <span className="font-sans text-base font-semibold text-foreground tracking-tight">WavDash</span>
          </a>

          {/* Desktop nav — centered */}
          <nav className="hidden md:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop auth buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isLoggedIn ? (
              <a
                href={`${appUrl}/dashboard`}
                className="inline-flex items-center px-4 py-2 rounded-[--radius-md] bg-primary text-primary-foreground text-sm font-medium shadow-sm-studio hover:scale-[1.01] transition-all"
              >
                Dashboard
              </a>
            ) : (
              <>
                <a
                  href={`${appUrl}/login`}
                  className="text-sm font-medium text-foreground hover:text-[--amber] transition-colors"
                >
                  Sign in
                </a>
                <a
                  href={`${appUrl}/register`}
                  className="inline-flex items-center px-4 py-2 rounded-[--radius-md] bg-primary text-primary-foreground text-sm font-medium shadow-amber hover:scale-[1.01] transition-all"
                >
                  Get started
                </a>
              </>
            )}
          </div>

          {/* Mobile menu */}
          <div className="md:hidden">
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <button
                  className="flex h-8 w-8 items-center justify-center rounded-[--radius-md] hover:bg-muted transition-colors"
                  aria-label="Open menu"
                >
                  <Menu size={18} className="text-foreground" />
                </button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[280px] p-0">
                <SheetHeader className="px-5 py-5 border-b border-[--border]">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[--amber] shrink-0">
                      <Music size={14} className="text-foreground" />
                    </div>
                    <SheetTitle className="font-sans text-base font-semibold text-foreground tracking-tight">
                      WavDash
                    </SheetTitle>
                  </div>
                </SheetHeader>

                <nav className="flex flex-col space-y-0.5 px-3 py-4">
                  {navLinks.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      onClick={() => setIsOpen(false)}
                      className="flex items-center px-3 py-2.5 rounded-[--radius-md] text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    >
                      {link.label}
                    </a>
                  ))}
                </nav>

                <div className="flex flex-col gap-3 px-4 pt-4 border-t border-[--border]">
                  {isLoggedIn ? (
                    <a
                      href={`${appUrl}/dashboard`}
                      className="inline-flex items-center justify-center px-4 py-2.5 rounded-[--radius-md] bg-primary text-primary-foreground text-sm font-medium shadow-sm-studio"
                    >
                      Dashboard
                    </a>
                  ) : (
                    <>
                      <a
                        href={`${appUrl}/login`}
                        className="inline-flex items-center justify-center px-4 py-2.5 rounded-[--radius-md] border border-[--border-strong] text-foreground text-sm font-medium hover:bg-muted transition-colors"
                      >
                        Sign in
                      </a>
                      <a
                        href={`${appUrl}/register`}
                        className="inline-flex items-center justify-center px-4 py-2.5 rounded-[--radius-md] bg-primary text-primary-foreground text-sm font-medium shadow-amber"
                      >
                        Get started free
                      </a>
                    </>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
