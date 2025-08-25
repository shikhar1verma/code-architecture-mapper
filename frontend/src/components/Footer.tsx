export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 bg-white py-6">
      <div className="container mx-auto max-w-6xl px-4 text-center text-sm text-gray-600">
        <p>
          © {currentYear} &nbsp;
          <a
            href="https://theshikhar.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            Shikhar Verma
          </a>
          &nbsp;• AI-powered code analysis tool for developers.
        </p>
        <p className="mt-2">
          Made with ❤️ for developers • Source code on{" "}
          <a
            href="https://github.com/shikhar1verma/code-architecture-mapper"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            GitHub
          </a>
        </p>
      </div>
    </footer>
  );
} 