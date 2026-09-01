// src/components/TranscriptBubble.jsx
import React from 'react';

export const TranscriptBubble = ({ transcript }) => {
    if (!transcript) return null;

    return (
        <div className="px-4 py-2 mb-4">
            <div className="flex justify-end">
                <div className="bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100 rounded-2xl px-4 py-2 max-w-[80%] shadow-sm">
                    <div className="text-xs text-blue-600 dark:text-blue-300 mb-1">
                        Transcribing...
                    </div>
                    <div className="text-sm">
                        {transcript}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TranscriptBubble;