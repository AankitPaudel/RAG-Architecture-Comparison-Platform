import React from 'react';
import { Database, MessageSquare, GitCompare, BarChart3 } from 'lucide-react';
import { ChatInterface } from './components/ChatInterface';
import { ComparisonPage } from './components/ComparisonPage';
import { EvaluationPage } from './components/EvaluationPage';
import { SourcesPage } from './components/SourcesPage';
import { AppContextProvider } from './context/AppContext';
import './styles/main.css';

function MainContent() {
    const [activeView, setActiveView] = React.useState('compare');

    const navButton = (view, icon, label) => {
        const Icon = icon;
        const active = activeView === view;
        return (
            <button
                key={view}
                type="button"
                onClick={() => setActiveView(view)}
                className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors sm:px-4 ${
                    active
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-gray-600 hover:bg-white hover:text-gray-900'
                }`}
            >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
            </button>
        );
    };

    const navItems = [
        navButton('chat', MessageSquare, 'Chat'),
        navButton('sources', Database, 'Sources'),
        navButton('compare', GitCompare, 'Compare'),
        navButton('evaluation', BarChart3, 'Evaluation'),
    ];

    return (
        <div className="app flex min-h-screen flex-col bg-gray-50">
            <header className="sticky top-0 z-50 shrink-0 border-b border-gray-200 bg-white shadow-sm">
                <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
                    <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-gray-900 sm:text-base">
                            RAG Architecture Comparison
                        </p>
                        <p className="hidden text-xs text-gray-500 sm:block">
                            Compare Naive, Hybrid, Agentic, and GraphRAG
                        </p>
                    </div>

                    <nav
                        className="flex w-full flex-wrap items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1 sm:w-auto sm:flex-nowrap"
                        aria-label="Main navigation"
                    >
                        {navItems}
                    </nav>
                </div>
            </header>

            <main className="app-main min-h-0 flex-1 overflow-hidden">
                {activeView === 'chat' && <ChatInterface />}
                {activeView === 'sources' && <SourcesPage />}
                {activeView === 'compare' && <ComparisonPage />}
                {activeView === 'evaluation' && <EvaluationPage />}
            </main>
        </div>
    );
}

function App() {
    return (
        <AppContextProvider>
            <MainContent />
        </AppContextProvider>
    );
}

export default App;
