'use client';

import { Component } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { FileText, AlertTriangle, TestTube, Link, Code2 } from 'lucide-react';

interface ComponentsViewProps {
  components: Component[];
}

export function ComponentsView({ components }: ComponentsViewProps) {
  if (!components || components.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Code2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No components analyzed yet.</p>
        <p className="text-sm">Component analysis will appear here after repository analysis.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Component Analysis</h3>
        <Badge variant="secondary">{components.length} components</Badge>
      </div>
      
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
        {components.map((component, index) => (
          <ComponentCard key={index} component={component} />
        ))}
      </div>
    </div>
  );
}

interface ComponentCardProps {
  component: Component;
}

function ComponentCard({ component }: ComponentCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Code2 className="w-5 h-5 text-blue-600" />
          {component.name}
        </CardTitle>
        <p className="text-sm text-gray-600">{component.purpose}</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Key Files */}
        {component.key_files && component.key_files.length > 0 && (
          <div>
            <h4 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <FileText className="w-4 h-4" />
              Key Files
            </h4>
            <div className="space-y-1">
              {component.key_files.map((file, idx) => (
                <div key={idx} className="text-xs">
                  <code className="bg-gray-100 px-2 py-1 rounded text-blue-600">
                    {file.path}
                  </code>
                  {file.reason && (
                    <span className="text-gray-500 ml-2">- {file.reason}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* APIs */}
        {component.apis && component.apis.length > 0 && (
          <div>
            <h4 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Link className="w-4 h-4" />
              APIs
            </h4>
            <div className="flex flex-wrap gap-1">
              {component.apis.map((api, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {api.name}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dependencies */}
        {component.dependencies && component.dependencies.length > 0 && (
          <div>
            <h4 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Code2 className="w-4 h-4" />
              Dependencies
            </h4>
            <div className="flex flex-wrap gap-1">
              {component.dependencies.map((dep, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {dep}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Tests */}
        {component.tests && component.tests.length > 0 && (
          <div>
            <h4 className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <TestTube className="w-4 h-4" />
              Tests
            </h4>
            <div className="space-y-1">
              {component.tests.map((test, idx) => (
                <code key={idx} className="block text-xs bg-green-50 px-2 py-1 rounded text-green-700">
                  {test}
                </code>
              ))}
            </div>
          </div>
        )}

        {/* Risks */}
        {component.risks && component.risks.length > 0 && (
          <div>
            <h4 className="flex items-center gap-2 text-sm font-medium text-red-700 mb-2">
              <AlertTriangle className="w-4 h-4" />
              Risks
            </h4>
            <div className="space-y-1">
              {component.risks.map((risk, idx) => (
                <div key={idx} className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                  {risk}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 