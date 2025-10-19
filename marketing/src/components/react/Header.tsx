import { Music } from 'lucide-react';

interface HeaderProps {
  isLoggedIn?: boolean;
}

export function Header({ isLoggedIn = false }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b-3 border-black">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <a href="/" className="flex items-center gap-3 group">
            <div className="border-3 border-black w-12 h-12 flex items-center justify-center bg-[#00eb90] neo-shadow-sm neo-transition group-hover:bg-[#ff73a9]">
              <Music size={24} className="text-black" />
            </div>
            <span className="text-xl uppercase tracking-wider">
              WavDash
            </span>
          </a>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="uppercase tracking-wider hover:text-[#00eb90] transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="uppercase tracking-wider hover:text-[#00eb90] transition-colors">
              How It Works
            </a>
            <a href="#pricing" className="uppercase tracking-wider hover:text-[#00eb90] transition-colors">
              Pricing
            </a>
          </nav>

          {/* Auth Buttons */}
          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift">
                Dashboard
              </button>
            ) : (
              <>
                <button className="border-3 border-black bg-white px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift hidden sm:block">
                  Login
                </button>
                <button className="border-3 border-black bg-[#00eb90] px-6 py-3 uppercase tracking-wider neo-shadow-sm neo-transition neo-hover-lift">
                  Register
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
