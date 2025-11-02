import clsx from "clsx";

const phaseMap: Record<string, { label: string; color: string; glow: string }> = {
  COOP: { label: "Cooperation", color: "bg-coop/20 text-coop border-coop/50", glow: "shadow-[0_0_30px_theme(colors.coop/50)]" },
  DEFECT: { label: "Defection", color: "bg-defect/20 text-defect border-defect/60", glow: "shadow-[0_0_30px_theme(colors.defect/40)]" },
  FORGIVE: { label: "Forgiveness", color: "bg-forgive/20 text-forgive border-forgive/50", glow: "shadow-[0_0_30px_theme(colors.forgive/40)]" }
};

export function PhaseBadge({ phase }: { phase: string }) {
  const key = phase?.toUpperCase();
  const config = phaseMap[key] ?? {
    label: phase ?? "Unknown",
    color: "bg-neutral-800 text-neutral-100 border-neutral-700",
    glow: ""
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium uppercase tracking-wide",
        config.color,
        config.glow
      )}
    >
      <span className="h-2 w-2 rounded-full bg-current" aria-hidden="true" />
      {config.label}
    </span>
  );
}
