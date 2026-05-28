const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Hej Assistant Team";
pres.title = "Hej Assistant — AI Commercial Briefing for IKEA Store Managers";

// === IKEA brand colours ===
const IKEA_BLUE = "0058A3";
const IKEA_YELLOW = "FFDA1A";
const IKEA_DARK = "111111";
const WHITE = "FFFFFF";
const LIGHT_GREY = "F5F5F5";
const MID_GREY = "929292";
const TEAL = "0A6E5C";
const PURPLE = "5B2D8E";
const BROWN = "8B6914";

const FONT = "Noto IKEA Latin";
const FONT_FALLBACK = "Arial";

// Paths
const ROOT = __dirname;
const LOGO = path.join(ROOT, "Ikea_logo.svg.png");
const ARCH_IMG = path.join(ROOT, "assets", "architecture-system.png");
const TARGET_IMG = path.join(ROOT, "image001.png");
const SCREENSHOT = path.join(ROOT, "assets", "screenshot-briefing.png"); // may not exist

// Helper: IKEA-blue footer bar
function addFooter(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.1, w: 10, h: 0.525,
    fill: { color: IKEA_BLUE }
  });
  slide.addText(text, {
    x: 0.5, y: 5.15, w: 9, h: 0.45,
    fontSize: 9, fontFace: FONT_FALLBACK, color: WHITE, valign: "middle"
  });
}

// Helper: section title badge
function addSectionBadge(slide, label, bgColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.35,
    fill: { color: bgColor || IKEA_BLUE }
  });
  slide.addText(label, {
    x: 0.5, y: 0, w: 9, h: 0.35,
    fontSize: 8, fontFace: FONT_FALLBACK, color: WHITE, bold: true,
    charSpacing: 3, valign: "middle"
  });
}

// ============================================================
// SLIDE 1 — Title Slide
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: IKEA_BLUE };

  // IKEA logo
  slide.addImage({ path: LOGO, x: 0.5, y: 0.4, w: 1.2, h: 1.0 });

  // Title
  slide.addText("Hej Assistant", {
    x: 0.5, y: 1.6, w: 9, h: 1.2,
    fontSize: 44, fontFace: FONT_FALLBACK, color: IKEA_YELLOW, bold: true, margin: 0
  });

  // Subtitle
  slide.addText("AI-powered daily commercial briefing\nfor IKEA store managers", {
    x: 0.5, y: 2.7, w: 7, h: 1.0,
    fontSize: 20, fontFace: FONT_FALLBACK, color: WHITE, margin: 0
  });

  // Bottom line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.3, w: 3, h: 0.04, fill: { color: IKEA_YELLOW }
  });

  slide.addText("RiverHacks Hackathon 2025", {
    x: 0.5, y: 4.5, w: 5, h: 0.5,
    fontSize: 14, fontFace: FONT_FALLBACK, color: WHITE, italic: true, margin: 0
  });
}

// ============================================================
// SLIDE 2 — The Problem
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "THE CHALLENGE");

  slide.addText("Store managers are overwhelmed by data", {
    x: 0.5, y: 0.7, w: 9, h: 0.7,
    fontSize: 28, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  slide.addText("Every morning, IKEA store managers must check multiple systems to understand their store's commercial performance. This wastes time and creates blind spots.", {
    x: 0.5, y: 1.4, w: 9, h: 0.8,
    fontSize: 14, fontFace: FONT_FALLBACK, color: "555555", margin: 0
  });

  // Pain points as cards
  const cards = [
    { icon: "5+", title: "Systems to check", desc: "Sales, stock, forecasts, promotions, margins — scattered across tools" },
    { icon: "45m", title: "Minutes lost daily", desc: "Manual data gathering before the store even opens" },
    { icon: "0", title: "Proactive alerts", desc: "No system tells managers what to focus on today" },
  ];

  cards.forEach((card, i) => {
    const x = 0.5 + i * 3.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.5, w: 2.8, h: 2.2,
      fill: { color: LIGHT_GREY },
      shadow: { type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.08 }
    });
    slide.addText(card.icon, {
      x, y: 2.6, w: 2.8, h: 0.7,
      fontSize: 36, fontFace: FONT_FALLBACK, color: IKEA_BLUE, bold: true, align: "center", valign: "middle"
    });
    slide.addText(card.title, {
      x: x + 0.2, y: 3.3, w: 2.4, h: 0.4,
      fontSize: 13, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, align: "center"
    });
    slide.addText(card.desc, {
      x: x + 0.2, y: 3.7, w: 2.4, h: 0.8,
      fontSize: 10, fontFace: FONT_FALLBACK, color: "666666", align: "center"
    });
  });

  addFooter(slide, "Hej Assistant  |  RiverHacks 2025");
}

// ============================================================
// SLIDE 3 — Our Solution
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: IKEA_BLUE };

  slide.addText("One AI co-worker. One morning briefing.", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 28, fontFace: FONT_FALLBACK, color: IKEA_YELLOW, bold: true, margin: 0
  });

  slide.addText("Hej Assistant generates a daily commercial briefing powered by AI — combining sales, stock, margin, and forecast data into actionable insights.", {
    x: 0.5, y: 1.3, w: 9, h: 0.7,
    fontSize: 14, fontFace: FONT_FALLBACK, color: WHITE, margin: 0
  });

  // Three capability pillars
  const pillars = [
    { title: "Daily Briefing", desc: "AI-generated report with KPIs, trends, and prioritised actions. Export to PDF.", color: "0D8A73" },
    { title: "Ask Me Anything", desc: "Chat with your store data. What-if scenarios, deep dives, follow-ups.", color: "0D8A73" },
    { title: "Proactive Alerts", desc: "Auto-surfaced critical issues on page load. No manual checks needed.", color: "0D8A73" },
  ];

  pillars.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.3, w: 2.8, h: 2.5,
      fill: { color: p.color }
    });
    slide.addText(p.title, {
      x: x + 0.2, y: 2.5, w: 2.4, h: 0.5,
      fontSize: 16, fontFace: FONT_FALLBACK, color: IKEA_YELLOW, bold: true
    });
    slide.addText(p.desc, {
      x: x + 0.2, y: 3.0, w: 2.4, h: 1.5,
      fontSize: 11, fontFace: FONT_FALLBACK, color: WHITE
    });
  });

  addFooter(slide, "Hej Assistant  |  Three core capabilities");
}

// ============================================================
// SLIDE 4 — Live Demo Screenshot
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "LIVE DEMO");

  slide.addText("The Store Manager Experience", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  // Callouts for UI features
  const features = [
    "Store selector with 8 IKEA locations",
    "Real-time KPI snapshot cards",
    "Proactive alerts banner with severity levels",
    "AI-generated briefing with PDF export",
    "IKEA Skapa design language",
  ];

  slide.addText(
    features.map((f, i) => ({
      text: f,
      options: { bullet: true, breakLine: i < features.length - 1, fontSize: 12, color: "444444" }
    })),
    { x: 0.5, y: 1.3, w: 4, h: 2.5, fontFace: FONT_FALLBACK, paraSpaceAfter: 6 }
  );

  // Architecture diagram as visual (right side)
  slide.addImage({
    path: ARCH_IMG,
    x: 4.8, y: 1.0, w: 4.8, h: 3.5,
    shadow: { type: "outer", blur: 6, offset: 3, angle: 135, color: "000000", opacity: 0.1 }
  });

  addFooter(slide, "Hej Assistant  |  Built with FastAPI + Claude Sonnet 4.6 + Skapa Design");
}

// ============================================================
// SLIDE 5 — System Architecture
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "SYSTEM ARCHITECTURE");

  slide.addText("How It Works", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  // Target architecture image (original vision)
  slide.addImage({
    path: TARGET_IMG,
    x: 0.3, y: 1.4, w: 4.5, h: 3.4,
  });

  slide.addText("Target Vision", {
    x: 0.3, y: 4.7, w: 4.5, h: 0.3,
    fontSize: 9, fontFace: FONT_FALLBACK, color: MID_GREY, align: "center", italic: true
  });

  // Current system diagram
  slide.addImage({
    path: ARCH_IMG,
    x: 5.2, y: 1.4, w: 4.5, h: 3.4,
  });

  slide.addText("Current Implementation", {
    x: 5.2, y: 4.7, w: 4.5, h: 0.3,
    fontSize: 9, fontFace: FONT_FALLBACK, color: MID_GREY, align: "center", italic: true
  });

  addFooter(slide, "Hej Assistant  |  10 of 11 target components built");
}

// ============================================================
// SLIDE 6 — Technology Stack
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "TECHNOLOGY", PURPLE);

  slide.addText("Built for Speed, Quality, and IKEA Identity", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 22, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  // Tech stack grid (2x3)
  const stack = [
    { title: "Claude Sonnet 4.6", desc: "LLM with tool-calling.\n20 tools, 10-round loop,\ncritic-refine pipeline.", color: PURPLE },
    { title: "FastAPI + Python", desc: "22 REST endpoints.\nAsync, lightweight,\nsingle deployable unit.", color: IKEA_BLUE },
    { title: "Skapa Design", desc: "IKEA design tokens.\nNoto IKEA font.\nBrand-native UI.", color: TEAL },
    { title: "pandas Analytics", desc: "450K+ rows analysed.\n17 analysis functions.\nReal-time aggregation.", color: BROWN },
    { title: "Alert Scheduler", desc: "Background refresh every\n30 min. Pre-warmed\ninsights cache per store.", color: "CC5500" },
    { title: "Railway Deploy", desc: "One-click deployment.\nHealth checks, auto-scale.\nEnvironment config.", color: "333333" },
  ];

  stack.forEach((item, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 3.1;
    const y = 1.5 + row * 1.9;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.8, h: 1.6,
      fill: { color: item.color }
    });
    slide.addText(item.title, {
      x: x + 0.15, y: y + 0.1, w: 2.5, h: 0.4,
      fontSize: 14, fontFace: FONT_FALLBACK, color: IKEA_YELLOW, bold: true, margin: 0
    });
    slide.addText(item.desc, {
      x: x + 0.15, y: y + 0.5, w: 2.5, h: 1.0,
      fontSize: 10, fontFace: FONT_FALLBACK, color: WHITE, margin: 0
    });
  });

  addFooter(slide, "Hej Assistant  |  Technology Stack");
}

// ============================================================
// SLIDE 7 — The Agent: How It Thinks
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "AI AGENT PROCESS");

  slide.addText("How the AI Agent Reasons", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  // Process flow: numbered steps
  const steps = [
    { n: "1", title: "User Query", desc: "Store manager asks a question or requests a briefing" },
    { n: "2", title: "Tool Selection", desc: "Claude analyses intent and selects from 20 analysis tools" },
    { n: "3", title: "Data Analysis", desc: "Tools query sales, stock, margin, and forecast data" },
    { n: "4", title: "Synthesis", desc: "Claude combines results into IKEA-tone narrative" },
    { n: "5", title: "Validation", desc: "Article references and numbers are verified" },
    { n: "6", title: "Response", desc: "Actionable insights delivered to the manager" },
  ];

  steps.forEach((step, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 3.1;
    const y = 1.5 + row * 1.8;

    // Number circle
    slide.addShape(pres.shapes.OVAL, {
      x: x, y: y, w: 0.45, h: 0.45,
      fill: { color: IKEA_BLUE }
    });
    slide.addText(step.n, {
      x: x, y: y, w: 0.45, h: 0.45,
      fontSize: 16, fontFace: FONT_FALLBACK, color: WHITE, bold: true, align: "center", valign: "middle"
    });

    slide.addText(step.title, {
      x: x + 0.55, y: y, w: 2.2, h: 0.4,
      fontSize: 14, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
    });
    slide.addText(step.desc, {
      x: x + 0.55, y: y + 0.4, w: 2.2, h: 0.7,
      fontSize: 10, fontFace: FONT_FALLBACK, color: "666666", margin: 0
    });

    // Arrow between steps (horizontal)
    if (col < 2) {
      slide.addShape(pres.shapes.LINE, {
        x: x + 2.8, y: y + 0.22, w: 0.3, h: 0,
        line: { color: MID_GREY, width: 1.5, endArrowType: "triangle" }
      });
    }
  });

  // Tool categories
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.3, w: 9, h: 0.7,
    fill: { color: LIGHT_GREY }
  });
  slide.addText([
    { text: "20 Tools: ", options: { bold: true, color: IKEA_DARK } },
    { text: "Sales (5) + Stock (4) + Margin (4) + Actions (1) + What-If (3) + Insights (1) + Context (1) + Memory (1)", options: { color: "555555" } },
  ], {
    x: 0.7, y: 4.35, w: 8.6, h: 0.6,
    fontSize: 11, fontFace: FONT_FALLBACK, valign: "middle"
  });

  addFooter(slide, "Hej Assistant  |  Agent Loop: up to 10 tool-calling rounds per request");
}

// ============================================================
// SLIDE 8 — Data & Quality
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "DATA & TESTING", TEAL);

  slide.addText("Data Foundation & Quality Assurance", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  // Left column: Data
  slide.addText("Data", {
    x: 0.5, y: 1.4, w: 4, h: 0.4,
    fontSize: 16, fontFace: FONT_FALLBACK, color: TEAL, bold: true, margin: 0
  });

  const dataRows = [
    ["Sales", "363,000 rows", "Transactions per article per store per day"],
    ["Forecast", "87,000 rows", "Demand predictions with accuracy tracking"],
    ["Stock", "87,000 rows", "Availability, OOS, burn rates"],
    ["Products", "30 articles", "HFB, series, colours, descriptions"],
    ["Stores", "8 IKEA locations", "Berlin, Amsterdam, Stockholm, ..."],
  ];

  slide.addTable(
    [
      [
        { text: "Source", options: { bold: true, color: WHITE, fill: { color: TEAL } } },
        { text: "Volume", options: { bold: true, color: WHITE, fill: { color: TEAL } } },
        { text: "Content", options: { bold: true, color: WHITE, fill: { color: TEAL } } },
      ],
      ...dataRows.map(r => r.map(c => ({ text: c, options: { fontSize: 10, color: "333333" } })))
    ],
    {
      x: 0.5, y: 1.8, w: 4.3, h: 2.5,
      fontSize: 10, fontFace: FONT_FALLBACK,
      border: { pt: 0.5, color: "DDDDDD" },
      colW: [0.9, 1.2, 2.2],
      autoPage: false,
      rowH: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
    }
  );

  // Right column: Testing & Validation
  slide.addText("Quality Assurance", {
    x: 5.3, y: 1.4, w: 4, h: 0.4,
    fontSize: 16, fontFace: FONT_FALLBACK, color: TEAL, bold: true, margin: 0
  });

  const qaItems = [
    { text: "Article reference validator", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "Number reasonableness checks", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "Critic-refine-evaluate loop for reports", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "What-if price elasticity evaluation", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "Mixed date format auto-detection", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "Session isolation per user", options: { bullet: true, breakLine: true, fontSize: 11, color: "444444" } },
    { text: "Pre-warmed insights cache (no cold starts)", options: { bullet: true, fontSize: 11, color: "444444" } },
  ];

  slide.addText(qaItems, {
    x: 5.3, y: 1.8, w: 4.2, h: 2.5,
    fontFace: FONT_FALLBACK, paraSpaceAfter: 4
  });

  // Key stats bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.5, w: 9, h: 0.5,
    fill: { color: TEAL }
  });
  slide.addText("450K+ data rows  |  22 API endpoints  |  20 LLM tools  |  8 stores  |  Full 2024 calendar year", {
    x: 0.7, y: 4.5, w: 8.6, h: 0.5,
    fontSize: 12, fontFace: FONT_FALLBACK, color: WHITE, bold: true, align: "center", valign: "middle"
  });

  addFooter(slide, "Hej Assistant  |  Data & Quality");
}

// ============================================================
// SLIDE 9 — Implementation Status
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "IMPLEMENTATION STATUS");

  slide.addText("10 of 11 Target Components Built", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  const statusRows = [
    ["Store manager interface", "Built", "HTML/CSS/JS with Skapa design, 3 tabs"],
    ["LLM agent orchestrator", "Built", "Claude tool-calling, 20 tools, critic-refine"],
    ["Q&A engine", "Built", "Conversational Q&A with store context"],
    ["Analysis sparring", "Built", "Price, availability, demand what-if (via chat)"],
    ["Proactive insights", "Built", "Auto-surfaced alerts, 30-min refresh"],
    ["Conversation memory", "Built", "Session history + persistent preferences"],
    ["Analytics tools", "Built", "17 analysis functions (sales/stock/margin)"],
    ["Alert scheduler", "Built", "Background refresh, pre-warmed cache"],
    ["Forecast data store", "Built", "CSV-based demand and accuracy data"],
    ["External context", "Built", "19 holidays, 12 promos, seasonal patterns"],
    ["Vector knowledge base", "Roadmap", "Embeddings, SOPs, document retrieval"],
  ];

  slide.addTable(
    [
      [
        { text: "Component", options: { bold: true, color: WHITE, fill: { color: IKEA_BLUE } } },
        { text: "Status", options: { bold: true, color: WHITE, fill: { color: IKEA_BLUE } } },
        { text: "Implementation", options: { bold: true, color: WHITE, fill: { color: IKEA_BLUE } } },
      ],
      ...statusRows.map(r => [
        { text: r[0], options: { fontSize: 9, color: "333333", bold: true } },
        { text: r[1], options: { fontSize: 9, color: r[1] === "Built" ? TEAL : "CC5500", bold: true } },
        { text: r[2], options: { fontSize: 9, color: "555555" } },
      ])
    ],
    {
      x: 0.5, y: 1.3, w: 9, h: 3.8,
      fontSize: 9, fontFace: FONT_FALLBACK,
      border: { pt: 0.5, color: "DDDDDD" },
      colW: [2.2, 0.8, 6],
      autoPage: false,
      rowH: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
    }
  );

  addFooter(slide, "Hej Assistant  |  91% of target architecture implemented");
}

// ============================================================
// SLIDE 10 — Future Potential
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  addSectionBadge(slide, "FUTURE POTENTIAL", "CC5500");

  slide.addText("From Prototype to Platform", {
    x: 0.5, y: 0.6, w: 9, h: 0.6,
    fontSize: 24, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, margin: 0
  });

  slide.addText("This hackathon prototype demonstrates what a production-ready AI assistant for IKEA retail could look like. The path forward:", {
    x: 0.5, y: 1.2, w: 9, h: 0.5,
    fontSize: 12, fontFace: FONT_FALLBACK, color: "555555", margin: 0
  });

  // Roadmap items
  const roadmap = [
    { priority: "HIGH", title: "Vector Knowledge Base", desc: "Embed SOPs, playbooks, and corporate guidelines for RAG-based retrieval. Enables answers grounded in IKEA documentation.", color: "CC0000" },
    { priority: "HIGH", title: "Real Data Integration", desc: "Connect to live IKEA data sources (sales APIs, inventory systems, promotion calendars) instead of CSV snapshots.", color: "CC0000" },
    { priority: "MED", title: "User Authentication", desc: "Store-level login for personalised preferences, audit trails, and role-based access control.", color: "CC8800" },
    { priority: "MED", title: "Live External APIs", desc: "Real-time holiday calendars, weather data, and campaign management system integration.", color: "CC8800" },
    { priority: "LOW", title: "Multi-language", desc: "Localise UI and AI responses per store region (Swedish, Dutch, German, etc.)", color: TEAL },
    { priority: "LOW", title: "Chart Visualisations", desc: "Interactive charts for trend analysis, comparisons, and data exploration.", color: TEAL },
  ];

  roadmap.forEach((item, i) => {
    const y = 1.9 + i * 0.55;

    // Priority badge
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 0.6, h: 0.4,
      fill: { color: item.color }
    });
    slide.addText(item.priority, {
      x: 0.5, y, w: 0.6, h: 0.4,
      fontSize: 7, fontFace: FONT_FALLBACK, color: WHITE, bold: true, align: "center", valign: "middle"
    });

    slide.addText(item.title, {
      x: 1.2, y, w: 2.5, h: 0.4,
      fontSize: 12, fontFace: FONT_FALLBACK, color: IKEA_DARK, bold: true, valign: "middle", margin: 0
    });
    slide.addText(item.desc, {
      x: 3.7, y, w: 5.8, h: 0.4,
      fontSize: 10, fontFace: FONT_FALLBACK, color: "666666", valign: "middle", margin: 0
    });
  });

  // Vision statement
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.3, w: 9, h: 0.7,
    fill: { color: IKEA_BLUE }
  });
  slide.addText("Vision: Every IKEA store manager starts their day with an AI co-worker that knows their store, anticipates problems, and recommends actions.", {
    x: 0.7, y: 4.35, w: 8.6, h: 0.6,
    fontSize: 12, fontFace: FONT_FALLBACK, color: WHITE, italic: true, align: "center", valign: "middle"
  });

  addFooter(slide, "Hej Assistant  |  Roadmap");
}

// ============================================================
// SLIDE 11 — Closing
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: IKEA_BLUE };

  slide.addImage({ path: LOGO, x: 4.15, y: 0.8, w: 1.7, h: 1.4 });

  slide.addText("Tack!", {
    x: 0.5, y: 2.3, w: 9, h: 1.0,
    fontSize: 48, fontFace: FONT_FALLBACK, color: IKEA_YELLOW, bold: true, align: "center"
  });

  slide.addText("Hej Assistant — making every store morning smarter.", {
    x: 1, y: 3.3, w: 8, h: 0.6,
    fontSize: 16, fontFace: FONT_FALLBACK, color: WHITE, align: "center", italic: true
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 4.1, w: 3, h: 0.04, fill: { color: IKEA_YELLOW }
  });

  slide.addText("RiverHacks 2025", {
    x: 1, y: 4.3, w: 8, h: 0.5,
    fontSize: 14, fontFace: FONT_FALLBACK, color: WHITE, align: "center"
  });
}

// ============================================================
// SAVE
// ============================================================
const outPath = path.join(ROOT, "assets", "Hej-Assistant-Presentation.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("Saved:", outPath);
}).catch(err => {
  console.error("Error:", err);
});
