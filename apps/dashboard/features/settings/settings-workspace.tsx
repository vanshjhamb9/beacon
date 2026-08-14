"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const TABS = ["Sources", "Discovery", "Outreach", "API Keys", "Preferences"] as const;

const DEFAULT_SOURCES = [
  { id: "reddit", name: "Reddit", subreddits: "r/SaaS, r/startups, r/entrepreneur", enabled: true },
  { id: "indie_hackers", name: "Indie Hackers", subreddits: "", enabled: true },
  { id: "product_hunt", name: "Product Hunt", subreddits: "", enabled: true },
  { id: "hacker_news", name: "Hacker News", subreddits: "", enabled: true },
  { id: "devto", name: "Dev.to", subreddits: "", enabled: true },
  { id: "rss", name: "RSS Feeds", subreddits: "TechCrunch, The Verge, SaaStr", enabled: false },
];

export function SettingsWorkspace() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Sources");
  const [sources, setSources] = useState(DEFAULT_SOURCES);
  const [schedule, setSchedule] = useState("09:00");
  const [autoAdd, setAutoAdd] = useState(true);
  const [minScore, setMinScore] = useState("70");
  const [dailyLimit, setDailyLimit] = useState("50");
  const [mode, setMode] = useState("sandbox");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">Configure your lead discovery and outreach</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Settings</h1>
      </header>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto scrollbar-thin">
        {TABS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setTab(item)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm transition",
              tab === item ? "bg-primary/15 text-foreground" : "text-muted-foreground hover:bg-muted/40"
            )}
          >
            {item}
          </button>
        ))}
      </div>

      {/* Sources Tab */}
      {tab === "Sources" && (
        <Card>
          <CardHeader>
            <CardTitle>Lead Sources</CardTitle>
            <CardDescription>Enable or disable lead discovery sources</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {sources.map((source) => (
              <div
                key={source.id}
                className="flex items-center justify-between rounded-lg border border-border/60 p-4"
              >
                <div>
                  <p className="font-medium">{source.name}</p>
                  {source.subreddits && (
                    <p className="text-xs text-muted-foreground">{source.subreddits}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setSources(sources.map((s) => (s.id === source.id ? { ...s, enabled: !s.enabled } : s)))
                  }
                  className={cn(
                    "relative h-6 w-11 rounded-full transition-colors",
                    source.enabled ? "bg-primary" : "bg-muted"
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform",
                      source.enabled ? "translate-x-5" : "translate-x-0.5"
                    )}
                  />
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Discovery Tab */}
      {tab === "Discovery" && (
        <Card>
          <CardHeader>
            <CardTitle>Discovery Schedule</CardTitle>
            <CardDescription>Configure automatic lead discovery</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="block space-y-1 text-sm">
              Run daily at
              <Input
                type="time"
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
              />
            </label>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Auto-add to pipeline</p>
                <p className="text-xs text-muted-foreground">Automatically add leads above min score</p>
              </div>
              <button
                type="button"
                onClick={() => setAutoAdd(!autoAdd)}
                className={cn(
                  "relative h-6 w-11 rounded-full transition-colors",
                  autoAdd ? "bg-primary" : "bg-muted"
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform",
                    autoAdd ? "translate-x-5" : "translate-x-0.5"
                  )}
                />
              </button>
            </div>

            <label className="block space-y-1 text-sm">
              Min score to auto-add
              <Input
                type="number"
                min={0}
                max={100}
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
              />
            </label>
          </CardContent>
        </Card>
      )}

      {/* Outreach Tab */}
      {tab === "Outreach" && (
        <Card>
          <CardHeader>
            <CardTitle>Outreach Settings</CardTitle>
            <CardDescription>Configure outreach mode and limits</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="block space-y-1 text-sm">
              Communication Mode
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-card px-3 py-2 text-sm"
              >
                <option value="sandbox">Sandbox (Test)</option>
                <option value="production">Production (Live)</option>
              </select>
            </label>

            <label className="block space-y-1 text-sm">
              Daily email limit
              <Input
                type="number"
                min={1}
                max={1000}
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
              />
            </label>

            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3">
              <p className="text-sm text-yellow-500">
                Production mode requires Gmail OAuth connection. Sandbox mode uses test emails only.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Keys Tab */}
      {tab === "API Keys" && (
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>Managed securely on the server</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { name: "Reddit API", status: "Configure in .env" },
              { name: "Gmail OAuth", status: "Configure in Integrations" },
              { name: "SMTP", status: "Configure in .env" },
              { name: "OpenAI", status: "Configure in .env" },
            ].map((key) => (
              <div
                key={key.name}
                className="flex items-center justify-between rounded-lg border border-border/60 px-4 py-3"
              >
                <span className="font-medium">{key.name}</span>
                <span className="text-xs text-muted-foreground">{key.status}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Preferences Tab */}
      {tab === "Preferences" && (
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">Theme</p>
                <p className="text-xs text-muted-foreground">Dark for focus</p>
              </div>
              <span className="rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary">Dark</span>
            </div>

            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">Refresh Interval</p>
                <p className="text-xs text-muted-foreground">How often data refreshes</p>
              </div>
              <span className="text-sm text-muted-foreground">30 seconds</span>
            </div>

            <div className="rounded-lg border border-border/60 p-4">
              <p className="text-sm font-medium">About</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Beacon AI - Founder Revenue OS v0.1.0
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
