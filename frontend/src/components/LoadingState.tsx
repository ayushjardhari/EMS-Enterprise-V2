export default function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex h-40 w-full flex-col items-center justify-center gap-3 text-gray-500">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
