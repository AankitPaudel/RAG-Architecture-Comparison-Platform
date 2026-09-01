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
                onClick={() => setActiveView(view)}
                className={`inline-flex items-center gap-2 rounded px-4 py-2 text-sm font-medium transition-colors ${
                    active ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
            >
                <Icon className="h-4 w-4" />
                {label}
            </button>
        );
    };

    return (
        <div className="app min-h-screen bg-gray-50">
            <nav className="fixed left-1/2 top-4 z-30 flex -translate-x-1/2 rounded-lg border border-gray-200 bg-white p-1 shadow-md">
                {navButton('chat', MessageSquare, 'Chat')}
                {navButton('sources', Database, 'Sources')}
                {navButton('compare', GitCompare, 'Compare')}
                {navButton('evaluation', BarChart3, 'Evaluation')}
            </nav>

            <main className="app-main">
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
