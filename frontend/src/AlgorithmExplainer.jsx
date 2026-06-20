import React, { useState } from 'react';
import './App.css';

const AlgorithmExplainer = ({ algo, onStart, onSkip }) => {
    const [slide, setSlide] = useState(0);

    const minimaxSlides = [
        {
            title: "Minimax: The Pessimistic Planner",
            text: "Minimax is the foundation of game AI. It assumes your opponent is perfect and will always make the move that is worst for you.",
            visual: "Imagine a tree where you pick the path to the highest score, but your opponent forced you onto the path to the lowest score at their turn."
        },
        {
            title: "How it works",
            text: "The AI looks ahead several moves. At its turn, it picks the move with the MAX score. At your turn, it assumes you pick the move with the MIN score.",
            visual: "Nodes toggle between MAX (Blue) and MIN (Red) levels."
        },
        {
            title: "The Goal",
            text: "By looking ahead, the AI finds a 'guaranteed' outcome. It doesn't just hope you make a mistake; it plays so that even if you play perfectly, it gets the best possible result.",
            visual: "Result: A solid, stable strategy that is hard to beat."
        }
    ];

    const alphabetaSlides = [
        {
            title: "Alpha-Beta: The Smart Shortcut",
            text: "Standard Minimax is slow because it looks at every single possibility. Alpha-Beta is an optimization that lets the AI skip irrelevant paths.",
            visual: "Think of it like a filtered search. 'If I already found a move that gives me 10 points, why would I look at a branch where I can clearly see my opponent can force me into 2 points?'"
        },
        {
            title: "Pruning (The 'X')",
            text: "When the AI realizes a branch can't possibly be better than what it already found, it stops looking. We call this 'Pruning' the tree.",
            visual: "In the Search Space, you'll see these marked with an 'X'. This saves massive amounts of time!"
        },
        {
            title: "The Efficiency Gain",
            text: "Alpha-Beta gives the same mathematical result as Minimax but can often look twice as deep in the same amount of time.",
            visual: "Deep Search + Speed = Master Level Play."
        }
    ];

    const slides = algo === 'minimax' ? minimaxSlides : alphabetaSlides;
    const currentSlide = slides[slide];

    const nextSlide = () => {
        if (slide < slides.length - 1) {
            setSlide(slide + 1);
        } else {
            onStart();
        }
    };

    return (
        <div className="explainer-overlay">
            <div className="explainer-container">
                <div className="explainer-content">
                    <div className="explainer-badge">{algo === 'minimax' ? 'Strategy Guide' : 'Algorithm Details'}</div>
                    <h2>{currentSlide.title}</h2>
                    <p className="explainer-text">{currentSlide.text}</p>

                    <div className="explainer-visual-box">
                        <div className="visual-caption">Concept Visualization</div>
                        <p>{currentSlide.visual}</p>
                        {/* We can add small CSS animations or SVG here later */}
                    </div>

                    <div className="explainer-nav">
                        <div className="slide-dots">
                            {slides.map((_, i) => (
                                <div key={i} className={`dot ${i === slide ? 'active' : ''}`}></div>
                            ))}
                        </div>
                        <div className="button-group">
                            <button className="control-btn" onClick={onSkip}>Skip Guide</button>
                            <button className="play-button" onClick={nextSlide}>
                                {slide === slides.length - 1 ? 'Start Simulation' : 'Next Step'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AlgorithmExplainer;
