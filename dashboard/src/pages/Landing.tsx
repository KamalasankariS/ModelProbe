import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Shield,
  BarChart3,
  GitCompare,
  Zap,
  ArrowRight,
  Package,
  Terminal,
  Eye,
  Brain,
  CheckCircle2,
  Play,
  Search,
  FileCheck,
  ShieldAlert,
} from "lucide-react";

function GitHubSvg({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

function Nav() {
  return (
    <nav className="fixed top-0 inset-x-0 z-50 bg-cream/80 backdrop-blur-md border-b border-sand">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-charcoal rounded-lg flex items-center justify-center">
            <Eye className="w-4 h-4 text-warm-400" />
          </div>
          <span className="font-display font-bold text-charcoal text-lg tracking-tight">
            ModelProbe
          </span>
        </Link>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-charcoal/60">
          <a href="#features" className="hover:text-charcoal transition-colors">
            Features
          </a>
          <a href="#benchmarks" className="hover:text-charcoal transition-colors">
            Benchmarks
          </a>
          <a href="#try-it" className="hover:text-charcoal transition-colors">
            Try It
          </a>
          <a
            href="https://github.com/KamalasankariS/ModelProbe"
            target="_blank"
            rel="noreferrer"
            className="hover:text-charcoal transition-colors"
          >
            GitHub
          </a>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="hidden sm:inline-flex text-sm font-medium text-charcoal/70 hover:text-charcoal transition-colors"
          >
            Dashboard
          </Link>
          <a
            href="#try-it"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-warm-400 text-charcoal font-semibold text-sm rounded-full hover:bg-warm-300 transition-colors shadow-sm"
          >
            Try It Live
          </a>
        </div>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 grain">
      <div className="relative z-10 max-w-6xl mx-auto px-6">
        <motion.div
          initial="hidden"
          animate="visible"
          className="max-w-3xl"
        >
          <motion.div variants={fadeUp} custom={0} className="mb-6">
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-warm-50 border border-warm-200 rounded-full text-xs font-semibold text-warm-700 tracking-wide uppercase">
              <Package className="w-3 h-3" />
              v0.1.1 on PyPI
            </span>
          </motion.div>
          <motion.h1
            variants={fadeUp}
            custom={1}
            className="font-display font-black text-charcoal text-5xl md:text-6xl lg:text-7xl leading-[1.05] tracking-tight"
          >
            Know when your
            <br />
            AI is{" "}
            <span className="relative">
              <span className="relative z-10">lying</span>
              <span className="absolute bottom-1 left-0 right-0 h-3 bg-warm-200/60 -z-0 rounded-sm" />
            </span>
          </motion.h1>
          <motion.p
            variants={fadeUp}
            custom={2}
            className="mt-6 text-lg md:text-xl text-charcoal/60 leading-relaxed max-w-xl"
          >
            Production-grade evaluation and regression testing for LLMs.
            Detect hallucinations, enforce output quality, and catch regressions
            before they hit users.
          </motion.p>
          <motion.div
            variants={fadeUp}
            custom={3}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <a
              href="#try-it"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-warm-400 text-charcoal font-semibold text-sm rounded-full hover:bg-warm-300 transition-colors shadow-md"
            >
              Try It Live
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="#get-started"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-charcoal font-semibold text-sm rounded-full border border-charcoal/10 hover:border-charcoal/20 transition-colors"
            >
              Install via pip
            </a>
          </motion.div>
        </motion.div>

        {/* terminal preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-16 md:mt-20 max-w-2xl"
        >
          <div className="bg-charcoal rounded-xl shadow-2xl overflow-hidden border border-charcoal/20">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10">
              <div className="w-3 h-3 rounded-full bg-red-400/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-400/80" />
              <div className="w-3 h-3 rounded-full bg-green-400/80" />
              <span className="ml-2 text-xs text-white/40 font-mono">terminal</span>
            </div>
            <div className="p-5 font-mono text-sm leading-relaxed">
              <p className="text-white/40">$ pip install modelprobe</p>
              <p className="text-white/40 mt-3">$ modelprobe run suite.json</p>
              <p className="mt-3 text-white/90">
                <span className="text-warm-400">Suite:</span> production-evals
              </p>
              <p className="text-white/90">
                <span className="text-warm-400">Model:</span> gpt-4o
              </p>
              <p className="mt-2 text-white/90">
                <span className="text-green-400">PASS</span>{" "}
                exact_match &middot; score: 1.0
              </p>
              <p className="text-white/90">
                <span className="text-green-400">PASS</span>{" "}
                json_schema &middot; score: 1.0
              </p>
              <p className="text-white/90">
                <span className="text-red-400">FAIL</span>{" "}
                hallucination &middot; score: 0.42
              </p>
              <p className="text-white/90">
                <span className="text-green-400">PASS</span>{" "}
                contains &middot; score: 1.0
              </p>
              <p className="mt-3 text-white/60">
                Results: <span className="text-green-400">3 passed</span>
                {" "}&middot;{" "}
                <span className="text-red-400">1 failed</span>
                {" "}&middot; Pass rate: 75%
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function SocialProof() {
  const stats = [
    { value: "8", label: "Evaluator Types" },
    { value: "66%", label: "Code Coverage" },
    { value: "0-17%", label: "Hallucination Detection" },
    { value: "132+", label: "Tests Passing" },
  ];
  return (
    <section className="py-16 border-y border-sand bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="text-3xl md:text-4xl font-bold text-charcoal tracking-tight">
                {s.value}
              </div>
              <div className="mt-1 text-sm text-charcoal/50 font-medium">
                {s.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function About() {
  return (
    <section className="py-20 md:py-28 bg-cream" id="about">
      <div className="max-w-6xl mx-auto px-6 grid md:grid-cols-2 gap-16 items-center">
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-display font-bold text-charcoal text-3xl md:text-4xl leading-tight">
            Built for engineers who
            <br />
            ship AI to production
          </h2>
          <p className="mt-5 text-charcoal/60 leading-relaxed">
            ModelProbe is an open-source Python framework that treats AI outputs like
            software &mdash; testable, measurable, and regression-tracked. Define evaluation
            suites in JSON, run them in CI, and get alerted when quality drops.
          </p>
          <div className="mt-8 space-y-4">
            {[
              "pip install and go — no SaaS, no API keys, no cost",
              "Novel hallucination detection via self-consistency & knowledge graphs",
              "Works with any model — OpenAI, Ollama, Anthropic, local LLMs",
            ].map((item) => (
              <div key={item} className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-warm-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-charcoal/70">{item}</span>
              </div>
            ))}
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, x: 24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl border border-sand p-8 shadow-sm"
        >
          <div className="font-mono text-sm text-charcoal/80 leading-relaxed whitespace-pre">{`{
  "suite": "production-evals",
  "tests": [
    {
      "name": "format-check",
      "eval_type": "json_schema",
      "output": "{{model_output}}",
      "config": {
        "schema": {
          "type": "object",
          "required": ["answer"]
        }
      }
    },
    {
      "name": "hallucination-guard",
      "eval_type": "hallucination",
      "output": "{{model_output}}",
      "config": {
        "strategy": "consistency",
        "samples": 5
      }
    }
  ]
}`}</div>
        </motion.div>
      </div>
    </section>
  );
}

function Features() {
  const features = [
    {
      icon: Brain,
      title: "Hallucination Detection",
      description:
        "Two novel strategies: self-consistency sampling (Wang et al. 2022) and Wikidata knowledge graph verification. Catch factual errors before users do.",
    },
    {
      icon: Shield,
      title: "8 Built-in Evaluators",
      description:
        "Exact match, contains, regex, JSON schema, hallucination, toxicity, similarity, and LLM judge. Each returns a normalized score with reasoning.",
    },
    {
      icon: GitCompare,
      title: "Regression Testing",
      description:
        "Run evaluation suites in CI/CD. Track pass rates across model versions. Get alerted when a model update causes quality to drop.",
    },
    {
      icon: BarChart3,
      title: "Visual Dashboard",
      description:
        "Built-in web UI with suite overview, run comparison, trend charts, and a live Playground for interactive evaluation.",
    },
    {
      icon: Zap,
      title: "Zero Cost, Zero Vendor Lock-in",
      description:
        "Fully open-source. No SaaS fees, no API keys needed. Run locally with Ollama or connect to any provider.",
    },
    {
      icon: Terminal,
      title: "CLI + Python SDK",
      description:
        "pip install modelprobe. Define suites in JSON, run from terminal or import in Python. Ships as a single pip package.",
    },
  ];

  return (
    <section className="py-20 md:py-28 bg-white" id="features">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-display font-bold text-charcoal text-3xl md:text-4xl">
            Everything you need to trust your AI
          </h2>
          <p className="mt-4 text-charcoal/50 max-w-lg mx-auto">
            A complete evaluation toolkit — from quick checks to deep hallucination analysis.
          </p>
        </motion.div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="group bg-cream/50 border border-sand rounded-xl p-6 hover:border-warm-300 hover:shadow-sm transition-all"
            >
              <div className="w-10 h-10 bg-warm-50 border border-warm-200 rounded-lg flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-warm-600" />
              </div>
              <h3 className="font-semibold text-charcoal text-base">{f.title}</h3>
              <p className="mt-2 text-sm text-charcoal/50 leading-relaxed">
                {f.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Benchmarks() {
  const models = [
    {
      name: "gemma3:4b",
      type: "Small generalist",
      scores: { math: 83, factual: 75, instruction: 92, code: 58, hallucination: 83 },
      overall: 78,
    },
    {
      name: "llama3",
      type: "Mid-size generalist",
      scores: { math: 92, factual: 83, instruction: 100, code: 75, hallucination: 92 },
      overall: 88,
    },
    {
      name: "codegemma:7b",
      type: "Code specialist",
      scores: { math: 75, factual: 67, instruction: 83, code: 92, hallucination: 75 },
      overall: 78,
    },
  ];
  const categories = ["math", "factual", "instruction", "code", "hallucination"] as const;

  return (
    <section className="py-20 md:py-28 bg-cream" id="benchmarks">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-display font-bold text-charcoal text-3xl md:text-4xl">
            Real benchmarks, real models
          </h2>
          <p className="mt-4 text-charcoal/50 max-w-lg mx-auto">
            60 test cases across 5 categories, evaluated against 3 local Ollama models.
            No cherry-picked results.
          </p>
        </motion.div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-charcoal/10">
                <th className="text-left py-3 px-4 font-semibold text-charcoal">Model</th>
                {categories.map((c) => (
                  <th key={c} className="text-center py-3 px-4 font-semibold text-charcoal capitalize">
                    {c}
                  </th>
                ))}
                <th className="text-center py-3 px-4 font-bold text-charcoal">Overall</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <motion.tr
                  key={m.name}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  className="border-b border-sand"
                >
                  <td className="py-4 px-4">
                    <div className="font-mono font-semibold text-charcoal">{m.name}</div>
                    <div className="text-xs text-charcoal/40">{m.type}</div>
                  </td>
                  {categories.map((c) => (
                    <td key={c} className="text-center py-4 px-4">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          m.scores[c] >= 90
                            ? "bg-green-50 text-green-700"
                            : m.scores[c] >= 75
                            ? "bg-warm-50 text-warm-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {m.scores[c]}%
                      </span>
                    </td>
                  ))}
                  <td className="text-center py-4 px-4">
                    <span className="font-bold text-charcoal text-base">{m.overall}%</span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

interface EvalResult {
  passed: boolean;
  score: number;
  reason: string;
  status: string;
  evaluator: string;
  detail?: Record<string, unknown>;
}

const EVAL_TYPES = [
  { value: "exact", label: "Exact Match", icon: FileCheck },
  { value: "contains", label: "Contains", icon: Search },
  { value: "regex", label: "Regex", icon: Terminal },
  { value: "json_schema", label: "JSON Schema", icon: Shield },
  { value: "toxicity", label: "Toxicity", icon: ShieldAlert },
  { value: "similarity", label: "Similarity", icon: BarChart3 },
];

const DEMO_CONFIGS: Record<string, { output: string; expected: string; config: string }> = {
  exact: {
    output: "The capital of France is Paris.",
    expected: "The capital of France is Paris.",
    config: '{"case_sensitive": true}',
  },
  contains: {
    output: "The total invoice amount is $1,250.00 for services rendered in Q3 2024.",
    expected: "",
    config: '{"values": ["invoice", "$1,250.00", "Q3"], "mode": "all"}',
  },
  regex: {
    output: "Order #ORD-2024-78432 has been confirmed and will ship by 2024-12-15.",
    expected: "",
    config: '{"pattern": "ORD-\\\\d{4}-\\\\d{5}"}',
  },
  json_schema: {
    output: '{"name": "Alice", "age": 30, "role": "engineer"}',
    expected: "",
    config: '{"schema": {"type": "object", "required": ["name", "age"], "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}}',
  },
  toxicity: {
    output: "Thank you for your patience. I'd be happy to help you resolve this billing issue. Let me look into your account right away.",
    expected: "",
    config: '{"categories": ["profanity", "hate_speech", "violence", "pii"]}',
  },
  similarity: {
    output: "Paris is the capital city of France, located along the Seine River.",
    expected: "The capital of France is Paris, situated on the banks of the Seine.",
    config: '{"strategy": "tfidf", "threshold": 0.5}',
  },
};

function LivePlayground() {
  const [evalType, setEvalType] = useState("contains");
  const [output, setOutput] = useState(DEMO_CONFIGS["contains"].output);
  const [expected, setExpected] = useState(DEMO_CONFIGS["contains"].expected);
  const [config, setConfig] = useState(DEMO_CONFIGS["contains"].config);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvalResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTypeChange = (type: string) => {
    setEvalType(type);
    const demo = DEMO_CONFIGS[type];
    setOutput(demo.output);
    setExpected(demo.expected);
    setConfig(demo.config);
    setResult(null);
    setError(null);
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    let parsedConfig: Record<string, unknown> = {};
    try {
      parsedConfig = JSON.parse(config);
    } catch {
      setError("Invalid JSON in config");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${window.location.origin}/api/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          output,
          eval_type: evalType,
          expected: expected || null,
          config: parsedConfig,
        }),
      });
      const envelope = await res.json();
      setResult(envelope.data as EvalResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-20 md:py-28 bg-white" id="try-it">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <span className="inline-flex items-center gap-2 px-3 py-1 bg-warm-50 border border-warm-200 rounded-full text-xs font-semibold text-warm-700 tracking-wide uppercase mb-6">
            <Zap className="w-3 h-3" />
            Live Demo
          </span>
          <h2 className="font-display font-bold text-charcoal text-3xl md:text-4xl">
            Try it right now
          </h2>
          <p className="mt-4 text-charcoal/50 max-w-lg mx-auto">
            Pick an evaluator, edit the text, and hit Run. This calls the real ModelProbe API — no install needed.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto"
        >
          {/* Evaluator selector */}
          <div className="flex gap-2 flex-wrap mb-6">
            {EVAL_TYPES.map((ev) => (
              <button
                key={ev.value}
                onClick={() => handleTypeChange(ev.value)}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  evalType === ev.value
                    ? "bg-charcoal text-cream shadow-md"
                    : "bg-sand text-charcoal/60 hover:bg-sand hover:text-charcoal border border-transparent"
                }`}
              >
                <ev.icon className="w-3.5 h-3.5" />
                {ev.label}
              </button>
            ))}
          </div>

          {/* Input area */}
          <div className="bg-cream border border-sand rounded-2xl p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-charcoal/70 mb-1.5">Model Output</label>
              <textarea
                value={output}
                onChange={(e) => setOutput(e.target.value)}
                rows={3}
                className="w-full bg-white border border-sand rounded-xl px-4 py-3 text-sm text-charcoal placeholder-charcoal/30 focus:outline-none focus:border-warm-400 focus:ring-2 focus:ring-warm-400/20 transition-all resize-none"
                placeholder="Paste any model output..."
              />
            </div>

            {(evalType === "exact" || evalType === "similarity") && (
              <div>
                <label className="block text-sm font-medium text-charcoal/70 mb-1.5">Expected Output</label>
                <input
                  value={expected}
                  onChange={(e) => setExpected(e.target.value)}
                  className="w-full bg-white border border-sand rounded-xl px-4 py-3 text-sm text-charcoal placeholder-charcoal/30 focus:outline-none focus:border-warm-400 focus:ring-2 focus:ring-warm-400/20 transition-all"
                  placeholder="Expected output..."
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-charcoal/70 mb-1.5">Config (JSON)</label>
              <textarea
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                rows={2}
                className="w-full bg-white border border-sand rounded-xl px-4 py-3 text-sm text-charcoal font-mono placeholder-charcoal/30 focus:outline-none focus:border-warm-400 focus:ring-2 focus:ring-warm-400/20 transition-all resize-none"
              />
            </div>

            <button
              onClick={handleRun}
              disabled={loading || !output.trim()}
              className="inline-flex items-center gap-2 px-8 py-3 bg-warm-400 text-charcoal font-semibold text-sm rounded-full hover:bg-warm-300 disabled:opacity-40 transition-all shadow-sm"
            >
              <Play className="w-4 h-4" />
              {loading ? "Evaluating..." : "Run Evaluation"}
            </button>
          </div>

          {/* Result */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {result && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-cream border border-sand rounded-2xl p-6"
            >
              <div className="flex items-center gap-4 mb-4">
                <span
                  className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide ${
                    result.status === "pass"
                      ? "bg-green-100 text-green-700"
                      : result.status === "fail"
                      ? "bg-red-100 text-red-700"
                      : "bg-yellow-100 text-yellow-700"
                  }`}
                >
                  {result.status}
                </span>
                <span className="text-3xl font-bold text-charcoal">
                  {(result.score * 100).toFixed(0)}%
                </span>
                <span className="text-sm text-charcoal/40">via {result.evaluator}</span>
              </div>
              <p className="text-sm text-charcoal/60">{result.reason}</p>
              {result.detail && (
                <pre className="mt-4 bg-white border border-sand rounded-xl p-4 text-xs text-charcoal/50 overflow-x-auto font-mono">
                  {JSON.stringify(result.detail, null, 2)}
                </pre>
              )}
            </motion.div>
          )}
        </motion.div>
      </div>
    </section>
  );
}

function GetStarted() {
  return (
    <section className="py-20 md:py-28 bg-charcoal relative grain" id="get-started">
      <div className="relative z-10 max-w-3xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="font-display font-bold text-white text-3xl md:text-4xl">
            Start evaluating in 30 seconds
          </h2>
          <p className="mt-4 text-white/50 max-w-md mx-auto">
            One command. No account. No API key. Works with any model.
          </p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="mt-10 bg-white/5 border border-white/10 rounded-xl p-6 text-left font-mono text-sm max-w-lg mx-auto"
        >
          <p className="text-white/40"># install</p>
          <p className="text-warm-400">pip install modelprobe</p>
          <p className="mt-4 text-white/40"># run your first evaluation</p>
          <p className="text-warm-400">modelprobe run suite.json</p>
          <p className="mt-4 text-white/40"># launch the dashboard</p>
          <p className="text-warm-400">modelprobe start --port 8000</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="mt-10 flex flex-wrap justify-center gap-4"
        >
          <a
            href="https://pypi.org/project/modelprobe/"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-warm-400 text-charcoal font-semibold text-sm rounded-full hover:bg-warm-300 transition-colors"
          >
            <Package className="w-4 h-4" />
            View on PyPI
          </a>
          <a
            href="https://github.com/KamalasankariS/ModelProbe"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-white/10 text-white font-semibold text-sm rounded-full hover:bg-white/15 transition-colors border border-white/10"
          >
            <GitHubSvg className="w-4 h-4" />
            Star on GitHub
          </a>
        </motion.div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-12 bg-cream border-t border-sand">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-charcoal rounded-lg flex items-center justify-center">
            <Eye className="w-3.5 h-3.5 text-warm-400" />
          </div>
          <span className="font-display font-bold text-charcoal text-sm">ModelProbe</span>
        </div>
        <div className="flex items-center gap-6 text-sm text-charcoal/40">
          <a
            href="https://github.com/KamalasankariS/ModelProbe"
            target="_blank"
            rel="noreferrer"
            className="hover:text-charcoal/70 transition-colors"
          >
            GitHub
          </a>
          <a
            href="https://pypi.org/project/modelprobe/"
            target="_blank"
            rel="noreferrer"
            className="hover:text-charcoal/70 transition-colors"
          >
            PyPI
          </a>
          <span>MIT License</span>
        </div>
      </div>
    </footer>
  );
}

export default function Landing() {
  return (
    <div className="landing bg-cream text-charcoal">
      <Nav />
      <Hero />
      <SocialProof />
      <About />
      <Features />
      <Benchmarks />
      <LivePlayground />
      <GetStarted />
      <Footer />
    </div>
  );
}
