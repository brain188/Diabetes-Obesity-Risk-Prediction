import { useState, useDeferredValue } from "react";
import {
  HelpCircle, ChevronDown, ChevronUp, BookOpen, ClipboardList,
  Brain, FileText, Shield, Search, ExternalLink, Mail,
  Zap, BookMarked, PlayCircle, MessageSquare,
} from "lucide-react";

interface FaqItem { q: string; a: string }

const SECTIONS = [
  {
    title: "Getting Started",
    icon: BookOpen,
    faqs: [
      { q: "How do I register a new patient?", a: "Click 'Register New Patient' on the Patients page or in the sidebar. Fill in the patient's full name, date of birth (must be 18 or older), and sex. Contact info and national ID are optional fields." },
      { q: "What are the minimum system requirements?", a: "The DSS runs in any modern browser (Chrome, Firefox, Safari, Edge). No installation is needed. A stable internet connection is required as all data is processed on the server." },
      { q: "How do I navigate between modules?", a: "Use the left sidebar to switch between Patients, Screenings, Predictions, Reports, and Analytics. The active module is highlighted in blue." },
      { q: "How do I log out?", a: "Click your profile avatar in the top-right corner and select 'Sign Out'. Your session will be cleared and you will be redirected to the login page." },
    ],
  },
  {
    title: "Screening & Prediction",
    icon: ClipboardList,
    faqs: [
      { q: "What data do I need for a screening?", a: "You need the patient's weight (kg), height (m), and answers to six clinical questions: physical activity level, family history of diabetes, previous gestational diabetes, hypertension status, current pregnancy status, and residence type (Urban/Rural)." },
      { q: "How is BMI calculated?", a: "BMI is automatically calculated from weight and height using the formula: BMI = weight (kg) / height² (m²). The category (Normal / Overweight / Obese) is displayed in real time as you type." },
      { q: "Can I enter pregnancy-related fields for male patients?", a: "Yes — is_pregnant and previous_gdm are available for all patients. For males, they default to No (false). The ML model requires these as input features, so keeping them as No for males is medically correct and does not affect prediction quality." },
      { q: "How long does a prediction take?", a: "Typically under 2 seconds. The system runs the CatBoost diabetes classifier and generates SHAP + LIME explanations simultaneously in the background." },
      { q: "What does the risk percentage mean?", a: "It is the model's estimated probability that the patient has diabetes, expressed as a percentage. Thresholds: Low < 34.7%, Moderate 34.7–54.7%, High ≥ 54.7%." },
    ],
  },
  {
    title: "AI Explainability",
    icon: Brain,
    faqs: [
      { q: "What is SHAP?", a: "SHAP (SHapley Additive exPlanations) shows how each clinical feature pushed the prediction up or down relative to the baseline probability. Positive values (red) increase diabetes risk; negative values (green) decrease it. The SHAP values sum to the final probability minus the baseline." },
      { q: "What is LIME?", a: "LIME (Local Interpretable Model-agnostic Explanations) builds a linear approximation around the patient's data point to explain the prediction. It is model-agnostic and provides a complementary, independent view to SHAP." },
      { q: "What is Global Feature Importance?", a: "This shows the overall weight of each feature in the CatBoost model across all training data — it is not specific to any one patient. Features with higher importance have a larger influence on predictions globally." },
      { q: "What do the risk classes mean?", a: "Low: probability < 34.7%. Moderate: 34.7–54.7%. High: ≥ 54.7%. These thresholds were optimised using the Youden-J index on the validation set for maximum sensitivity + specificity trade-off." },
      { q: "Why might SHAP and LIME give slightly different results?", a: "SHAP is exact (Shapley values) while LIME is a local approximation — both are valid but use different mathematical frameworks. Where they agree, you can have high confidence in the explanation." },
    ],
  },
  {
    title: "Reports",
    icon: FileText,
    faqs: [
      { q: "How do I generate a PDF report?", a: "From the Prediction Results page, click 'Download PDF'. The system will generate a PDF containing the patient summary, risk assessment, SHAP explanation, and clinical recommendations. Reports are also accessible from the patient's profile." },
      { q: "Can I download a report multiple times?", a: "Yes. Reports are stored on the server and can be downloaded as many times as needed from the Reports Management page." },
      { q: "What is included in the PDF report?", a: "Patient demographics, screening indicators (BMI, activity level, etc.), diabetes risk class and probability, obesity risk class, SHAP feature contributions, and tailored clinical recommendations with follow-up interval." },
      { q: "Are reports stored permanently?", a: "Reports are retained until deleted by an authorised user. You can manage all reports from the Reports Management page, including viewing, downloading, and deleting." },
    ],
  },
  {
    title: "Security & Privacy",
    icon: Shield,
    faqs: [
      { q: "Is patient data encrypted?", a: "Yes. All data is transmitted over HTTPS (TLS 1.3) and stored in a PostgreSQL database with at-rest encryption. Access tokens expire after 60 minutes and are automatically refreshed." },
      { q: "Who can see patient data?", a: "Healthcare workers can access patients they have registered. Admin accounts have broader access for system management and audit purposes. All data access is logged in the audit trail." },
      { q: "What happens when my session expires?", a: "You will be automatically redirected to the login page. No data is lost — all predictions and patient records are saved to the database before the session expires." },
      { q: "How do I change my password?", a: "Go to Settings → Account tab → Security Settings section. Enter your current password, then set and confirm the new password. The strength indicator will guide you." },
    ],
  },
];

const QUICK_LINKS = [
  { label: "Quick Start Guide", icon: Zap, desc: "Up and running in 5 minutes" },
  { label: "Screening Tutorial", icon: PlayCircle, desc: "Step-by-step video walkthrough" },
  { label: "AI Model Docs", icon: BookMarked, desc: "CatBoost model reference" },
  { label: "Contact Support", icon: MessageSquare, desc: "Reach the project team" },
];

function FaqAccordion({ q, a }: FaqItem) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border/50 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start justify-between gap-4 py-4 text-left"
      >
        <span className="text-sm font-medium text-foreground leading-relaxed">{q}</span>
        <span className="shrink-0 mt-0.5">
          {open
            ? <ChevronUp className="h-4 w-4 text-muted-foreground" />
            : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </span>
      </button>
      {open && (
        <p className="text-sm text-muted-foreground pb-4 leading-relaxed pr-8">{a}</p>
      )}
    </div>
  );
}

export default function HelpCenterPage() {
  const [search, setSearch] = useState("");
  const deferred = useDeferredValue(search.toLowerCase());

  const filtered = SECTIONS.map((s) => ({
    ...s,
    faqs: s.faqs.filter(
      (f) =>
        !deferred ||
        f.q.toLowerCase().includes(deferred) ||
        f.a.toLowerCase().includes(deferred),
    ),
  })).filter((s) => s.faqs.length > 0);

  return (
    <div className="pb-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-xl bg-primary/10">
          <HelpCircle className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Help Center</h1>
          <p className="text-sm text-muted-foreground">Documentation and FAQs for the DiabObesity DSS.</p>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative mb-6">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search documentation…"
          className="w-full pl-11 pr-4 py-3 bg-card border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary shadow-sm"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex gap-6 items-start">
        {/* Main FAQ content */}
        <div className="flex-1 min-w-0 space-y-4">
          {filtered.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-10 text-center">
              <HelpCircle className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">No results for "{search}"</p>
              <p className="text-xs text-muted-foreground mt-1">Try different keywords or browse sections below.</p>
              <button onClick={() => setSearch("")} className="mt-3 text-xs text-primary hover:underline">
                Clear search
              </button>
            </div>
          ) : (
            filtered.map(({ title, icon: Icon, faqs }) => (
              <div key={title} className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-primary/10">
                    <Icon className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <h2 className="text-sm font-semibold text-foreground">{title}</h2>
                  <span className="ml-auto text-xs text-muted-foreground">{faqs.length} articles</span>
                </div>
                <div className="px-6">
                  {faqs.map((f) => <FaqAccordion key={f.q} {...f} />)}
                </div>
              </div>
            ))
          )}

          {/* Contact banner */}
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-foreground">Still need help?</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Contact your system administrator or raise an issue via the project repository.
                </p>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
                <Mail className="h-4 w-4" />Contact Support
              </button>
            </div>
          </div>
        </div>

        {/* Quick links sidebar */}
        <div className="hidden lg:block w-56 shrink-0 space-y-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">Quick Links</h3>
          {QUICK_LINKS.map(({ label, icon: Icon, desc }) => (
            <button
              key={label}
              className="w-full flex items-start gap-3 p-3 rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-primary/5 transition-all text-left group"
            >
              <div className="p-1.5 rounded-lg bg-muted group-hover:bg-primary/10 shrink-0">
                <Icon className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-foreground leading-tight">{label}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{desc}</p>
              </div>
            </button>
          ))}

          <div className="mt-4 p-3 rounded-xl border border-border bg-card space-y-1.5">
            <p className="text-xs font-semibold text-foreground">System Version</p>
            <p className="text-xs text-muted-foreground">DiabObesity DSS v1.0</p>
            <p className="text-xs text-muted-foreground">CatBoost model v1.0</p>
          </div>
        </div>
      </div>
    </div>
  );
}
