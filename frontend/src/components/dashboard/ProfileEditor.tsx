"use client";

import type { BusinessProfile } from "@/lib/api";

const STAGE_LABELS: Record<string, { label: string; color: string }> = {
  idea: { label: "Idea Stage", color: "var(--color-text-muted)" },
  planning: { label: "Planning", color: "var(--color-gold)" },
  registered: { label: "Registered", color: "var(--color-earth)" },
  launched: { label: "Launched", color: "var(--color-green-light)" },
  growing: { label: "Growing", color: "var(--color-green)" },
  scaling: { label: "Scaling", color: "var(--color-green-dark)" },
};

const PROFILE_FIELDS = [
  { label: "Business Name", key: "business_name" as const, type: "text" },
  { label: "Business Type", key: "business_type" as const, type: "text" },
  { label: "Location", key: "location" as const, type: "text" },
  {
    label: "Startup Capital (UGX)",
    key: "startup_capital_ugx" as const,
    type: "number",
  },
  {
    label: "Monthly Revenue (UGX)",
    key: "monthly_revenue_ugx" as const,
    type: "number",
  },
  {
    label: "Monthly Profit (UGX)",
    key: "monthly_profit_ugx" as const,
    type: "number",
  },
  { label: "Employees", key: "employees" as const, type: "number" },
] as const;

interface ProfileEditorProps {
  profile: BusinessProfile;
  onUpdate: (key: keyof BusinessProfile, value: string | number) => void;
  onSave: () => void;
  saving: boolean;
  saveSuccess: boolean;
}

export function ProfileEditor({
  profile,
  onUpdate,
  onSave,
  saving,
  saveSuccess,
}: ProfileEditorProps) {
  return (
    <div className="space-y-4 animate-fade-in">
      <div className="card space-y-4">
        <h3
          className="text-base font-bold"
          style={{ color: "var(--color-green-dark)" }}
        >
          Business Profile
        </h3>
        {PROFILE_FIELDS.map((field) => (
          <div key={field.key}>
            <label
              className="text-xs font-semibold block mb-1"
              style={{ color: "var(--color-text-muted)" }}
              htmlFor={`profile-${field.key}`}
            >
              {field.label}
            </label>
            <input
              id={`profile-${field.key}`}
              className="input-field"
              type={field.type}
              value={profile[field.key]}
              min={
                field.type === "number" &&
                field.key !== "monthly_profit_ugx"
                  ? 0
                  : undefined
              }
              onChange={(e) =>
                onUpdate(
                  field.key,
                  field.type === "number"
                    ? parseInt(e.target.value) || 0
                    : e.target.value,
                )
              }
            />
          </div>
        ))}
        <div>
          <label
            className="text-xs font-semibold block mb-1"
            style={{ color: "var(--color-text-muted)" }}
            htmlFor="profile-stage"
          >
            Business Stage
          </label>
          <select
            id="profile-stage"
            className="input-field"
            value={profile.stage}
            onChange={(e) => onUpdate("stage", e.target.value)}
          >
            {Object.entries(STAGE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={onSave}
          className="btn-primary w-full"
          disabled={saving}
        >
          {saving ? "Saving..." : saveSuccess ? "Saved!" : "Save Profile"}
        </button>
      </div>
    </div>
  );
}
