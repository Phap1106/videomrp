"use client";

export function Tabs<T extends string>({
  value,
  onChange,
  tabs
}: {
  value: T;
  onChange: (v: T) => void;
  tabs: { key: T; label: string }[];
}) {
  return (
    <div className="row" style={{ gap: 8 }}>
      {tabs.map(t => (
        <button
          key={t.key}
          className={`btn ${value === t.key ? "" : "secondary"}`}
          type="button"
          onClick={() => onChange(t.key)}
          style={{ padding: "8px 10px" }}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
