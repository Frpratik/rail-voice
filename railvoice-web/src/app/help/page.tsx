import type { Metadata } from "next";
import { PageHeader } from "@/components/ui/empty-state";
import { Prose } from "@/components/layout/prose";

export const metadata: Metadata = { title: "How it works" };

const STATUSES = [
  ["Submitted", "Your report is in. Station staff have been told."],
  ["Under review", "Staff are checking the details."],
  ["Verified", "Staff confirmed the problem is real."],
  ["Assigned", "A named officer is responsible for it."],
  ["Forwarded", "Sent to the station manager, division or zone office."],
  ["Action started / In progress", "Work has begun."],
  ["Completed", "Staff say it's fixed. You'll be asked to confirm."],
  ["Closed", "Confirmed fixed, or resolved with no further action."],
  ["Rejected", "Staff decided it isn't a railway matter or can't be acted on."],
];

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        eyebrow="Help"
        title="How RailVoice works"
        description="Report a problem at a Western Railway station, between Churchgate and Virar, and follow it until it's fixed."
      />
      <Prose>
        <div className="border-2 border-destructive bg-destructive/10 p-4">
          <p className="text-display text-xl text-destructive">In an emergency, don&apos;t use this site</p>
          <p>
            Railway helpline <strong>139</strong> · RPF security helpline <strong>182</strong> ·
            National emergency <strong>112</strong>. RailVoice is read by station staff, not
            monitored around the clock.
          </p>
        </div>

        <h2>Reporting a problem</h2>
        <ul>
          <li>Sign in with your mobile number.</li>
          <li>Pick the station, choose a category and describe exactly where the problem is.</li>
          <li>Add up to three photos if you can. They help staff find and fix it.</li>
          <li>
            If someone has already reported the same thing, back that report instead of making a
            new one. Reports with more backing are looked at first.
          </li>
        </ul>

        <h2>After you report</h2>
        <ul>
          <li>Station staff are notified straight away.</li>
          <li>You get a notification each time the status changes.</li>
          <li>You can withdraw a report until staff start work on it.</li>
          <li>When staff mark it fixed, tell us whether it really is. If not, it goes back to staff.</li>
        </ul>

        <h2>What the statuses mean</h2>
        <ul>
          {STATUSES.map(([name, meaning]) => (
            <li key={name}>
              <strong>{name}.</strong> {meaning}
            </li>
          ))}
        </ul>

        <h2>Keeping it useful</h2>
        <ul>
          <li>One problem per report, and only real problems at real stations.</li>
          <li>Be civil in comments. Don&apos;t post other people&apos;s personal details.</li>
          <li>Use the flag button on spam, abuse or made-up reports. Staff review every flag.</li>
          <li>There is a daily limit on how many reports one person can file.</li>
        </ul>
      </Prose>
    </div>
  );
}
