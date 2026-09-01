import React, { useState } from 'react';
import { BarChart3, Loader2, Play } from 'lucide-react';
import { api } from '../services/api';

const PIPELINE_LABELS = {
    naive: 'Naive RAG',
    hybrid: 'Hybrid RAG',
    agentic: 'Agentic RAG',
    graph: 'GraphRAG',
};

const MetricTable = ({ title, metrics }) => (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-900">{title}</h3>
        <div className="space-y-2 text-sm">
            {Object.entries(metrics).map(([key, value]) => (
                <div key={key} className="flex justify-between text-gray-700">
                    <span className="text-gray-500">{key}</span>
                    <span>{value ?? '—'}</span>
                </div>
            ))}
        </div>
    </div>
);

export const EvaluationPage = () => {
    const [results, setResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const runEvaluation = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await api.runEvaluation();
            setResults(response);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="knowledge-shell flex h-screen flex-col bg-gray-50 text-gray-900">
            <header className="relative z-10 border-b border-gray-200 bg-white px-6 py-5">
                <div className="mx-auto max-w-6xl">
                    <h1 className="text-2xl font-semibold">RAG Evaluation</h1>
                    <p className="mt-1 max-w-3xl text-sm text-gray-600">
                        Benchmark all four RAG architectures using a fixed evaluation dataset with ground-truth chunk IDs.
                    </p>
                </div>
            </header>

            <main className="relative z-10 mx-auto w-full max-w-6xl flex-1 overflow-y-auto px-6 py-5 pt-20">
                <div className="mb-6 flex items-center gap-3">
                    <button onClick={runEvaluation} disabled={isLoading} className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                        Run Evaluation
                    </button>
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                </div>

                {error && (
                    <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
                )}

                {results?.notes && (
                    <div className="mb-4 space-y-2">
                        {results.notes.map((note) => (
                            <div key={note} className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">{note}</div>
                        ))}
                    </div>
                )}

                {results?.pipelines && (
                    <div className="grid gap-4 md:grid-cols-2">
                        {Object.entries(results.pipelines).map(([name, pipeline]) => (
                            <section key={name} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                                <h2 className="mb-4 text-lg font-semibold text-gray-900">{PIPELINE_LABELS[name] || name}</h2>
                                <div className="grid gap-4">
                                    <MetricTable title="Retrieval Metrics (averages)" metrics={pipeline.averages} />
                                    <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                                        <div className="mb-2 font-medium text-gray-900">Operational Metrics</div>
                                        <div className="flex justify-between"><span className="text-gray-500">Avg latency</span><span>{pipeline.averages?.avg_latency_ms ?? '—'} ms</span></div>
                                        <div className="flex justify-between"><span className="text-gray-500">Avg tokens</span><span>{pipeline.averages?.avg_token_usage ?? '—'}</span></div>
                                        <div className="flex justify-between"><span className="text-gray-500">Errors</span><span>{pipeline.errors?.length ?? 0}</span></div>
                                    </div>
                                </div>
                            </section>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default EvaluationPage;
