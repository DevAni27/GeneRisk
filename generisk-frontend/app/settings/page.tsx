"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOutIcon } from "lucide-react";
import { workerStates } from "@/data/states";
import { ToggleRow } from "@/components/ToggleRow";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";
import { supabase } from "@/lib/supabase";

type TabId = "profile" | "preferences" | "model" | "about";

const TABS: { id: TabId; label: string }[] = [
  { id: "profile", label: "Profile" },
  { id: "preferences", label: "Preferences" },
  { id: "model", label: "Model & data" },
  { id: "about", label: "About & disclaimer" },
];

const LANGUAGES = ["English", "Hindi", "Marathi", "Odia", "Telugu"];

const GENES = [
  { value: "HBB", label: "HBB — sickle cell / thalassemia" },
  { value: "G6PD", label: "G6PD — stretch goal" },
];

const FIELD_CLASSES =
  "h-11 w-full rounded-soft border border-line bg-paper px-3.5 text-sm text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25";

const SELECT_CLASSES = `${FIELD_CLASSES} appearance-none bg-[url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234A5A5F' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>")] bg-[length:16px_16px] bg-[right_0.85rem_center] bg-no-repeat pr-10`;

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 block font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft"
    >
      {children}
    </label>
  );
}

function Card({
  title,
  subtext,
  children,
}: {
  title: string;
  subtext?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-card border border-line bg-white p-6 sm:p-7">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {subtext && <p className="mt-1 text-sm text-ink-soft">{subtext}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("profile");

  const {
    workerName,
    workerId: authWorkerId,
    facility: authFacility,
    state: authState,
    logout,
    updateProfile,
  } = useAuth();

  const [fullName, setFullName] = useState(workerName || "");
  const [workerId, setWorkerId] = useState(authWorkerId || "");
  const [facility, setFacility] = useState(authFacility || "");
  const [state, setState] = useState(authState || workerStates[0]);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const [language, setLanguage] = useState("English");
  const [showDeltaScore, setShowDeltaScore] = useState(true);
  const [highContrast, setHighContrast] = useState(false);

  const [defaultGene, setDefaultGene] = useState("HBB");
  const [useCachedResults, setUseCachedResults] = useState(true);
  const [showClinVar, setShowClinVar] = useState(true);

  const router = useRouter();
  const { theme, setTheme } = useTheme();

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-teal">
        Device settings
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-[34px]">
        Settings
      </h1>

      <div className="mt-8 grid grid-cols-1 items-start gap-6 lg:grid-cols-[13.5rem_1fr]">
        <aside className="rounded-card border border-line bg-white p-3">
          <nav aria-label="Settings sections" className="flex flex-col gap-1">
            {TABS.map((tab) => {
              const isActive = tab.id === activeTab;
              return (
                <button
                  key={tab.id}
                  type="button"
                  aria-current={isActive ? "page" : undefined}
                  onClick={() => setActiveTab(tab.id)}
                  className={`rounded-soft px-3.5 py-2.5 text-left text-sm transition-colors duration-150 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 ${
                    isActive
                      ? "bg-teal/10 font-medium text-teal"
                      : "text-ink-soft hover:bg-paper hover:text-ink"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-3 border-t border-line pt-3">
            <button
              type="button"
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="flex w-full items-center gap-2 rounded-soft px-3.5 py-2.5 text-left text-sm text-clay transition-colors duration-150 ease-out hover:bg-clay/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-clay/40"
            >
              <LogOutIcon className="h-4 w-4" aria-hidden="true" />
              Log out
            </button>
          </div>
        </aside>

        <div className="space-y-6">
          {activeTab === "profile" && (
            <Card title="Worker profile" subtext="Shown on any exported or shared triage result.">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel htmlFor="settings-name">Full name</FieldLabel>
                  <input
                    id="settings-name"
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    className={FIELD_CLASSES}
                  />
                </div>
                <div>
                  <FieldLabel htmlFor="settings-worker-id">Worker ID</FieldLabel>
                  <input
                    id="settings-worker-id"
                    type="text"
                    value={workerId}
                    onChange={(event) => setWorkerId(event.target.value)}
                    className={`${FIELD_CLASSES} font-mono`}
                  />
                </div>
                <div>
                  <FieldLabel htmlFor="settings-facility">Health center / camp</FieldLabel>
                  <input
                    id="settings-facility"
                    type="text"
                    value={facility}
                    onChange={(event) => setFacility(event.target.value)}
                    className={FIELD_CLASSES}
                  />
                </div>
                <div>
                  <FieldLabel htmlFor="settings-state">State</FieldLabel>
                  <select
                    id="settings-state"
                    value={state}
                    onChange={(event) => setState(event.target.value)}
                    className={SELECT_CLASSES}
                  >
                    {workerStates.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-6 flex items-center gap-3">
                <button
                  type="button"
                  onClick={async () => {
                    setSaveStatus("saving");
                    const { error, data } = await supabase
                      .from("workers")
                      .update({ full_name: fullName, facility, state })
                      .eq("worker_id", workerId)
                      .select();

                    if (error || !data || data.length === 0) {
                      console.error("Failed to update profile:", error || "No matching worker row found");
                      setSaveStatus("error");
                      return;
                    }

                    updateProfile({ workerName: fullName, facility, state });
                    setSaveStatus("saved");
                    setTimeout(() => setSaveStatus("idle"), 2000);
                  }}
                  disabled={saveStatus === "saving"}
                  className="h-11 rounded-soft bg-teal px-6 text-sm font-semibold tracking-wide text-white transition-colors duration-150 ease-out hover:bg-[#095A54] focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:opacity-60"
                >
                  {saveStatus === "saving" ? "Saving…" : "Save changes"}
                </button>
                {saveStatus === "saved" && (
                  <span className="text-sm text-moss">Saved</span>
                )}
                {saveStatus === "error" && (
                  <span className="text-sm text-clay">Couldn&apos;t save — try again</span>
                )}
              </div>
            </Card>
          )}

          {activeTab === "preferences" && (
            <Card
              title="Language & display"
              subtext="Applies to plain-language explanations and the interface."
            >
              <div className="max-w-xs">
                <FieldLabel htmlFor="settings-language">Explanation language</FieldLabel>
                <select
                  id="settings-language"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                  className={SELECT_CLASSES}
                >
                  {LANGUAGES.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mt-6">
                <ToggleRow
                  id="settings-dark-theme"
                  label="Dark theme"
                  description="Switch the interface to a dark color scheme"
                  checked={theme === "dark"}
                  onChange={(checked) => setTheme(checked ? "dark" : "light")}
                />
              </div>

              <div className="mt-6 border-t border-line">
                <ToggleRow
                  id="settings-delta"
                  label="Show technical delta score"
                  description="Display the raw Evo2 delta value alongside the plain-language read"
                  checked={showDeltaScore}
                  onChange={setShowDeltaScore}
                />
                <ToggleRow
                  id="settings-contrast"
                  label="High-contrast mode"
                  description="Larger text and stronger colors for outdoor/low-light screening camps"
                  checked={highContrast}
                  onChange={setHighContrast}
                />
              </div>
            </Card>
          )}

          {activeTab === "model" && (
            <>
              <Card title="Default gene">
                <div className="max-w-md">
                  <FieldLabel htmlFor="settings-gene">Gene used for new lookups</FieldLabel>
                  <select
                    id="settings-gene"
                    value={defaultGene}
                    onChange={(event) => setDefaultGene(event.target.value)}
                    className={SELECT_CLASSES}
                  >
                    {GENES.map((gene) => (
                      <option key={gene.value} value={gene.value}>
                        {gene.label}
                      </option>
                    ))}
                  </select>
                </div>
              </Card>

              <Card title="Demo & caching">
                <div className="border-t border-line">
                  <ToggleRow
                    id="settings-cache"
                    label="Use cached results for pinned demo variants"
                    description="Avoids waiting on the live API for the 3-4 variants used on stage"
                    checked={useCachedResults}
                    onChange={setUseCachedResults}
                  />
                  <ToggleRow
                    id="settings-clinvar"
                    label="Show ClinVar comparison"
                    description="Turn off to preview how results look with clinical data unavailable"
                    checked={showClinVar}
                    onChange={setShowClinVar}
                  />
                </div>
              </Card>
            </>
          )}

          {activeTab === "about" && (
            <Card title="What GeneRisk is — and isn't">
              <p className="max-w-2xl text-sm leading-relaxed text-ink">
                GeneRisk gives a free, instant, first-pass triage signal on HBB
                gene variants using the Evo2 genomic AI model, compared against
                ClinVar where available. It is{" "}
                <strong className="font-semibold text-ink">not</strong> a
                diagnostic tool and does{" "}
                <strong className="font-semibold text-ink">not</strong> replace a
                genetic counselor or physician. Every result should be reviewed
                by a trained professional before being shared with a patient.
              </p>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}