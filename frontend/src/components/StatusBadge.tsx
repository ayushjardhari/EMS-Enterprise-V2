const COLOR_MAP: Record<string, string> = {
  ACTIVE: "bg-green-100 text-green-700",
  INACTIVE: "bg-gray-100 text-gray-600",
  ON_LEAVE: "bg-amber-100 text-amber-700",
  AVAILABLE: "bg-green-100 text-green-700",
  PARTIALLY_AVAILABLE: "bg-amber-100 text-amber-700",
  UNAVAILABLE: "bg-red-100 text-red-700",
  PLANNED: "bg-blue-100 text-blue-700",
  ON_HOLD: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-gray-100 text-gray-600",
};

export default function StatusBadge({ status }: { status: string }) {
  const classes = COLOR_MAP[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
