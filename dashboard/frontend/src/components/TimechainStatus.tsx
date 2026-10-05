import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CardSkeleton } from './LoadingSkeletons';

export function TimechainStatus() {
  const [data, setData] = useState<{ blocks: number; integrity: string; genesis: string; latest_block_hash: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.timechain.status()
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (isLoading) return <CardSkeleton />;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Timechain Status">
      <h2 className="text-xl font-bold mb-4">Timechain Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Total Blocks</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data?.blocks || 0}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Integrity</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            <span className={data?.integrity === 'valid' ? 'text-green-600' : 'text-red-600'}>
              {data?.integrity || 'unknown'}
            </span>
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Genesis</p>
          <p className="text-sm font-mono text-gray-900 mt-1 truncate">{data?.genesis || '—'}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Latest Block</p>
          <p className="text-sm font-mono text-gray-900 truncate">{data?.latest_block_hash || '—'}</p>
        </div>
      </div>
    </section>
  );
}