import React, { useState, useEffect } from 'react';

interface LeadFeedbackButtonsProps {
  leadId: number;
  initialVote?: 'up' | 'down';
}

interface FeedbackState {
  vote_type: 'up' | 'down' | null;
  can_change: boolean;
  feedback_date: string | null;
}

export default function LeadFeedbackButtons({ leadId, initialVote }: LeadFeedbackButtonsProps) {
  const [feedbackState, setFeedbackState] = useState<FeedbackState>({
    vote_type: initialVote || null,
    can_change: true,
    feedback_date: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentVote();
  }, [leadId]);

  const fetchCurrentVote = async () => {
    try {
      // In a real app, you'd get the auth token from your auth system
      // For now, we'll assume it's available via a global auth context
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`/api/leads/${String(leadId)}/feedback`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFeedbackState(data);
      }
    } catch (err) {
      console.error('Failed to fetch current vote:', err);
    }
  };

  const handleVote = async (voteType: 'up' | 'down') => {
    if (loading) return;
    
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Please log in to vote');
        setLoading(false);
        return;
      }

      // Optimistic update
      const previousState = feedbackState;
      setFeedbackState({
        vote_type: voteType,
        can_change: true,
        feedback_date: new Date().toISOString()
      });

      const response = await fetch(`/api/leads/${String(leadId)}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ vote_type: voteType }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Revert optimistic update on error
        setFeedbackState(previousState);
        
        if (response.status === 403 && data.error?.includes('24 hours')) {
          setError('Cannot change vote after 24 hours');
        } else {
          setError(data.error || 'Failed to submit vote');
        }
      } else {
        // Update with server response
        setFeedbackState({
          vote_type: data.vote_type,
          can_change: data.can_change,
          feedback_date: data.data?.updated_at || new Date().toISOString()
        });
      }
    } catch (err) {
      console.error('Vote submission error:', err);
      setError('Network error. Please try again.');
      // Revert optimistic update
      await fetchCurrentVote();
    } finally {
      setLoading(false);
    }
  };

  const handleChangeVote = () => {
    setError(null);
    // Allow voting again
    setFeedbackState(prev => ({
      ...prev,
      can_change: true
    }));
  };

  // Helper function to get auth token - this would be implemented based on your auth system
  const getAuthToken = (): string | null => {
    // This is a placeholder - in a real app you'd get this from your auth context/provider
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token') || null;
    }
    return null;
  };

  const isSelected = (type: 'up' | 'down') => feedbackState.vote_type === type;
  const isDisabled = loading || (!feedbackState.can_change && feedbackState.vote_type !== null);

  return (
    <div className="flex items-center space-x-2">
      {/* Thumbs Up Button */}
      <button
        onClick={() => handleVote('up')}
        disabled={isDisabled && !isSelected('up')}
        className={`
          flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-200
          ${isSelected('up')
            ? 'bg-green-500 border-green-500 text-white shadow-md' 
            : 'border-gray-300 text-gray-500 hover:border-green-400 hover:text-green-500'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${isDisabled && !isSelected('up') ? 'opacity-30 cursor-not-allowed' : ''}
        `}
        title={isSelected('up') ? 'You voted this up' : 'Vote this lead up'}
      >
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <path d="M7 10l5-5 5 5M7 14l5-5 5 5" />
        </svg>
      </button>

      {/* Thumbs Down Button */}
      <button
        onClick={() => handleVote('down')}
        disabled={isDisabled && !isSelected('down')}
        className={`
          flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-200
          ${isSelected('down')
            ? 'bg-red-500 border-red-500 text-white shadow-md' 
            : 'border-gray-300 text-gray-500 hover:border-red-400 hover:text-red-500'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${isDisabled && !isSelected('down') ? 'opacity-30 cursor-not-allowed' : ''}
        `}
        title={isSelected('down') ? 'You voted this down' : 'Vote this lead down'}
      >
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <path d="M17 14l-5 5-5-5M17 10l-5 5-5-5" />
        </svg>
      </button>

      {/* Change link for votes older than allowed time */}
      {feedbackState.vote_type && !feedbackState.can_change && (
        <button
          onClick={handleChangeVote}
          className="text-xs text-blue-500 hover:text-blue-700 underline ml-2"
        >
          Change
        </button>
      )}

      {/* Loading indicator */}
      {loading && (
        <div className="text-xs text-gray-500">
          Saving...
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="text-xs text-red-500 max-w-xs">
          {error}
        </div>
      )}
    </div>
  );
}