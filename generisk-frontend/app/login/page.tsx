"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { workerStates } from "@/data/states";
import { useAuth } from "@/lib/auth-context";
import { supabase } from "@/lib/supabase";

type Mode = "login" | "signup";

interface FormValues {
  workerId: string;
  pin: string;
  state: string;
  fullName: string;
  confirmPin: string;
  facility: string;
}

const EMPTY_VALUES: FormValues = {
  workerId: "",
  pin: "",
  state: workerStates[0],
  fullName: "",
  confirmPin: "",
  facility: "",
};

const FIELD_CLASSES =
  "h-11 w-full rounded-soft border border-line bg-paper px-3.5 text-sm text-ink placeholder:text-ink-soft/70 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25";

const SELECT_CLASSES = `${FIELD_CLASSES} appearance-none bg-[url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234A5A5F' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>")] bg-[length:16px_16px] bg-[right_0.85rem_center] bg-no-repeat pr-10`;

function Label({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 block font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft"
    >
      {children}
    </label>
  );
}

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [values, setValues] = useState<FormValues>(EMPTY_VALUES);
  const router = useRouter();
  const { login } = useAuth();

  const isSignup = mode === "signup";

  const setField = (field: keyof FormValues) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setValues((current) => ({ ...current, [field]: event.target.value }));
  };

  const toggleMode = () => {
    setMode(isSignup ? "login" : "signup");
  };

  return (
    <main className="flex min-h-full w-full items-center justify-center bg-paper px-6 py-12 font-sans">
      <div className="w-full max-w-[380px]">
        <div className="rounded-card border border-line bg-white p-6 sm:p-7">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-teal">
            Health worker access
          </p>
          <h1 className="mt-2.5 text-xl font-semibold tracking-tight text-ink">
            {isSignup ? "Create your worker account" : "Log in to GeneRisk"}
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            {isSignup
              ? "Register your worker ID and camp so every lookup you run is logged against the right facility."
              : "Sign in with your screening camp worker ID to log variant lookups against your facility."}
          </p>

          <form
            className="mt-6 space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              const displayName = isSignup
                ? values.fullName || values.workerId
                : values.workerId;

              if (isSignup) {
                const { error } = await supabase.from("workers").insert({
                  worker_id: values.workerId,
                  full_name: values.fullName,
                  facility: values.facility,
                  state: values.state,
                });
                if (error) console.error("Failed to save worker:", error);
              }

              login(displayName, values.workerId, values.facility, values.state);
              router.push("/");
            }}
          >
            {isSignup && (
              <div>
                <Label htmlFor="fullName">Full name</Label>
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  autoComplete="name"
                  value={values.fullName}
                  onChange={setField("fullName")}
                  placeholder="Sunita Patil"
                  className={FIELD_CLASSES}
                />
              </div>
            )}

            <div>
              <Label htmlFor="workerId">Worker ID / phone number</Label>
              <input
                id="workerId"
                name="workerId"
                type="text"
                inputMode="text"
                autoComplete="username"
                value={values.workerId}
                onChange={setField("workerId")}
                placeholder="ASHA-04821 or 98xxxxxxxx"
                className={`${FIELD_CLASSES} font-mono`}
              />
            </div>

            {isSignup ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="pin">PIN</Label>
                  <input
                    id="pin"
                    name="pin"
                    type="password"
                    inputMode="numeric"
                    autoComplete="new-password"
                    value={values.pin}
                    onChange={setField("pin")}
                    placeholder="••••"
                    className={`${FIELD_CLASSES} font-mono tracking-[0.2em]`}
                  />
                </div>
                <div>
                  <Label htmlFor="confirmPin">Confirm PIN</Label>
                  <input
                    id="confirmPin"
                    name="confirmPin"
                    type="password"
                    inputMode="numeric"
                    autoComplete="new-password"
                    value={values.confirmPin}
                    onChange={setField("confirmPin")}
                    placeholder="••••"
                    className={`${FIELD_CLASSES} font-mono tracking-[0.2em]`}
                  />
                </div>
              </div>
            ) : (
              <div>
                <Label htmlFor="pin">PIN</Label>
                <input
                  id="pin"
                  name="pin"
                  type="password"
                  inputMode="numeric"
                  autoComplete="current-password"
                  value={values.pin}
                  onChange={setField("pin")}
                  placeholder="••••"
                  className={`${FIELD_CLASSES} font-mono tracking-[0.2em]`}
                />
              </div>
            )}

            {isSignup ? (
              <>
                <div>
                  <Label htmlFor="facility">Primary health center / camp</Label>
                  <input
                    id="facility"
                    name="facility"
                    type="text"
                    value={values.facility}
                    onChange={setField("facility")}
                    placeholder="PHC Betul"
                    className={FIELD_CLASSES}
                  />
                </div>
                <div>
                  <Label htmlFor="signup-state">State</Label>
                  <select
                    id="signup-state"
                    name="state"
                    value={values.state}
                    onChange={setField("state")}
                    className={SELECT_CLASSES}
                  >
                    {workerStates.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            ) : (
              <div>
                <Label htmlFor="state">State</Label>
                <select
                  id="state"
                  name="state"
                  value={values.state}
                  onChange={setField("state")}
                  className={SELECT_CLASSES}
                >
                  {workerStates.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              type="submit"
              className="mt-1 h-11 w-full rounded-soft bg-teal text-sm font-semibold tracking-wide text-white transition-colors duration-150 ease-out hover:bg-[#095A54] focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
            >
              {isSignup ? "Create account" : "Log in"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-ink-soft">
            {isSignup ? "Already have an account? " : "New to GeneRisk? "}
            <button
              type="button"
              onClick={toggleMode}
              className="rounded text-teal underline decoration-teal/30 underline-offset-2 transition-colors duration-150 ease-out hover:decoration-teal focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40"
            >
              {isSignup ? "Log in instead" : "Create an account"}
            </button>
          </p>
        </div>

        <p className="mt-4 rounded-soft border border-line bg-white/60 px-4 py-3 text-xs leading-relaxed text-ink-soft">
          GeneRisk gives a first-pass triage read only. Every result should still
          be reviewed by a genetic counselor before being shared with a patient.
        </p>
      </div>
    </main>
  );
}