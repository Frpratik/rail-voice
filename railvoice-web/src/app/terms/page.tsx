import type { Metadata } from "next";
import { PageHeader } from "@/components/ui/empty-state";
import { Prose } from "@/components/layout/prose";

export const metadata: Metadata = { title: "Terms of use" };

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader eyebrow="Legal" title="Terms of use" description="The rules for using RailVoice." />
      <Prose>
        <h2>What RailVoice is</h2>
        <p>
          RailVoice lets passengers report problems at Western Railway suburban stations and lets
          station staff track them. It isn&apos;t an emergency service, and a report doesn&apos;t
          guarantee any particular action or timescale.
        </p>

        <h2>Your reports</h2>
        <ul>
          <li>Report only real problems that you have seen yourself.</li>
          <li>Don&apos;t post anything false, abusive, hateful or unlawful, or anyone&apos;s private details.</li>
          <li>Only upload photos you took, or have the right to share.</li>
          <li>Don&apos;t file duplicate or test reports, or use the site to advertise.</li>
        </ul>

        <h2>Moderation</h2>
        <p>
          Staff may hide or remove reports and comments that break these rules, and may restrict
          accounts that keep doing so. Passengers can flag content for review.
        </p>

        <h2>Content you post</h2>
        <p>
          You keep ownership of what you post, and you allow RailVoice and Western Railway staff to
          display and use it to handle and publish the report.
        </p>

        <h2>Changes</h2>
        <p>These terms may change. Using the site after a change means you accept the new version.</p>
      </Prose>
    </div>
  );
}
