import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';

const STEPS = [
  { 
    id: 'welcome', 
    title: 'Welcome to Abraxas', 
    content: 'Welcome to the Abraxas Dashboard - your real-time symbolic intelligence platform for multi-domain cascade prediction. Abraxas combines oracle pipelines, phase detection, and ritual systems to provide predictive intelligence across domains.'
  },
  { 
    id: 'metrics', 
    title: 'System Overview', 
    content: 'The top metric cards show live system health at a glance: Total Artifacts, Oracle Runs (24h), Active Alignments, Rituals (24h), Timechain Blocks.'
  },
  { 
    id: 'alignments', 
    title: 'Phase Alignment Timeline', 
    content: 'The Phase Alignment Timeline shows when multiple domains enter the same lifecycle phase simultaneously. Click any alignment to see detailed token breakdown.'
  },
  { 
    id: 'weather', 
    title: 'Memetic Weather (Synchronicity Map)', 
    content: 'The Synchronicity Map shows predictive coupling between domains - when domain X enters a phase, domain Y follows after a lag. High-confidence patterns enable early warning of phase transitions.'
  },
  { 
    id: 'narratives', 
    title: 'Resonance Narratives', 
    content: 'Resonance Narratives provide human-readable summaries of oracle outputs with evidence gating and constraint tracking. Narratives include provenance footprints for full traceability.'
  },
];

interface OnboardingFlowProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

export function OnboardingFlow({ isOpen, onClose, onComplete }: OnboardingFlowProps) {
  const [step, setStep] = useState(0);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  if (!isOpen) return null;

  const isLast = step === 4;

  const handleNext = () => {
    if (step === 4) {
      onComplete();
    } else {
      setStep(s => s + 1);
    }
  };

  const handleBack = () => {
    setStep(s => s - 1);
  };

  const handleClose = () => {
    if (dontShowAgain) {
      localStorage.setItem('onboarding_completed', 'true');
    }
    onClose();
  };

  return createPortal(
    React.createElement('div', { className: 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in' },
      React.createElement('div', { className: 'bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-md w-full p-6 animate-slide-up' },
        React.createElement('div', { className: 'flex justify-between items-center mb-4' },
          React.createElement('h2', { className: 'text-xl font-bold text-gray-900 dark:text-gray-100' }, 'Abraxas Onboarding'),
          React.createElement('button', { 
            onClick: handleClose, 
            className: 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors',
            'aria-label': 'Close onboarding'
          }, '✕')
        ),
        React.createElement('div', { className: 'mb-6' },
          React.createElement('div', { className: 'flex justify-center gap-1 mb-4' },
            [0,1,2,3,4].map((_, i) => 
              React.createElement('div', { 
                key: i, 
                className: 'w-2 h-2 rounded-full transition-colors ' + (i === step ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600')
              })
            ))
        ),
        React.createElement('h3', { className: 'text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2' }, STEPS[step].title),
        React.createElement('div', { className: 'prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300' },
          React.createElement('p', null, STEPS[step].content)
        ),
        React.createElement('div', { className: 'flex justify-between' },
          step > 0 && React.createElement('button', { 
            onClick: () => setStep(s => s - 1),
            className: 'px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors'
          }, 'Back'),
          React.createElement('div', { className: 'flex items-center space-x-2' },
            React.createElement('label', { className: 'flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400' },
              React.createElement('input', {
                type: 'checkbox',
                checked: dontShowAgain,
                onChange: (e: React.ChangeEvent<HTMLInputElement>) => setDontShowAgain(e.target.checked),
                className: 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
              }),
              React.createElement('span', { className: 'text-gray-600 dark:text-gray-400' }, 'Don't show again')
            )
          ),
          React.createElement('button', { 
            onClick: () => {
              if (step === 4) {
                onComplete();
              } else {
                setStep(s => s + 1);
              }
            },
            className: 'px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium'
          }, isLast ? 'Get Started' : 'Next')
        ),
        React.createElement('div', { className: 'flex justify-center mt-4 gap-1' },
          [0,1,2,3,4].map((_, i) => 
            React.createElement('div', { 
              key: i, 
              className: 'w-2 h-2 rounded-full transition-colors ' + (i === step ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600')
            })
          ))
        )
      ),
      document.body
    );
  }
}

function OnboardingWrapper() {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem('onboarding_completed');
    if (!completed) {
      const timer = setTimeout(() => setShowOnboarding(true), 500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleComplete = () => {
    localStorage.setItem('onboarding_completed', 'true');
    setShowOnboarding(false);
  };

  const handleClose = () => {
    setShowOnboarding(false);
  };

  if (!showOnboarding) return null;

  return React.createElement(OnboardingFlow, { isOpen: true, onClose: handleClose, onComplete: handleComplete });
}

export function OnboardingWrapper() {
  return React.createElement(OnboardingWrapper);
}
