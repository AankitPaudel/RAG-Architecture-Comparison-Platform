// File: frontend/src/hooks/useAudio.js
import { useState, useCallback } from 'react';
import { audioService } from '../services/audioService';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [error, setError] = useState(null);

    const playAudio = useCallback(async (audioUrl) => {
        try {
            setError(null);
            setIsPlaying(true);
            const audio = await audioService.playAudio(audioUrl);
            
            audio.onended = () => {
                setIsPlaying(false);
            };
        } catch (err) {
            setError(err.message);
            setIsPlaying(false);
        }
    }, []);

    return { isPlaying, error, playAudio };
};