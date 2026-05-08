import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, Space, Popconfirm, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import {
  getKnowledgeDocuments,
  createKnowledgeDocument,
  updateKnowledgeDocument,
  deleteKnowledgeDocument,
} from '../services/api';
import type { KnowledgeDocument } from '../services/types';

const CATEGORIES = [
  { label: '产品知识', value: 'product_knowledge' },
  { label: '配置指南', value: 'config_guide' },
  { label: '售后服务', value: 'after_sales' },
];

export default function KnowledgeManage() {
  const [data, setData] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeDocument | null>(null);
  const [form] = Form.useForm();

  const fetchData = () => {
    setLoading(true);
    getKnowledgeDocuments()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: KnowledgeDocument) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editing) {
        await updateKnowledgeDocument(editing.id, values);
        message.success('更新成功');
      } else {
        await createKnowledgeDocument(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchData();
    } catch {
      message.error('操作失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteKnowledgeDocument(id);
      message.success('删除成功');
      fetchData();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', width: 200 },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (v: string) => {
        const cat = CATEGORIES.find((c) => c.value === v);
        return cat ? cat.label : v;
      },
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <>
          {tags?.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: unknown, record: KnowledgeDocument) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>知识库管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增文档
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
      <Modal
        title={editing ? '编辑文档' : '新增文档'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <Input.TextArea rows={6} />
          </Form.Item>
          <Form.Item name="category" label="类别" rules={[{ required: true }]}>
            <Select options={CATEGORIES} />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
