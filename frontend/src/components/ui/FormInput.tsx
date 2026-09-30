import React from 'react';

const inputCls = 'w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500';

interface InputProps {
  label: string;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function FormInput({ label, type = 'text', value, onChange }: InputProps) {
  return (
    <div>
      <label className="text-xs text-gray-400 block mb-1">{label}</label>
      <input type={type} value={value} onChange={onChange} className={inputCls} />
    </div>
  );
}

interface FieldProps {
  label: string;
  children: React.ReactNode;
}

export function FormField({ label, children }: FieldProps) {
  return (
    <div>
      <label className="text-xs text-gray-400 block mb-1">{label}</label>
      {children}
    </div>
  );
}

export { inputCls };
