export default function Tabs({ tabs, active, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-700">
      {tabs.map(([key, label, badge]) => (
        <button key={key} onClick={() => onChange(key)}
          className={`whitespace-nowrap border-b-2 px-4 py-2 text-sm font-semibold ${active === key ? "border-indigo-600 text-indigo-600 dark:text-indigo-400" : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white"}`}>
          {label}{badge ? <span className="ml-1.5 rounded-full bg-rose-500 px-1.5 text-xs text-white">{badge}</span> : null}
        </button>
      ))}
    </div>
  );
}
