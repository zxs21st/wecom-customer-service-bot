import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import {
  MessageOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { getDashboardStats } from '../services/api';
import type { DashboardStats as Stats } from '../services/types';

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据概览</h2>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总会话数"
              value={stats?.total_consultations ?? 0}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已解决"
              value={stats?.resolved ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="转人工"
              value={stats?.escalated ?? 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="解决率"
              value={stats?.resolution_rate ?? 0}
              suffix="%"
              prefix={<RiseOutlined />}
              precision={1}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic title="今日会话" value={stats?.today_consultations ?? 0} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="平均置信度" value={stats?.avg_confidence ?? 0} precision={2} suffix="/ 1.0" />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
