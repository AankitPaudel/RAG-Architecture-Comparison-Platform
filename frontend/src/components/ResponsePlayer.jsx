// File: frontend/src/components/ResponsePlayer.jsx
import React, { useState, useRef, useEffect } from 'react';

export const ResponsePlayer = ({ audioUrl, autoPlay = false, onComplete, onTranscriptionEnd }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [hasAutoPlayed, setHasAutoPlayed] = useState(false);  // Track first auto-play
    const audioRef = useRef(null);

    // Auto-play when the audio URL changes (first time only)
    useEffect(() => {
        if (audioUrl && autoPlay && audioRef.current && !hasAutoPlayed) {
            setLoading(true);
            audioRef.current.play()
                .then(() => {
                    setLoading(false);
                    setError(null);
                    setIsPlaying(true);
                    setHasAutoPlayed(true); // Ensure only first auto-play happens
                    if (onTranscriptionEnd) onTranscriptionEnd(); // Clear transcribing
                })
                .catch(err => {
                    console.error('Auto-play error:', err);
                    setError('Failed to auto-play audio');
                    setLoading(false);
                });
        }
    }, [audioUrl, autoPlay, hasAutoPlayed, onTranscriptionEnd]);

    // Reset transcribing state after audio ends
    const handleAudioEnded = () => {
        setIsPlaying(false);
        if (onComplete) onComplete();  // Notify parent that playback is complete
    };

    // Toggle play/pause
    const togglePlay = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                setLoading(true);
                audioRef.current.play()
                    .then(() => {
                        setLoading(false);
                        setError(null);
                        setIsPlaying(true);
                    })
                    .catch(err => {
                        console.error('Play error:', err);
                        setError('Failed to play audio');
                        setLoading(false);
                    });
            }
        }
    };

    return (
        <div className="audio-player">
            {error && <div className="error-message text-red-500">{error}</div>}

            <audio
                ref={audioRef}
                src={audioUrl}
                preload="metadata"
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onEnded={handleAudioEnded}
                onError={() => setError('Error loading audio')}
                onLoadedData={() => {
                    setLoading(false);
                    if (onTranscriptionEnd) onTranscriptionEnd();  // Clear transcribing after loading
                }}
            />

            <button
                onClick={togglePlay}
                disabled={!audioUrl || loading}
                className={`px-4 py-2 rounded-md ${isPlaying ? 'bg-red-500' : 'bg-blue-500'} text-white`}
            >
                {loading ? 'Loading...' : isPlaying ? 'Pause' : 'Play Response'}
            </button>
        </div>
    );
};

export default ResponsePlayer;
