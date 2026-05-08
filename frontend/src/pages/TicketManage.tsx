import { useEffect, useState } from 'react';
import { Table, Tag, Tabs } from 'antd';
import { getTickets, getOrders } from '../services/api';
import type { AfterSalesTicket, Order } from '../services/types';

const TICKET_STATUS_COLORS: Record<string, string> = {
  open: 'blue',
  in_progress: 'orange',
  resolved: 'green',
  closed: 'default',
};

const TICKET_STATUS_LABELS: Record<string, string> = {
  open: '待处理',
  in_progress: '处理中',
  resolved: '已解决',
  closed: '已关闭',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'default',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

const PRIORITY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急',
};

function TicketTable() {
  const [data, setData] = useState<AfterSalesTicket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTickets()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: '工单号', dataIndex: 'ticket_number', key: 'ticket_number', width: 160 },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    {
      title: '问题类型',
      dataIndex: 'issue_type',
      key: 'issue_type',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (v: string) => (
        <Tag color={PRIORITY_COLORS[v] ?? 'default'}>{PRIORITY_LABELS[v] ?? v}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={TICKET_STATUS_COLORS[v] ?? 'default'}>{TICKET_STATUS_LABELS[v] ?? v}</Tag>
      ),
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ];

  return (
    <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
  );
}

function OrderTable() {
  const [data, setData] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOrders()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: '订单号', dataIndex: 'order_number', key: 'order_number', width: 160 },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (v: number) => `¥${v?.toFixed(2)}`,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ];

  return (
    <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
  );
}

const items = [
  { key: 'tickets', label: '售后工单', children: <TicketTable /> },
  { key: 'orders', label: '订单列表', children: <OrderTable /> },
];

export default function TicketManage() {
  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>工单管理</h2>
      <Tabs items={items} defaultActiveKey="tickets" />
    </div>
  );
}
