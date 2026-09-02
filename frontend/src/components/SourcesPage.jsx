import React, { useEffect, useState } from 'react';
import { Database, FileText, Link, Loader2, Plus, Trash2 } from 'lucide-react';
import { api } from '../services/api';

export const SourcesPage = () => {
    const [sources, setSources] = useState([]);
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [youtubeTitle, setYoutubeTitle] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadSources = async () => {
        setError(null);
        try {
            const data = await api.getLectures();
            setSources(data);
        } catch (err) {
            setError(err.message);
        }
    };

    useEffect(() => { loadSources(); }, []);

    const addTextSource = async (event) => {
        event.preventDefault();
        if (!title.trim() || !content.trim()) return;
        setIsLoading(true);
        setError(null);
        try {
            await api.addLecture({ title: title.trim(), content: content.trim() });
            setTitle('');
            setContent('');
            await loadSources();
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const addYouTubeSource = async (event) => {
        event.preventDefault();
        if (!youtubeUrl.trim()) return;
        setIsLoading(true);
        setError(null);
        try {
            await api.addYouTubeSource({ url: youtubeUrl.trim(), title: youtubeTitle.trim() || undefined });
            setYoutubeUrl('');
            setYoutubeTitle('');
            await loadSources();
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const deleteSource = async (id) => {
        setIsLoading(true);
        setError(null);
        try {
            await api.deleteLecture(id);
            await loadSources();
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const inputClass = "h-11 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

    return (
        <div className="knowledge-shell flex h-full min-h-0 flex-col bg-gray-50 text-gray-900">
            <main className="relative z-10 mx-auto grid w-full max-w-6xl flex-1 gap-5 overflow-y-auto px-6 py-6 lg:grid-cols-[420px_1fr]">
                <section className="space-y-5">
                    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                        <div className="mb-4 flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-blue-200 bg-blue-50 text-blue-600">
                                <FileText className="h-5 w-5" />
                            </div>
                            <div>
                                <h1 className="text-lg font-semibold">Add text source</h1>
                                <p className="text-sm text-gray-600">Paste lecture notes, cleaned transcripts, or study material.</p>
                            </div>
                        </div>
                        <form onSubmit={addTextSource} className="space-y-3">
                            <input value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} placeholder="Source title" />
                            <textarea value={content} onChange={(e) => setContent(e.target.value)} className={`${inputClass} min-h-40 resize-y py-3`} placeholder="Paste source text here" />
                            <button type="submit" disabled={isLoading || !title.trim() || !content.trim()} className="inline-flex h-11 items-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                                Add source
                            </button>
                        </form>
                    </div>

                    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                        <div className="mb-4 flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 text-emerald-600">
                                <Link className="h-5 w-5" />
                            </div>
                            <div>
                                <h2 className="text-lg font-semibold">Add YouTube transcript</h2>
                                <p className="text-sm text-gray-600">Video captions are converted into indexed RAG knowledge.</p>
                            </div>
                        </div>
                        <form onSubmit={addYouTubeSource} className="space-y-3">
                            <input value={youtubeUrl} onChange={(e) => setYoutubeUrl(e.target.value)} className={inputClass} placeholder="YouTube video URL" />
                            <input value={youtubeTitle} onChange={(e) => setYoutubeTitle(e.target.value)} className={inputClass} placeholder="Optional title" />
                            <button type="submit" disabled={isLoading || !youtubeUrl.trim()} className="inline-flex h-11 items-center gap-2 rounded-md bg-emerald-600 px-4 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50">
                                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                                Import transcript
                            </button>
                        </form>
                    </div>
                </section>

                <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                    <div className="mb-4 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-blue-200 bg-blue-50 text-blue-600">
                                <Database className="h-5 w-5" />
                            </div>
                            <div>
                                <h2 className="text-lg font-semibold">Indexed sources</h2>
                                <p className="text-sm text-gray-600">These records are used for RAG answers.</p>
                            </div>
                        </div>
                        <button onClick={loadSources} className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                            Refresh
                        </button>
                    </div>

                    {error && (
                        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
                    )}

                    <div className="space-y-3">
                        {sources.length ? sources.map((source) => (
                            <article key={source.id} className="rounded-md border border-gray-200 bg-gray-50 p-4">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <h3 className="font-medium text-gray-900">{source.title}</h3>
                                        <p className="mt-1 text-xs text-gray-500">ID {source.id}</p>
                                    </div>
                                    <button onClick={() => deleteSource(source.id)} disabled={isLoading} className="rounded-md p-2 text-gray-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-50" aria-label="Delete source">
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                                <p className="mt-3 line-clamp-3 text-sm leading-6 text-gray-600">{source.content}</p>
                            </article>
                        )) : (
                            <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-gray-500">No sources indexed yet.</div>
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
};

export default SourcesPage;
