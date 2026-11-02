import type { Metadata } from "next";
import { PageHeader } from "@/components/ui/empty-state";
import { Prose } from "@/components/layout/prose";

export const metadata: Metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader eyebrow="Legal" title="Privacy" description="What RailVoice keeps about you, and why." />
      <Prose>
        <h2>What we collect</h2>
        <ul>
          <li>
            <strong>Your mobile number.</strong> We keep a one-way hash of it to recognise you when
            you sign in, plus its last four digits. We don&apos;t store the full number in readable form.
          </li>
          <li>A display name (and an email address if you sign in with Google).</li>
          <li>The reports, comments, photos and backing you add, and the time you added them.</li>
          <li>Sign-in activity (time, IP address and browser) to detect abuse.</li>
        </ul>

        <h2>What is public</h2>
        <p>
          Reports, their photos, comments, status history and the display name of the person who
          wrote them are visible to anyone. Don&apos;t put phone numbers, ticket details or other
          people&apos;s personal information in a report, comment or photo.
        </p>

        <h2>Who sees the rest</h2>
        <p>
          Railway station and division staff using the control room can see reports in their area
          and the people who made them. Your mobile number is not shown to other passengers.
        </p>

        <h2>How we use it</h2>
        <ul>
          <li>To pass your report to the right station and keep you updated on it.</li>
          <li>To prevent spam and abuse, including daily limits and moderation.</li>
          <li>We don&apos;t sell your information or use it for advertising.</li>
        </ul>

        <h2>AI features</h2>
        <p>
          When AI features are switched on, the text and photos of a report are sent to our AI providers
          (Groq, Google Gemini or Anthropic) to draft reports, translate them, check for duplicates and spam, and help staff. Your
          name and mobile number are never sent. AI only suggests; people at the railway make every decision.
        </p>

        <h2>Your choices</h2>
        <p>
          You can withdraw a report before work starts. To have your account removed, ask the
          station office or the RailVoice administrator. Reports already handled by staff may be
          kept as a record, without your name.
        </p>
      </Prose>
    </div>
  );
}
