const paths = {
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m20 20-4.2-4.2" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  minus: <path d="M5 12h14" />,
  edit: <><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="m13.5 6.5 4 4" /></>,
  trash: <><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></>,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  inbound: <><path d="M12 4v12" /><path d="m7 11 5 5 5-5" /><path d="M5 20h14" /></>,
  outbound: <><path d="M12 20V8" /><path d="m7 13 5-5 5 5" /><path d="M5 4h14" /></>,
  alert: <><path d="M12 3 2.5 20h19z" /><path d="M12 10v4M12 17v.5" /></>,
  ban: <><circle cx="12" cy="12" r="8.5" /><path d="m6 6 12 12" /></>,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  refresh: <><path d="M20 11a8 8 0 1 0-2.3 5.7" /><path d="M20 5v6h-6" /></>,
  sliders: <><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></>,
};

export default function Icon({ name, size = 18, className = '' }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

export function StatusBadge({ status }) {
  const meta = {
    OK: { label: 'In stock', icon: 'check' },
    LOW: { label: 'Low', icon: 'alert' },
    OUT: { label: 'Out', icon: 'ban' },
  }[status];
  return (
    <span className={`badge badge--${status.toLowerCase()}`}>
      <Icon name={meta.icon} size={13} />
      {meta.label}
    </span>
  );
}
