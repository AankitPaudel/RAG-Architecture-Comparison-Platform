// frontend/src/components/LoadingIndicator.jsx
import React from 'react';

export const LoadingIndicator = () => {
    return (
        <div className="loading-container">
            <div className="loading-content">
                <div className="loading-brain">
                    {/* Brain thinking animation */}
                    <div className="brain-waves">
                        <div className="wave"></div>
                        <div className="wave"></div>
                        <div className="wave"></div>
                    </div>
                </div>
                <div className="loading-text">
                    <span>T</span>
                    <span>h</span>
                    <span>i</span>
                    <span>n</span>
                    <span>k</span>
                    <span>i</span>
                    <span>n</span>
                    <span>g</span>
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                </div>
            </div>
        </div>
    );
};