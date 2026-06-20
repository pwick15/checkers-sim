import React, { useState, useEffect } from 'react';
import './App.css';

const OnboardingTour = ({ active, onComplete }) => {
    const [step, setStep] = useState(0);

    const steps = [
        {
            target: '#board-area',
            title: 'The Battlefield',
            content: 'This is where the magic happens. You play as Red, and the AI plays as Black. Standard checkers rules apply!',
            position: 'right'
        },
        {
            target: '.top-moves-list',
            title: 'AI Candidates',
            content: 'When the AI thinks, it evaluates many paths. The top 3 most promising moves are shown here with their calculated scores.',
            position: 'left'
        },
        {
            target: '.grid-container',
            title: 'The Search Space',
            content: 'This visualization shows every single board state the AI explored. Hover over dots to see specific evaluations, or click to see why a path was pruned.',
            position: 'left'
        },
        {
            target: '.speed-dropdown',
            title: 'Control Time',
            content: 'Adjust the simulation speed here. 1x for careful study, 10x for a quick summary of the AI\'s logic.',
            position: 'bottom'
        },
        {
            target: '.status-bar',
            title: 'Pro Tip',
            content: 'Keep an eye on the status bar at the bottom for real-time educational insights into the AI\'s current sub-task.',
            position: 'top'
        }
    ];

    const [bubbleStyle, setBubbleStyle] = useState({});

    useEffect(() => {
        if (active) {
            const el = document.querySelector(steps[step].target);
            if (el) {
                const rect = el.getBoundingClientRect();
                const pos = steps[step].position;
                let style = {};

                if (pos === 'right') {
                    style = { top: rect.top + rect.height / 2, left: rect.right + 20, transform: 'translateY(-50%)' };
                } else if (pos === 'left') {
                    style = { top: rect.top + rect.height / 2, left: rect.left - 300, transform: 'translateY(-50%)' };
                } else if (pos === 'bottom') {
                    style = { top: rect.bottom + 20, left: rect.left + rect.width / 2, transform: 'translateX(-50%)' };
                } else if (pos === 'top') {
                    style = { top: rect.top - 200, left: rect.left + rect.width / 2, transform: 'translateX(-50%)' };
                }
                setBubbleStyle(style);
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }, [step, active]);

    if (!active) return null;

    const currentStep = steps[step];

    const handleNext = () => {
        if (step < steps.length - 1) {
            setStep(step + 1);
        } else {
            onComplete();
        }
    };

    const handleSkip = () => onComplete();

    return (
        <div className="tour-overlay">
            <div className="tour-bubble" style={bubbleStyle}>
                <div className="tour-step-counter">{step + 1} / {steps.length}</div>
                <h3>{currentStep.title}</h3>
                <p>{currentStep.content}</p>
                <div className="tour-actions">
                    <button className="control-btn small" onClick={handleSkip}>Skip Tour</button>
                    <button className="play-button small" onClick={handleNext}>
                        {step === steps.length - 1 ? 'Finish' : 'Next →'}
                    </button>
                </div>
            </div>
            <div className="tour-highlight" style={getHighlightStyle(currentStep.target)}></div>
        </div>
    );
};

// Helper to determine highlight position
function getHighlightStyle(selector) {
    const el = document.querySelector(selector);
    if (!el) return { display: 'none' };
    const rect = el.getBoundingClientRect();
    return {
        top: rect.top - 8,
        left: rect.left - 8,
        width: rect.width + 16,
        height: rect.height + 16,
        boxShadow: '0 0 0 9999px rgba(0,0,0,0.7), 0 0 15px var(--accent-gold)',
        borderRadius: '8px'
    };
}

export default OnboardingTour;
