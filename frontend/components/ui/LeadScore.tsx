import { Progress } from "./Progress";
import Badge from "./Badge";
import clsx from "clsx";

interface LeadScoreProps {
  score: number;
  maxScore?: number;
  showDetails?: boolean;
  breakdown?: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  size?: 'sm' | 'md' | 'lg';
}

export default function LeadScore({
  score,
  maxScore = 100,
  showDetails = false,
  breakdown,
  size = 'md'
}: LeadScoreProps) {
  const percentage = Math.min((score / maxScore) * 100, 100);
  
  const getScoreColor = () => {
    if (percentage >= 80) return 'success';
    if (percentage >= 60) return 'warning';
    if (percentage >= 40) return 'texas';
    return 'danger';
  };

  const getScoreLabel = () => {
    if (percentage >= 80) return 'Hot Lead';
    if (percentage >= 60) return 'Warm';
    if (percentage >= 40) return 'Potential';
    return 'Cold';
  };

  return (
    <div className={clsx(
      "space-y-2",
      size === 'sm' && "text-sm",
      size === 'lg' && "text-lg"
    )}>
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-700">Lead Score</span>
        <Badge variant="score" size={size}>
          {Math.round(score)}/{maxScore}
        </Badge>
      </div>
      
      <Progress 
        value={percentage} 
        className={clsx(
          size === 'sm' && "h-2",
          size === 'md' && "h-3",
          size === 'lg' && "h-4"
        )}
        color={getScoreColor()}
      />
      
      <div className="flex items-center justify-between text-sm">
        <Badge variant={getScoreColor()} size="sm">
          {getScoreLabel()}
        </Badge>
        <span className="text-gray-500">{Math.round(percentage)}%</span>
      </div>

      {showDetails && breakdown && (
        <div className="mt-4 space-y-2 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
            Score Breakdown
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span>Recency:</span>
              <span className="font-medium">{breakdown.recency}/25</span>
            </div>
            <div className="flex justify-between">
              <span>Residential:</span>
              <span className="font-medium">{breakdown.residential}/20</span>
            </div>
            <div className="flex justify-between">
              <span>Value:</span>
              <span className="font-medium">{breakdown.value}/25</span>
            </div>
            <div className="flex justify-between">
              <span>Work Class:</span>
              <span className="font-medium">{breakdown.workClass}/18</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}