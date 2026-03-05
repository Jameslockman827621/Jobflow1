interface JobCardProps {
  id: number;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  hybrid?: boolean;
  min_salary?: number;
  max_salary?: number;
  seniority?: string;
  match_score?: number;
  external_url: string;
  posted_date?: string;
  onApply?: (jobId: number) => void;
}

export default function JobCard({
  id,
  title,
  company,
  location,
  remote,
  hybrid,
  min_salary,
  max_salary,
  seniority,
  match_score,
  external_url,
  posted_date,
  onApply,
}: JobCardProps) {
  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return null;
    const format = (n: number) => `$${(n / 1000).toFixed(0)}k`;
    if (min && max) return `${format(min)} - ${format(max)}`;
    if (min) return `From ${format(min)}`;
    if (max) return `Up to ${format(max)}`;
    return null;
  };

  const getMatchColor = (score?: number) => {
    if (!score) return "bg-gray-100 text-gray-800";
    if (score >= 80) return "bg-green-100 text-green-800";
    if (score >= 60) return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  };

  const getMatchLabel = (score?: number) => {
    if (!score) return "";
    if (score >= 80) return "Excellent Match";
    if (score >= 60) return "Good Match";
    return "Weak Match";
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {match_score !== undefined && (
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getMatchColor(match_score)}`}>
                {match_score}% match
              </span>
            )}
          </div>
          
          <p className="text-gray-600 font-medium mb-3">{company}</p>
          
          <div className="flex flex-wrap gap-2 text-sm text-gray-500 mb-4">
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {location}
            </span>
            
            {remote && (
              <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium">
                Remote
              </span>
            )}
            
            {hybrid && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                Hybrid
              </span>
            )}
            
            {seniority && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs font-medium capitalize">
                {seniority}
              </span>
            )}
            
            {formatSalary(min_salary, max_salary) && (
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {formatSalary(min_salary, max_salary)}
              </span>
            )}
          </div>
          
          {posted_date && (
            <p className="text-xs text-gray-400">
              Posted {new Date(posted_date).toLocaleDateString()}
            </p>
          )}
        </div>
        
        <div className="flex flex-col gap-2 ml-4">
          <a
            href={external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-center"
          >
            View Job
          </a>
          {onApply && (
            <button
              onClick={() => onApply(id)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Apply Now
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
