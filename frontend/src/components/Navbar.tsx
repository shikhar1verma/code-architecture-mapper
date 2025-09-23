'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'About', href: '/about' },
  ];

  const isActive = (href: string) => {
    return pathname === href;
  };

  return (
    <header className="sticky top-0 z-50 border-b bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 md:px-8">
        <Link href="/" className="text-lg font-semibold text-primary">
          Code Architecture Mapper
        </Link>

        {/* Desktop Navigation */}
        <ul className="hidden items-center gap-6 md:flex">
          {navigation.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`transition-colors duration-200 ${
                  isActive(item.href)
                    ? 'text-primary font-medium'
                    : 'text-gray-600 hover:text-primary'
                }`}
              >
                {item.name}
              </Link>
            </li>
          ))}
          <li>
            <a
              href="https://github.com/shikhar1verma/code-architecture-mapper"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md border border-primary px-3 py-1 text-primary hover:bg-primary hover:text-white transition-colors duration-200"
            >
              GitHub
            </a>
          </li>
        </ul>

        {/* Mobile menu button */}
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? (
            <X className="h-6 w-6 text-gray-800" />
          ) : (
            <Menu className="h-6 w-6 text-gray-800" />
          )}
        </button>
      </nav>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <ul className="space-y-2 bg-white px-4 pb-4 md:hidden">
          {navigation.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={() => setIsMenuOpen(false)}
                className={`block py-1 transition-colors duration-200 ${
                  isActive(item.href)
                    ? 'text-primary font-medium'
                    : 'text-gray-700 hover:text-primary'
                }`}
              >
                {item.name}
              </Link>
            </li>
          ))}
          <li>
            <a
              href="https://github.com/shikhar1verma/code-architecture-mapper"
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-md border border-primary px-3 py-1 text-center text-primary hover:bg-primary hover:text-white transition-colors duration-200"
            >
              GitHub
            </a>
          </li>
        </ul>
      )}
    </header>
  );
} 