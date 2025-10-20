import { useState } from 'react';
import { Music, Menu, X } from 'lucide-react';
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

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#how-it-works', label: 'How It Works' },
    { href: '#pricing', label: 'Pricing' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b-3 border-black">
      <div className="w-full px-8 md:px-12 py-5">
        <div className="flex items-center justify-between relative">
          {/* Logo - Left */}
          <a href="/" className="flex items-center gap-3 group flex-shrink-0">
            <div className="border-3 border-black w-12 h-12 flex items-center justify-center bg-[#00eb90] neo-shadow-sm neo-transition group-hover:bg-[#ff73a9]">
              <Music size={24} className="text-black" />
            </div>
            <span className="text-xl uppercase tracking-wider">
              WavDash
            </span>
          </a>

          {/* Desktop Navigation - Absolutely Centered on Viewport */}
          <nav className="hidden md:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="uppercase tracking-wider hover:text-[#00eb90] transition-colors whitespace-nowrap"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop Auth Buttons - Right */}
          <div className="hidden md:flex items-center gap-4">
            {isLoggedIn ? (
              <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift">
                Dashboard
              </button>
            ) : (
              <>
                <button className="border-3 border-black bg-white px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift">
                  Login
                </button>
                <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift">
                  Register
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <button
                  className="border-3 border-black bg-white p-2 neo-shadow-sm"
                  aria-label="Open menu"
                >
                  <Menu size={24} className="text-black" />
                </button>
              </SheetTrigger>
              <SheetContent
                side="right"
                className="w-[300px] sm:w-[400px] border-l-3 border-black bg-white p-0"
              >
                <SheetHeader className="border-b-3 border-black p-6">
                  <SheetTitle className="text-left uppercase tracking-wider text-2xl">
                    Menu
                  </SheetTitle>
                </SheetHeader>

                {/* Mobile Navigation */}
                <nav className="flex flex-col p-6 space-y-6">
                  {navLinks.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      onClick={() => setIsOpen(false)}
                      className="uppercase tracking-wider hover:text-[#00eb90] transition-colors text-lg border-b-2 border-black pb-4"
                    >
                      {link.label}
                    </a>
                  ))}

                  {/* Mobile Auth Buttons */}
                  <div className="flex flex-col gap-4 pt-4">
                    {isLoggedIn ? (
                      <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition w-full">
                        Dashboard
                      </button>
                    ) : (
                      <>
                        <button className="border-3 border-black bg-white px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition w-full">
                          Login
                        </button>
                        <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition w-full">
                          Register
                        </button>
                      </>
                    )}
                  </div>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
