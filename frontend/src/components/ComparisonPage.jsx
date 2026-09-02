import React, { useEffect, useState } from 'react';
import { Search, Loader2, BrainCircuit, Layers, Bot, Share2 } from 'lucide-react';
import { api } from '../services/api';

const PIPELINES = ['naive', 'hybrid', 'agentic', 'graph'];

const PIPELINE_META = {
    naive: {
        title: 'Naive RAG',
        icon: BrainCircuit,
        description: 'Dense vector similarity search over ChromaDB embeddings.',
        retrievalMethod: 'Vector similarity',
    },
    hybrid: {
        title: 'Hybrid RAG',
        icon: Layers,
        description: 'Dense + BM25 retrieval, fused with RRF and reranked.',
        retrievalMethod: 'Dense + BM25 + RRF + rerank',
    },
    agentic: {
        title: 'Agentic RAG',
        icon: Bot,
        description: 'Self-correcting retrieval with evidence grading and query rewriting.',
        retrievalMethod: 'Hybrid retriever with retry loop',
    },
    graph: {
        title: 'GraphRAG',
        icon: Share2,
        description: 'Entity graph traversal to retrieve supporting source chunks.',
        retrievalMethod: 'Entity graph traversal (2 hops)',
    },
};

const formatMs = (value) => (typeof value === 'number' ? `${value.toFixed(1)} ms` : '—');
const formatTokens = (tokenUsage) => tokenUsage?.total_tokens ?? '—';
const dash = (value) => (value === null || value === undefined || value === '' ? '—' : value);

const MetricRow = ({ label, value }) => (
    <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span className="font-medium text-gray-800">{value}</span>
    </div>
);

const ChunkCard = ({ chunk, index }) => (
    <article className="rounded-md border border-gray-200 bg-gray-50 p-3">
        <div className="mb-2 flex flex-wrap gap-2 text-[11px] text-gray-500">
            <span className="rounded bg-blue-50 text-blue-700">#{index + 1}</span>
            {chunk.metadata?.title && <span className="text-gray-800">{chunk.metadata.title}</span>}
            {typeof chunk.dense_rank === 'number' && <span className="rounded bg-gray-100 px-2 py-0.5">dense {chunk.dense_rank}</span>}
            {typeof chunk.bm25_rank === 'number' && <span className="rounded bg-gray-100 px-2 py-0.5">bm25 {chunk.bm25_rank}</span>}
            {typeof chunk.fused_rank === 'number' && <span className="rounded bg-gray-100 px-2 py-0.5">fused {chunk.fused_rank}</span>}
            {typeof chunk.reranked_rank === 'number' && <span className="rounded bg-emerald-50 text-emerald-700">reranked {chunk.reranked_rank}</span>}
        </div>
        <p className="line-clamp-4 text-sm leading-6 text-gray-700">{chunk.content}</p>
    </article>
);

const ArchitectureDetails = ({ pipelineName, result }) => {
    if (!result) return null;

    if (pipelineName === 'naive') {
        return (
            <div className="space-y-1 text-xs text-gray-500">
                <div>Vector similarity over top-{result.chunks_sent_to_llm} chunks</div>
                <div>Chunks retrieved: {dash(result.num_chunks_retrieved)}</div>
            </div>
        );
    }

    if (pipelineName === 'hybrid') {
        return (
            <div className="space-y-1 text-xs text-gray-500">
                <div>Dense + BM25 candidates considered: {dash(result.chunks_considered)}</div>
                <div>Fused and reranked to top-{dash(result.chunks_sent_to_llm)}</div>
            </div>
        );
    }

    if (pipelineName === 'agentic') {
        const attempts = result.execution_trace || [];
        const rewrites = attempts.filter((attempt) => attempt.rewritten_query).length;
        const finalAttempt = attempts[attempts.length - 1];
        return (
            <div className="space-y-1 text-xs text-gray-500">
                <div>Retrieval attempts: {attempts.length || '—'}</div>
                <div>Query rewrites: {rewrites}</div>
                <div>Final evidence confidence: {dash(finalAttempt?.evidence_confidence)}</div>
                <div>Final decision: {dash(finalAttempt?.decision)}</div>
            </div>
        );
    }

    if (pipelineName === 'graph') {
        return (
            <div className="space-y-1 text-xs text-gray-500">
                <div>Matched entities: {(result.matched_entities || []).join(', ') || '—'}</div>
                <div>Graph nodes: {result.graph_nodes?.length ?? 0}</div>
                <div>Relationships: {result.relationships?.length ?? 0}</div>
                <div>Graph hops: {dash(result.hop_count)}</div>
            </div>
        );
    }

    return null;
};

const PipelineCard = ({ pipelineName, payload }) => {
    const meta = PIPELINE_META[pipelineName];
    const Icon = meta.icon;
    const result = payload?.result;
    const failed = !payload?.success;

    return (
        <section className="flex min-h-[560px] flex-col border-l border-gray-200 bg-white p-5 backdrop-blur first:border-l-0">
            <div className="mb-4 flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-blue-200 bg-blue-50 text-blue-600">
                    <Icon className="h-5 w-5" />
                </div>
                <div>
                    <h2 className="text-base font-semibold text-gray-900">{meta.title}</h2>
                    <p className="mt-1 text-sm text-gray-500">{meta.description}</p>
                </div>
            </div>

            {failed ? (
                <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    {payload?.error || 'Pipeline failed'}
                </div>
            ) : (
                <div className="space-y-4">
                    <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                        <h3 className="mb-2 text-xs uppercase tracking-wide text-gray-500">Answer</h3>
                        <p className="text-sm leading-6 text-gray-800">{result.answer}</p>
                    </div>

                    <div className="grid gap-2 rounded-md border border-gray-200 bg-gray-50 p-3">
                        <MetricRow label="Retrieval time" value={formatMs(result.retrieval_time_ms)} />
                        <MetricRow label="Reranking time" value={formatMs(result.reranking_time_ms)} />
                        <MetricRow label="Generation time" value={formatMs(result.generation_time_ms)} />
                        <MetricRow label="Total latency" value={formatMs(result.total_time_ms)} />
                        <MetricRow label="Tokens" value={formatTokens(result.token_usage)} />
                        <MetricRow label="Chunks considered" value={dash(result.chunks_considered)} />
                        <MetricRow label="Chunks sent to LLM" value={dash(result.chunks_sent_to_llm)} />
                    </div>

                    <ArchitectureDetails pipelineName={pipelineName} result={result} />

                    {result.citations?.length > 0 && (
                        <div>
                            <h3 className="mb-2 text-xs uppercase tracking-wide text-gray-500">Citations</h3>
                            <div className="flex flex-wrap gap-2">
                                {result.citations.map((citation) => (
                                    <span key={`${pipelineName}-${citation.source}`} className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
                                        {citation.title || citation.source}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {pipelineName === 'graph' && result.relationships?.length > 0 && (
                        <div>
                            <h3 className="mb-2 text-xs uppercase tracking-wide text-gray-500">Relationships Used</h3>
                            <div className="space-y-2">
                                {result.relationships.map((rel, index) => (
                                    <div key={`${pipelineName}-rel-${index}`} className="rounded-md border border-gray-200 bg-gray-50 p-2 text-xs text-gray-700">
                                        {rel.source} <span className="text-blue-700">{rel.relation}</span> {rel.target}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {pipelineName === 'agentic' && result.execution_trace?.length > 0 && (
                        <div>
                            <h3 className="mb-2 text-xs uppercase tracking-wide text-gray-500">Retrieval Attempts</h3>
                            <div className="space-y-2">
                                {result.execution_trace.map((attempt) => (
                                    <div key={`${pipelineName}-attempt-${attempt.attempt}`} className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
                                        <div className="mb-1 font-medium text-gray-100">Attempt {attempt.attempt}</div>
                                        <div>Query: {attempt.query}</div>
                                        <div>Confidence: {attempt.evidence_confidence}</div>
                                        <div>Decision: {attempt.decision}</div>
                                        {attempt.rewritten_query && <div className="mt-1 text-blue-700">Rewritten: {attempt.rewritten_query}</div>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </section>
    );
};

const getComparisonValue = (pipelineName, rowKey, result) => {
    if (!result) return '—';

    switch (rowKey) {
        case 'retrieval_method':
            return PIPELINE_META[pipelineName]?.retrievalMethod || '—';
        case 'retrieval_attempts':
            return pipelineName === 'agentic' ? (result.execution_trace?.length || '—') : '—';
        case 'retrieval_time':
            return formatMs(result.retrieval_time_ms);
        case 'reranking_time':
            return pipelineName === 'hybrid' || pipelineName === 'agentic' ? formatMs(result.reranking_time_ms) : '—';
        case 'generation_time':
            return formatMs(result.generation_time_ms);
        case 'total_latency':
            return formatMs(result.total_time_ms);
        case 'chunks_considered':
            return dash(result.chunks_considered);
        case 'chunks_sent_to_llm':
            return dash(result.chunks_sent_to_llm);
        case 'tokens':
            return formatTokens(result.token_usage);
        case 'citations':
            return result.citations?.length ?? 0;
        case 'query_rewrites':
            return pipelineName === 'agentic'
                ? (result.execution_trace || []).filter((attempt) => attempt.rewritten_query).length
                : '—';
        case 'graph_nodes':
            return pipelineName === 'graph' ? (result.graph_nodes?.length ?? 0) : '—';
        case 'graph_relationships':
            return pipelineName === 'graph' ? (result.relationships?.length ?? 0) : '—';
        default:
            return '—';
    }
};

const ComparisonTable = ({ results }) => {
    if (!results?.length) return null;

    const rows = [
        { key: 'retrieval_method', label: 'Retrieval method' },
        { key: 'retrieval_attempts', label: 'Retrieval attempts' },
        { key: 'retrieval_time', label: 'Retrieval time' },
        { key: 'reranking_time', label: 'Reranking time' },
        { key: 'generation_time', label: 'Generation time' },
        { key: 'total_latency', label: 'Total latency' },
        { key: 'chunks_considered', label: 'Chunks considered' },
        { key: 'chunks_sent_to_llm', label: 'Chunks sent to LLM' },
        { key: 'tokens', label: 'Tokens' },
        { key: 'citations', label: 'Citations' },
        { key: 'query_rewrites', label: 'Query rewrites' },
        { key: 'graph_nodes', label: 'Graph nodes' },
        { key: 'graph_relationships', label: 'Graph relationships' },
    ];

    return (
        <div className="mt-6 overflow-x-auto rounded-md border border-gray-200 bg-white">
            <table className="min-w-full text-left text-sm">
                <thead className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
                    <tr>
                        <th className="px-4 py-3">Metric</th>
                        {results.map((item) => (
                            <th key={item.pipeline} className="px-4 py-3">
                                {PIPELINE_META[item.pipeline]?.title || item.pipeline}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.key} className="border-b border-gray-200">
                            <td className="px-4 py-3 text-gray-500">{row.label}</td>
                            {results.map((item) => (
                                <td key={`${item.pipeline}-${row.key}`} className="px-4 py-3 text-gray-800">
                                    {getComparisonValue(item.pipeline, row.key, item.result)}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export const ComparisonPage = () => {
    const [question, setQuestion] = useState('Explain recursion');
    const [sources, setSources] = useState([]);
    const [selectedSourceIds, setSelectedSourceIds] = useState([]);
    const [comparison, setComparison] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        api.getLectures().then(setSources).catch(console.error);
    }, []);

    const toggleSource = (sourceId) => {
        const id = String(sourceId);
        setSelectedSourceIds((current) => (
            current.includes(id) ? current.filter((value) => value !== id) : [...current, id]
        ));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!question.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const result = await api.comparePipelines({
                question: question.trim(),
                source_ids: selectedSourceIds.length ? selectedSourceIds : null,
                pipelines: PIPELINES,
            });
            setComparison(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="knowledge-shell flex h-full min-h-0 flex-col bg-gray-50 text-gray-900">
            <header className="relative z-10 border-b border-gray-200 bg-white px-6 py-5">
                <div className="mx-auto max-w-7xl">
                    <h1 className="text-2xl font-semibold">RAG Architecture Comparison</h1>
                    <p className="mt-1 max-w-4xl text-sm text-gray-500">
                        Ask one question against the same selected sources and compare Naive, Hybrid, Agentic, and GraphRAG side by side.
                    </p>
                </div>
            </header>

            <main className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col overflow-hidden px-6 py-5">
                <form onSubmit={handleSubmit} className="mb-4 space-y-4">
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-blue-600" />
                            <input
                                value={question}
                                onChange={(event) => setQuestion(event.target.value)}
                                className="h-12 w-full rounded-md border border-gray-300 bg-white pl-12 pr-4 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                                placeholder="Ask a question about your uploaded sources"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={isLoading || !question.trim()}
                            className="inline-flex h-12 items-center gap-2 rounded-md bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                            Compare
                        </button>
                    </div>

                    {sources.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {sources.map((source) => {
                                const id = String(source.id);
                                const selected = selectedSourceIds.includes(id);
                                return (
                                    <button
                                        key={source.id}
                                        type="button"
                                        onClick={() => toggleSource(source.id)}
                                        className={`rounded-full border px-3 py-1 text-xs ${
                                            selected
                                                ? 'border-blue-400 bg-blue-50 text-blue-700'
                                                : 'border-gray-300 text-gray-600 hover:border-gray-400'
                                        }`}
                                    >
                                        {source.title}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </form>

                {error && (
                    <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        {error}
                    </div>
                )}

                <div className="min-h-0 flex-1 overflow-y-auto">
                    {comparison?.results?.length > 0 && (
                        <>
                            <div className="grid rounded-md border border-gray-200 bg-white shadow-sm xl:grid-cols-4 lg:grid-cols-2">
                                {comparison.results.map((item) => (
                                    <PipelineCard key={item.pipeline} pipelineName={item.pipeline} payload={item} />
                                ))}
                            </div>

                            <ComparisonTable results={comparison.results} />

                            <section className="mt-6 rounded-md border border-gray-200 bg-white p-5">
                                <h2 className="mb-4 text-lg font-semibold text-gray-900">Retrieved Evidence</h2>
                                <div className="grid gap-4 xl:grid-cols-4 lg:grid-cols-2">
                                    {comparison.results.map((item) => (
                                        <div key={`evidence-${item.pipeline}`}>
                                            <h3 className="mb-3 text-sm font-medium text-blue-800">
                                                {PIPELINE_META[item.pipeline]?.title || item.pipeline}
                                            </h3>
                                            <div className="space-y-3">
                                                {item.result?.retrieved_chunks?.length ? (
                                                    item.result.retrieved_chunks.map((chunk, index) => (
                                                        <ChunkCard key={`${item.pipeline}-${index}`} chunk={chunk} index={index} />
                                                    ))
                                                ) : (
                                                    <div className="rounded-md border border-dashed border-gray-300 p-4 text-sm text-gray-500">
                                                        No chunks retrieved.
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
};

export default ComparisonPage;
