import Navbar from "../components/Navbar";
import { useNavigate } from "react-router-dom";
import homeImage from "../assets/home.png";

const features = [
  { icon: "🌱", title: "Soil Analysis", desc: "Understand N, P, K and pH levels instantly." },
  { icon: "🌦️", title: "Weather Insights", desc: "Hyperlocal real-time data for smarter decisions." },
  { icon: "🤖", title: "AI Recommendations", desc: "Precise fertilizer suggestions powered by AI." },
];

const steps = ["Enter Location", "Select Crop", "Analyze Data", "Get Recommendation"];

const Home = () => {
  const navigate = useNavigate();
  const handleStart = () => navigate(localStorage.getItem("token") ? "/recommend" : "/auth");

  return (
    <div className="min-h-screen bg-white font-sans">
      <div className="relative z-50">
        <Navbar />
      </div>

      {/* ── Hero ── */}
      <section className="relative h-screen flex items-center justify-center text-center overflow-hidden">
        <img src={homeImage} alt="Farm" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-950/60 via-emerald-950/70 to-emerald-950/90" />

        <div className="relative z-10 px-6 max-w-2xl mx-auto">
          <span className="inline-block px-4 py-1.5 rounded-full border border-emerald-400/40 bg-emerald-400/10 text-emerald-400 text-xs tracking-widest uppercase font-semibold mb-7">
            AI-Powered Agriculture
          </span>
          <h1 className="text-5xl md:text-7xl font-bold text-white leading-[1.08] mb-5">
            Smarter farms.<br />
            <span className="text-emerald-400 italic">Better yields.</span>
          </h1>
          <p className="text-white/60 text-lg md:text-xl mb-10 leading-relaxed font-light">
            Combine live soil and weather data to get fertilizer recommendations that actually work.
          </p>
          <button
            onClick={handleStart}
            className="inline-flex items-center gap-2 bg-emerald-950 hover:bg-emerald-900 text-white px-8 py-4 rounded-full text-base font-semibold shadow-xl transition hover:-translate-y-0.5 active:scale-95"
          >
            Get Started <span className="text-emerald-400">→</span>
          </button>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-1 text-white/30 text-xs tracking-widest uppercase animate-bounce">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
          Scroll
        </div>
      </section>

      {/* ── Stats band ── */}
      <div className="bg-emerald-950 py-7">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-4 text-center px-6">
          {[["30%", "Yield Increase"], ["7", "Crops Supported"], ["Live", "Weather Data"]].map(([num, label]) => (
            <div key={label}>
              <p className="text-2xl font-bold text-emerald-400">{num}</p>
              <p className="text-xs text-white/40 uppercase tracking-wider mt-1">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Features ── */}
      <section className="py-24 bg-stone-50 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <p className="text-xs tracking-widest uppercase text-emerald-800 font-semibold mb-3">What We Offer</p>
          <h2 className="text-4xl font-bold text-gray-900 mb-14">Powerful Features</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="bg-white rounded-2xl p-8 border border-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 group text-left">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-2xl mb-5">{f.icon}</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="py-24 bg-white px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs tracking-widest uppercase text-emerald-800 font-semibold mb-3">The Process</p>
          <h2 className="text-4xl font-bold text-gray-900 mb-16">How It Works</h2>
          <div className="relative grid grid-cols-4 gap-4">
            <div className="absolute top-6 left-[12%] right-[12%] h-px bg-gray-200 -z-0" />
            {steps.map((s, i) => (
              <div key={s} className="flex flex-col items-center gap-3 relative z-10">
                <div className="w-12 h-12 rounded-full bg-emerald-950 text-white flex items-center justify-center font-bold text-lg shadow-md">
                  {i + 1}
                </div>
                <p className="text-sm font-medium text-gray-700">{s}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA band ── */}
      <section className="bg-emerald-950 py-20 px-6 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_100%,rgba(52,211,153,0.12),transparent_60%)]" />
        <div className="relative z-10 max-w-lg mx-auto">
          <h2 className="text-4xl font-bold text-white mb-4">Ready to improve your yield?</h2>
          <p className="text-white/40 mb-8 text-sm">Start using smart recommendations today — it's free to try.</p>
          <button
            onClick={handleStart}
            className="inline-flex items-center gap-2 bg-emerald-400 hover:bg-emerald-300 text-emerald-950 px-8 py-4 rounded-full text-base font-bold shadow-xl transition hover:-translate-y-0.5 active:scale-95"
          >
            Get Your Recommendation →
          </button>
        </div>
      </section>
    </div>
  );
};

export default Home;