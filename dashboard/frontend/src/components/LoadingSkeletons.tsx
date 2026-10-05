export function MetricCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-8 bg-gray-200 rounded w-1/2"></div>
      <div className="text-4xl opacity-0">📦</div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="overflow-x-auto animate-pulse">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-24"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-16"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-16"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-20"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-20"></div></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i} className="border-b border-gray-100">
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse space-y-3">
      <div className="h-6 bg-gray-200 rounded w-1/4"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}