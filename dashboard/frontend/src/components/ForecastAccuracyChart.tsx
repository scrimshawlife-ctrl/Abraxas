import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function ForecastAccuracyChart() {
  
  // Mock forecast accuracy data for demo
  const chartData = [
    { horizon: '1h', accuracy: 0.89 },
    { horizon: '6h', accuracy: 0.85 },
    { horizon: '12h', accuracy: 0.81 },
    { horizon: '24h', accuracy: 0.76 },
    { horizon: '48h', accuracy: 0.70 },
    { horizon: '72h', accuracy: 0.64 },
  ];
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Forecast Accuracy">
      <h2 className="text-xl font-bold mb-4">Forecast Accuracy (Horizon Bands)</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="horizon" stroke="#9ca3af" />
            <YAxis 
              stroke="#9ca3af" 
              domain={[0.5, 1]} 
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} 
            />
            <Tooltip 
              formatter={(value: number) => [(value * 100).toFixed(1) + '%', 'Accuracy']} 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Line 
              type="monotone" 
              dataKey="accuracy" 
              stroke="#3b82f6" 
              strokeWidth={2} 
              dot={{ r: 4, fill: '#3b82f6' }}
              activeDot={{ r: 6, fill: '#3b82f6' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center">
        Accuracy by forecast horizon • Based on last 30 oracle runs
      </p>
    </section>
  );
}