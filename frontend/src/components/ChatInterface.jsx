import React, { useState, useRef, useEffect } from 'react';
import { Send, Network, Database, BrainCircuit, Sparkles, ShieldCheck } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import { AudioRecorder } from './AudioRecorder';
import { MessageList } from './MessageList';
import { TranscriptBubble } from './TranscriptBubble';

export const ChatInterface = () => {
    const { messages, sendMessage, isLoading, error, allowFallback, setAllowFallback } = useChat();
    const [inputText, setInputText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const chatContainerRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages, transcript]);

    const handleTextSubmit = async (event) => {
        event.preventDefault();
        if (inputText.trim()) {
            await sendMessage({ type: 'text', content: inputText });
            setInputText('');
        }
    };

    const handleInputKeyDown = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleTextSubmit(event);
        }
    };

    const handleAudioSubmit = async (audioBlob, finalTranscript) => {
        setIsRecording(false);
        await sendMessage({ type: 'audio', content: audioBlob, transcript: finalTranscript });
        setTranscript('');
    };

    return (
        <div className="knowledge-shell flex h-full min-h-0 bg-gray-50 text-gray-900">
            <aside className="relative z-10 hidden w-80 flex-col border-r border-gray-200 bg-white md:flex">
                <div className="flex h-full flex-col justify-between">
                    <div>
                        <div className="border-b border-gray-200 p-6">
                            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-md border border-blue-200 bg-blue-50 text-blue-600">
                                <Network className="h-6 w-6" />
                            </div>
                            <h1 className="text-2xl font-semibold text-gray-900">Knowledge RAG</h1>
                            <p className="mt-2 text-sm leading-6 text-gray-600">
                                Search uploaded learning content, retrieve the strongest context, and generate grounded answers.
                            </p>
                        </div>

                        <div className="p-6">
                            <div className="knowledge-panel h-48 rounded-md border border-gray-200 bg-white p-5">
                                <div className="relative h-full">
                                    <span className="graph-node graph-node-a" />
                                    <span className="graph-node graph-node-b" />
                                    <span className="graph-node graph-node-c" />
                                    <span className="graph-node graph-node-d" />
                                    <span className="graph-line graph-line-1" />
                                    <span className="graph-line graph-line-2" />
                                    <span className="graph-line graph-line-3" />
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3 px-6">
                            <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                                <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                                    <Database className="h-4 w-4 text-blue-600" />
                                    Vector knowledge store
                                </div>
                                <p className="mt-2 text-xs leading-5 text-gray-600">Semantic chunks are retrieved before GPT answers.</p>
                            </div>
                            <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                                <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                                    <BrainCircuit className="h-4 w-4 text-emerald-600" />
                                    GPT fallback
                                </div>
                                <p className="mt-2 text-xs leading-5 text-gray-600">When no match exists, the response is labeled as fallback.</p>
                            </div>
                            <label className="flex cursor-pointer items-center justify-between rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                                <div>
                                    <div className="flex items-center gap-3 text-sm font-medium text-gray-900">
                                        <ShieldCheck className="h-4 w-4 text-blue-600" />
                                        Hybrid fallback
                                    </div>
                                    <p className="mt-2 text-xs leading-5 text-gray-600">Off means answers must come from your sources only.</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={allowFallback}
                                    onChange={(event) => setAllowFallback(event.target.checked)}
                                    className="h-5 w-5 accent-blue-600"
                                />
                            </label>
                        </div>
                    </div>
                </div>
            </aside>

            <section className="relative z-10 flex min-w-0 flex-1 flex-col">
                <div ref={chatContainerRef} className="relative flex-1 overflow-y-auto p-6">
                    <div className="mx-auto mb-5 flex max-w-4xl items-center gap-3 rounded-md border border-gray-200 bg-white px-4 py-3 shadow-sm">
                        <Sparkles className="h-5 w-5 text-blue-600" />
                        <div>
                            <p className="text-sm font-medium text-gray-900">Knowledge graph assistant</p>
                            <p className="text-xs text-gray-600">
                                {allowFallback
                                    ? 'Hybrid mode: source search first, external GPT fallback if no match is found.'
                                    : 'Strict mode: answers only from indexed sources.'}
                            </p>
                        </div>
                    </div>
                    <MessageList messages={messages} />
                    {transcript && <TranscriptBubble transcript={transcript} />}
                </div>

                {error && (
                    <div className="mx-auto mb-3 w-full max-w-4xl px-4">
                        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                            {error}
                        </div>
                    </div>
                )}

                <div className="relative z-10 border-t border-gray-200 bg-white p-4">
                    <div className="mx-auto max-w-4xl">
                        <form onSubmit={handleTextSubmit} className="flex items-end gap-4">
                            <textarea
                                ref={inputRef}
                                value={inputText}
                                onChange={(event) => setInputText(event.target.value)}
                                onKeyDown={handleInputKeyDown}
                                placeholder="Ask a question about the lecture content..."
                                rows="1"
                                disabled={isRecording}
                                className="min-h-[60px] max-h-[200px] flex-1 resize-none rounded-md border border-gray-300 bg-white p-4 text-base text-gray-900 outline-none placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:opacity-50"
                            />
                            <div className="flex items-center gap-2">
                                <AudioRecorder
                                    onTranscriptUpdate={setTranscript}
                                    onRecordingComplete={handleAudioSubmit}
                                    onRecordingStart={() => setIsRecording(true)}
                                    silenceThreshold={3000}
                                />
                                <button
                                    type="submit"
                                    disabled={isLoading || isRecording || !inputText.trim()}
                                    className="rounded-md bg-blue-600 p-3 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                                    aria-label="Send message"
                                >
                                    <Send className="h-5 w-5" />
                                </button>
                            </div>
                        </form>
                        <p className="mt-2 text-center text-xs text-gray-500">
                            {isRecording ? 'Listening... auto-stops on silence' : 'Press Enter to send message'}
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default ChatInterface;
