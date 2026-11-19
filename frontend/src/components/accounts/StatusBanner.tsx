interface StatusBannerProps {
  message: string
  type?: 'info' | 'warning'
}

export function StatusBanner({ message, type = 'info' }: StatusBannerProps) {
  return (
    <div
      style={{
        border: '1px solid #8d8d8d',
        borderLeft: `4px solid ${type === 'warning' ? '#c62828' : '#161616'}`,
        background: '#f4f4f4',
        padding: '12px 16px',
        fontSize: '14px',
        lineHeight: '20px',
      }}
    >
      {message}
    </div>
  )
}
