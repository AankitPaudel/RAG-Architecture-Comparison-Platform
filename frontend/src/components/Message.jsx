// src/components/Message.jsx
import React from 'react';
import { ResponsePlayer } from './ResponsePlayer';
import { Bot, User } from 'lucide-react';

export const Message = ({ message, isLatest }) => {
    const isUser = message.sender === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-3 mx-4`}>
            {!isUser && (
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-md border border-blue-200 bg-blue-50 text-blue-600 shadow-sm">
                    <Bot className="h-5 w-5" />
                </div>
            )}

            <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
                <div className={`rounded-md px-4 py-3 shadow-sm ${
                    isUser
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-200 bg-white text-gray-900'
                }`}>
                    <div className="text-sm whitespace-pre-wrap">{message.text}</div>
                </div>

                {message.audioUrl && (
                    <div className="mt-2">
                        <ResponsePlayer audioUrl={message.audioUrl} autoPlay={isLatest} />
                    </div>
                )}

                {!isUser && message.sources?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        {message.mode && (
                            <span className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-emerald-700">
                                {message.mode}
                            </span>
                        )}
                        {message.sources.map((source) => (
                            <span key={source} className="rounded border border-gray-200 bg-gray-50 px-2 py-1 text-gray-600">
                                {source}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {isUser && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-gray-200">
                    <User className="h-5 w-5 text-gray-600" />
                </div>
            )}
        </div>
    );
};

export default Message;
