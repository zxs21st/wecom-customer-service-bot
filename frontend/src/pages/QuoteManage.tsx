import { useEffect, useState } from 'react';
import { Table, Tag, Spin } from 'antd';
import { getQuotes } from '../services/api';
import type { Quote } from '../services/types';

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  sent: 'blue',
  accepted: 'green',
  rejected: 'red',
  expired: 'orange',
};

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  sent: '已发送',
  accepted: '已接受',
  rejected: '已拒绝',
  expired: '已过期',
};

export default function QuoteManage() {
  const [data, setData] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQuotes()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: '报价单号', dataIndex: 'quote_number', key: 'quote_number', width: 160 },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '联系方式', dataIndex: 'customer_contact', key: 'customer_contact' },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (v: number) => `¥${v?.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] ?? 'default'}>{STATUS_LABELS[v] ?? v}</Tag>
      ),
    },
    { title: '有效期至', dataIndex: 'valid_until', key: 'valid_until', width: 140 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ];

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>报价管理</h2>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={{ pageSize: 10 }} />
    </div>
  );
}
