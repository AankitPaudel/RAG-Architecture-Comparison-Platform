import React from 'react';
import { BookOpen, Mic, Search } from 'lucide-react';
import { Message } from './Message';

export const MessageList = ({ messages }) => {
    if (messages.length === 0) {
        return (
            <div className="flex min-h-[420px] items-center justify-center p-8">
                <div className="w-full max-w-2xl rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h2 className="text-center text-2xl font-semibold text-gray-900">
                        Ask your knowledge base
                    </h2>
                    <p className="mx-auto mt-3 max-w-xl text-center text-sm leading-6 text-gray-600">
                        Questions are matched against stored content first, then the answer is generated from the retrieved context.
                    </p>
                    <div className="mt-6 grid gap-3 md:grid-cols-3">
                        <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                            <BookOpen className="mb-3 h-5 w-5 text-blue-600" />
                            <h3 className="text-sm font-semibold text-gray-900">Source grounded</h3>
                            <p className="mt-2 text-xs leading-5 text-gray-600">Answers are based on indexed material.</p>
                        </div>
                        <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                            <Search className="mb-3 h-5 w-5 text-emerald-600" />
                            <h3 className="text-sm font-semibold text-gray-900">Source retrieval</h3>
                            <p className="mt-2 text-xs leading-5 text-gray-600">The backend retrieves relevant chunks before answering.</p>
                        </div>
                        <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                            <Mic className="mb-3 h-5 w-5 text-violet-600" />
                            <h3 className="text-sm font-semibold text-gray-900">Voice support</h3>
                            <p className="mt-2 text-xs leading-5 text-gray-600">Ask with your microphone and listen to responses.</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 p-4">
            {messages.map((message, index) => (
                <Message key={index} message={message} isLatest={index === messages.length - 1} />
            ))}
        </div>
    );
};

export default MessageList;
