// File: frontend/src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
    async sendQuestion(question, allowFallback = false) {
        try {
            const response = await fetch(`${API_BASE_URL}/qa/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question, allow_fallback: allowFallback }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error sending question:', error);
            throw error;
        }
    },

    async comparePipelines({ question, source_ids = null, pipelines = ['naive', 'hybrid', 'agentic', 'graph'] }) {
        try {
            const response = await fetch(`${API_BASE_URL}/compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question, source_ids, pipelines }),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error comparing pipelines:', error);
            throw error;
        }
    },

    async queryPipeline({ question, pipeline = 'naive', source_ids = null, allow_fallback = false }) {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question,
                pipeline,
                source_ids,
                allow_fallback,
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    },

    async sendAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');

            const response = await fetch(`${API_BASE_URL}/audio/speech-to-text`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error sending audio:', error);
            throw error;
        }
    },

    async getAudioResponse(text) {
        try {
            const response = await fetch(`${API_BASE_URL}/audio/text-to-speech`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            console.error('Error getting audio response:', error);
            throw error;
        }
    },

    async cleanupAudio() {
        try {
            const response = await fetch(`${API_BASE_URL}/audio/cleanup`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error cleaning up audio:', error);
            throw error;
        }
    },

    async getLectures() {
        const response = await fetch(`${API_BASE_URL}/lectures/?limit=100`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    },

    async addLecture({ title, content }) {
        const response = await fetch(`${API_BASE_URL}/lectures/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, content }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    },

    async addYouTubeSource({ url, title }) {
        const response = await fetch(`${API_BASE_URL}/lectures/youtube`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, title }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    },

    async deleteLecture(id) {
        const response = await fetch(`${API_BASE_URL}/lectures/${id}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    },

    async runEvaluation(pipelines = ['naive', 'hybrid', 'agentic', 'graph']) {
        const response = await fetch(`${API_BASE_URL}/evaluation/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pipelines }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    },

};
