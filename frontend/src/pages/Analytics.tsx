import { useEffect, useState } from 'react';
import { Card, Spin } from 'antd';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getDailyTrends } from '../services/api';
import type { DailyStat } from '../services/types';

export default function Analytics() {
  const [data, setData] = useState<DailyStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDailyTrends(30)
      .then(({ data: stats }) => {
        const formatted = stats.map((s) => ({
          ...s,
          date: s.stat_date.slice(5), // show MM-DD
        }));
        setData(formatted);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>数据分析</h2>
      <Card title="30天会话趋势">
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="total_queries" name="总会话" stroke="#1890ff" strokeWidth={2} />
            <Line type="monotone" dataKey="resolved_queries" name="已解决" stroke="#52c41a" strokeWidth={2} />
            <Line type="monotone" dataKey="escalated_queries" name="转人工" stroke="#ff4d4f" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
