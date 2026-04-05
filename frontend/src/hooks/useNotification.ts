/**
 * Notification Hook
 * Antd message API wrapper
 */
import { App } from 'antd';

export function useNotification() {
  const { message, notification } = App.useApp();

  return {
    success: (content: string, duration = 3) => {
      message.success(content, duration);
    },
    error: (content: string, duration = 4) => {
      message.error(content, duration);
    },
    warning: (content: string, duration = 3) => {
      message.warning(content, duration);
    },
    info: (content: string, duration = 3) => {
      message.info(content, duration);
    },
    loading: (content: string) => {
      return message.loading(content, 0); // 0 = infinite
    },
    notify: {
      success: (title: string, description?: string) => {
        notification.success({ message: title, description });
      },
      error: (title: string, description?: string) => {
        notification.error({ message: title, description });
      },
      warning: (title: string, description?: string) => {
        notification.warning({ message: title, description });
      },
      info: (title: string, description?: string) => {
        notification.info({ message: title, description });
      },
    },
  };
}
