import { Code2, Brain, FileText, GitBranch, Zap, Shield } from 'lucide-react';

export default function About() {
  const features = [
    {
      icon: <Brain className="w-6 h-6" />,
      title: 'AI-Powered Analysis',
      description: 'Uses advanced AI models to understand code structure and generate meaningful insights about your repository architecture.',
    },
    {
      icon: <GitBranch className="w-6 h-6" />,
      title: 'Dependency Mapping',
      description: 'Visualizes complex dependency relationships between files and modules with interactive Mermaid diagrams.',
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: 'Comprehensive Reports',
      description: 'Generates detailed documentation and reports that can be downloaded and shared with your team.',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Fast Processing',
      description: 'Efficiently analyzes repositories with intelligent caching and optimized processing pipelines.',
    },
    {
      icon: <Code2 className="w-6 h-6" />,
      title: 'Multi-Language Support',
      description: 'Supports Python, TypeScript, and JavaScript codebases with language-specific analysis capabilities.',
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'Secure & Private',
      description: 'Analyzes public repositories safely without storing your code or compromising your data.',
    },
  ];

  const stats = [
    { label: 'Languages Supported', value: '3' },
    { label: 'Demo Examples', value: '3+' },
    { label: 'Tech Stack Components', value: '8+' },
    { label: 'Average Analysis Time', value: '<2min' },
  ];

  return (
    <div className="bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center w-16 h-16 bg-primary rounded-2xl mx-auto mb-6">
            <Code2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            About Code Architecture Mapper
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            A powerful tool designed to help developers understand, analyze, and visualize 
            the architecture of their codebases using artificial intelligence.
          </p>
        </div>

        {/* About Section */}
        <div className="bg-white rounded-lg shadow-sm border p-8 mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">About This Project</h2>
          <p className="text-gray-700 text-lg leading-relaxed mb-4">
            This is an educational demo showcasing how AI can be used to analyze 
            and understand code architecture. Whether you&apos;re exploring a new codebase, documenting 
            existing projects, or learning about software architecture patterns, this tool provides 
            automated insights into code structure and dependencies.
          </p>
          <p className="text-gray-700 text-lg leading-relaxed">
            This application 
            combines AI-powered analysis with interactive visualizations to make code exploration more 
            accessible and insightful.
          </p>
        </div>

        {/* Features Grid */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center justify-center w-12 h-12 bg-blue-50 text-primary rounded-lg mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Section */}
        <div className="bg-primary rounded-lg p-8 mb-16">
          <h2 className="text-2xl font-bold text-white text-center mb-8">Project Highlights</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-blue-100">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-lg shadow-sm border p-8 mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 text-primary rounded-full mx-auto mb-4 font-bold">
                1
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Input Repository</h3>
              <p className="text-gray-600">Provide a GitHub repository URL or try demo examples</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 text-primary rounded-full mx-auto mb-4 font-bold">
                2
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-600">AI processes the code structure and relationships</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 text-primary rounded-full mx-auto mb-4 font-bold">
                3
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Get Insights</h3>
              <p className="text-gray-600">View comprehensive reports and interactive diagrams</p>
            </div>
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-white rounded-lg shadow-sm border p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Built With Modern Technology</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">Frontend</div>
              <div className="text-gray-600">Next.js, React, Tailwind CSS</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">Backend</div>
              <div className="text-gray-600">Python, Flask, SQLite</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">AI/ML</div>
              <div className="text-gray-600">Google Gemini, LangChain</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">Visualization</div>
              <div className="text-gray-600">Mermaid.js, D3.js</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 