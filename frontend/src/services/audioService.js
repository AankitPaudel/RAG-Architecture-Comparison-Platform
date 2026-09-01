// File: frontend/src/services/audioService.js
export const audioService = {
    async createAudioElement(audioUrl) {
        return new Promise((resolve, reject) => {
            const audio = new Audio(audioUrl);
            audio.oncanplaythrough = () => resolve(audio);
            audio.onerror = reject;
            audio.load();
        });
    },

    async playAudio(audioUrl) {
        try {
            const audio = await this.createAudioElement(audioUrl);
            await audio.play();
            return audio;
        } catch (error) {
            console.error('Error playing audio:', error);
            throw error;
        }
    },
};
