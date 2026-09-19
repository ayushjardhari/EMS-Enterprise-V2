import { useEffect, useState } from "react";

interface SearchBarProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  debounceMs?: number;
}

/** Debounces input locally so we don't fire a request on every keystroke. */
export default function SearchBar({ placeholder = "Search...", onSearch, debounceMs = 350 }: SearchBarProps) {
  const [value, setValue] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => onSearch(value), debounceMs);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <input
      type="text"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={placeholder}
      className="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
    />
  );
}
