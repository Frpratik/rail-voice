"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Lang = "en" | "hi" | "mr";

export const LANGUAGES: { code: Lang; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
];

type Entry = { en: string; hi: string; mr: string };

const STRINGS = {
  "nav.feed": { en: "Feed", hi: "फ़ीड", mr: "फीड" },
  "nav.home": { en: "Home", hi: "होम", mr: "होम" },
  "nav.stations": { en: "Stations", hi: "स्टेशन", mr: "स्थानके" },
  "nav.myIssues": { en: "My Issues", hi: "मेरी शिकायतें", mr: "माझ्या तक्रारी" },
  "nav.report": { en: "Report", hi: "रिपोर्ट", mr: "तक्रार" },
  "nav.reportIssue": { en: "Report issue", hi: "शिकायत करें", mr: "तक्रार करा" },
  "nav.control": { en: "Control Room", hi: "कंट्रोल रूम", mr: "नियंत्रण कक्ष" },
  "nav.profile": { en: "Profile", hi: "प्रोफ़ाइल", mr: "प्रोफाइल" },
  "nav.signIn": { en: "Sign in", hi: "साइन इन", mr: "साइन इन" },
  "nav.leaderboard": { en: "Leaderboard", hi: "लीडरबोर्ड", mr: "लीडरबोर्ड" },
  "nav.transparency": { en: "Transparency", hi: "पारदर्शिता", mr: "पारदर्शकता" },
  "nav.help": { en: "Help", hi: "मदद", mr: "मदत" },

  "home.tagline": {
    en: "Broken lift, dirty platform, unsafe edge? Report it here. Other passengers back the report, and the station office sees the most-supported problems first.",
    hi: "लिफ्ट खराब, प्लेटफॉर्म गंदा, किनारा असुरक्षित? यहाँ रिपोर्ट करें। दूसरे यात्री उसका समर्थन करते हैं, और स्टेशन कार्यालय सबसे ज़्यादा समर्थित समस्याएँ पहले देखता है।",
    mr: "लिफ्ट बंद, फलाट अस्वच्छ, कडा असुरक्षित? इथे तक्रार करा. इतर प्रवासी तिला पाठिंबा देतात आणि स्थानक कार्यालय सर्वाधिक पाठिंबा असलेल्या समस्या आधी पाहते.",
  },
  "home.report": { en: "Report a problem", hi: "समस्या बताएँ", mr: "समस्या कळवा" },
  "home.myReports": { en: "My reports", hi: "मेरी रिपोर्ट", mr: "माझ्या तक्रारी" },
  "home.open": { en: "Open", hi: "खुली", mr: "उघड्या" },
  "home.urgent": { en: "Urgent", hi: "तत्काल", mr: "तातडीच्या" },
  "home.fixed": { en: "Fixed", hi: "ठीक हुईं", mr: "सोडवलेल्या" },
  "home.allStations": { en: "All stations", hi: "सभी स्टेशन", mr: "सर्व स्थानके" },
  "home.search": {
    en: "Search by keyword, report number or station",
    hi: "शब्द, रिपोर्ट नंबर या स्टेशन से खोजें",
    mr: "शब्द, तक्रार क्रमांक किंवा स्थानकाने शोधा",
  },
  "home.reports": { en: "reports", hi: "रिपोर्ट", mr: "तक्रारी" },
  "home.nearMe": { en: "Near me", hi: "मेरे पास", mr: "माझ्या जवळ" },
  "home.myStations": { en: "My stations", hi: "मेरे स्टेशन", mr: "माझी स्थानके" },
  "home.openOnly": { en: "Open only", hi: "सिर्फ़ खुली", mr: "फक्त उघड्या" },
  "home.allCategories": { en: "All categories", hi: "सभी श्रेणियाँ", mr: "सर्व प्रकार" },
  "home.line": { en: "Western line", hi: "पश्चिम रेलवे लाइन", mr: "पश्चिम मार्ग" },
  "home.showAll": { en: "Show all", hi: "सभी दिखाएँ", mr: "सर्व दाखवा" },

  "sort.most_supported": { en: "Most supported", hi: "सबसे समर्थित", mr: "सर्वाधिक पाठिंबा" },
  "sort.newest": { en: "Newest", hi: "नई", mr: "नवीन" },
  "sort.urgent": { en: "Urgent first", hi: "तत्काल पहले", mr: "तातडीचे आधी" },

  "report.title": { en: "Report a problem", hi: "समस्या बताएँ", mr: "समस्या कळवा" },
  "report.station": { en: "Station", hi: "स्टेशन", mr: "स्थानक" },
  "report.useLocation": { en: "Use my location", hi: "मेरी लोकेशन लें", mr: "माझे स्थान वापरा" },
  "report.platform": { en: "Platform or area", hi: "प्लेटफॉर्म या जगह", mr: "फलाट किंवा जागा" },
  "report.train": { en: "Train / local (optional)", hi: "ट्रेन / लोकल (वैकल्पिक)", mr: "गाडी / लोकल (ऐच्छिक)" },
  "report.category": { en: "Category", hi: "श्रेणी", mr: "प्रकार" },
  "report.summary": { en: "Short title", hi: "छोटा शीर्षक", mr: "लहान शीर्षक" },
  "report.details": { en: "What is wrong?", hi: "क्या समस्या है?", mr: "काय समस्या आहे?" },
  "report.urgent": { en: "Urgent safety hazard?", hi: "तत्काल सुरक्षा ख़तरा?", mr: "तातडीचा सुरक्षा धोका?" },
  "report.photos": { en: "Photos (optional)", hi: "फ़ोटो (वैकल्पिक)", mr: "फोटो (ऐच्छिक)" },
  "report.addPhoto": { en: "Add photo", hi: "फ़ोटो जोड़ें", mr: "फोटो जोडा" },
  "report.submit": { en: "Submit report", hi: "रिपोर्ट भेजें", mr: "तक्रार पाठवा" },
  "report.submitting": { en: "Submitting…", hi: "भेज रहे हैं…", mr: "पाठवत आहे…" },
  "report.anon": {
    en: "Report without signing in",
    hi: "बिना साइन इन रिपोर्ट करें",
    mr: "साइन इन न करता तक्रार करा",
  },
  "report.danger": {
    en: "If someone is in danger, call now",
    hi: "अगर कोई ख़तरे में है, तो अभी कॉल करें",
    mr: "कोणी धोक्यात असल्यास आत्ताच कॉल करा",
  },
  "report.draft": { en: "Draft restored", hi: "ड्राफ़्ट वापस लाया गया", mr: "मसुदा परत आणला" },

  "issue.back": { en: "Back this report", hi: "समर्थन करें", mr: "पाठिंबा द्या" },
  "issue.backed": { en: "You've backed this", hi: "आपने समर्थन किया", mr: "तुम्ही पाठिंबा दिला" },
  "issue.follow": { en: "Follow", hi: "फ़ॉलो करें", mr: "फॉलो करा" },
  "issue.following": { en: "Following", hi: "फ़ॉलो कर रहे हैं", mr: "फॉलो करत आहात" },
  "issue.timeline": { en: "Timeline", hi: "टाइमलाइन", mr: "टाइमलाइन" },
  "issue.comments": { en: "Comments", hi: "टिप्पणियाँ", mr: "टिप्पण्या" },
  "issue.reply": { en: "Reply", hi: "जवाब", mr: "उत्तर" },

  "status.submitted": { en: "Submitted", hi: "दर्ज", mr: "नोंदवली" },
  "status.under_review": { en: "Under review", hi: "जाँच में", mr: "तपासणीत" },
  "status.verified": { en: "Verified", hi: "पुष्ट", mr: "खात्री झाली" },
  "status.assigned": { en: "Assigned", hi: "सौंपा गया", mr: "सोपवली" },
  "status.work_in_progress": { en: "In progress", hi: "काम जारी", mr: "काम सुरू" },
  "status.action_started": { en: "Action started", hi: "कार्रवाई शुरू", mr: "कारवाई सुरू" },
  "status.waiting_for_material": { en: "Waiting", hi: "प्रतीक्षा में", mr: "प्रतीक्षेत" },
  "status.completed": { en: "Completed", hi: "पूरा", mr: "पूर्ण" },
  "status.verified_complete": { en: "Verified done", hi: "पूरा पुष्ट", mr: "पूर्ण खात्री" },
  "status.closed": { en: "Closed", hi: "बंद", mr: "बंद" },
  "status.rejected": { en: "Rejected", hi: "अस्वीकृत", mr: "नाकारली" },
  "status.spam": { en: "Removed", hi: "हटाया गया", mr: "काढली" },
  "status.withdrawn": { en: "Withdrawn", hi: "वापस ली", mr: "मागे घेतली" },
  "status.forwarded_division": { en: "With division", hi: "डिवीज़न के पास", mr: "विभागाकडे" },
  "status.forwarded_zone": { en: "With zone", hi: "ज़ोन के पास", mr: "झोनकडे" },
  "status.forwarded_station_manager": { en: "With station manager", hi: "स्टेशन मैनेजर के पास", mr: "स्टेशन मॅनेजरकडे" },
} satisfies Record<string, Entry>;

export type TextKey = keyof typeof STRINGS;

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

export const useLangStore = create<LangState>()(
  persist(
    (set) => ({
      lang: "en",
      setLang: (lang) => set({ lang }),
    }),
    // Rehydrated after mount so the server-rendered English markup still matches.
    { name: "railvoice-lang", skipHydration: true }
  )
);

export function useT() {
  const lang = useLangStore((s) => s.lang);
  return (key: TextKey): string => STRINGS[key]?.[lang];
}

export function stationName(
  station: { name: string; name_hi?: string | null; name_mr?: string | null },
  lang: Lang
) {
  if (lang === "hi") return station.name_hi || station.name;
  if (lang === "mr") return station.name_mr || station.name;
  return station.name;
}
