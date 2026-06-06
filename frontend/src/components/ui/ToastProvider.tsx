import { Toaster } from 'sonner';

export default function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      theme="dark"
      toastOptions={{
        style: {
          background: '#12121e',
          border: '1px solid #252540',
          color: '#e8e8ed',
          fontFamily: "'Noto Sans SC', system-ui, sans-serif",
        },
      }}
    />
  );
}