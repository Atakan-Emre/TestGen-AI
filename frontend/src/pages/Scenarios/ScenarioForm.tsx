import React from 'react';
import { Modal, Form, Input, Select } from 'antd';
import { Category, Scenario } from '../../api/types';

interface ScenarioFormProps {
    open: boolean;
    onCancel: () => void;
    onSubmit: (values: any) => void;
    initialValues?: Scenario | null;
    loading?: boolean;
    categories: Category[];
}

export const ScenarioForm: React.FC<ScenarioFormProps> = ({
    open,
    onCancel,
    onSubmit,
    initialValues,
    loading,
    categories,
}) => {
    const [form] = Form.useForm();

    React.useEffect(() => {
        if (open && initialValues) {
            form.setFieldsValue(initialValues);
        } else {
            form.resetFields();
        }
    }, [open, initialValues, form]);

    const handleOk = () => {
        form.submit();
    };

    return (
        <Modal
            title={initialValues ? 'Senaryo Düzenle' : 'Yeni Senaryo'}
            open={open}
            onCancel={onCancel}
            onOk={handleOk}
            confirmLoading={loading}
            width={800}
        >
            <Form
                form={form}
                layout="vertical"
                onFinish={onSubmit}
                initialValues={{
                    test_data: {},
                    expected_result: '',
                }}
            >
                <Form.Item
                    name="category_id"
                    label="Kategori"
                    rules={[{ required: true, message: 'Lütfen kategori seçin' }]}
                >
                    <Select>
                        {categories.map(category => (
                            <Select.Option key={category.id} value={category.id}>
                                {category.name}
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item
                    name="name"
                    label="Senaryo Adı"
                    rules={[{ required: true, message: 'Lütfen senaryo adını girin' }]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    name="description"
                    label="Açıklama"
                >
                    <Input.TextArea rows={4} />
                </Form.Item>

                <Form.Item
                    name="test_data"
                    label="Test Verisi"
                    rules={[{ required: true, message: 'Lütfen test verisini girin' }]}
                >
                    <Input.TextArea 
                        rows={6} 
                        placeholder="JSON formatında test verisi girin"
                        onChange={(e) => {
                            try {
                                const json = JSON.parse(e.target.value);
                                form.setFieldsValue({ test_data: json });
                            } catch (error) {
                                // JSON parse hatası - kullanıcı henüz yazıyor olabilir
                            }
                        }}
                    />
                </Form.Item>

                <Form.Item
                    name="expected_result"
                    label="Beklenen Sonuç"
                    rules={[{ required: true, message: 'Lütfen beklenen sonucu girin' }]}
                >
                    <Input.TextArea rows={4} />
                </Form.Item>
            </Form>
        </Modal>
    );
}; 