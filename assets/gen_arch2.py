"""Generate a clean, PowerPoint-ready architecture diagram."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 11), dpi=200)
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis("off")
fig.patch.set_facecolor("white")

# Colours (IKEA-inspired)
IKEA_BLUE = "#0058A3"
IKEA_DARK = "#111111"
TEAL = "#0A6E5C"
BROWN = "#8B6914"
GREY_BORDER = "#DFDFDF"


def draw_box(
    x, y, w, h, label, sublabel="", color=IKEA_BLUE, text_color="white", fontsize=9, sublabel_size=7
):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.08",
        facecolor=color,
        edgecolor="none",
        linewidth=0,
        zorder=3,
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(
            x + w / 2,
            y + h / 2 + 0.13,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=text_color,
            zorder=4,
        )
        ax.text(
            x + w / 2,
            y + h / 2 - 0.15,
            sublabel,
            ha="center",
            va="center",
            fontsize=sublabel_size,
            color=text_color,
            alpha=0.85,
            zorder=4,
            style="italic",
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=text_color,
            zorder=4,
        )


def draw_section(x, y, w, h, color="#E8E8E8"):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor=GREY_BORDER,
        linewidth=1.5,
        zorder=1,
        alpha=0.5,
    )
    ax.add_patch(box)


def draw_arrow(x1, y1, x2, y2, color="#999999", lw=1.5):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=lw),
        zorder=2,
    )


# === Title ===
ax.text(
    9,
    10.55,
    "Hej Assistant  --  System Architecture",
    ha="center",
    va="center",
    fontsize=18,
    fontweight="bold",
    color=IKEA_DARK,
)
ax.text(
    9,
    10.15,
    "AI-powered daily commercial briefing for IKEA store managers",
    ha="center",
    va="center",
    fontsize=10,
    color="#666666",
    style="italic",
)

# === LAYER 1: Presentation ===
draw_section(0.4, 8.8, 17.2, 1.1, "#D4E8F7")
ax.text(
    1.0, 9.7, "PRESENTATION", ha="left", fontsize=7, fontweight="bold", color="#4A90C4", zorder=4
)
draw_box(0.8, 9.0, 4.0, 0.7, "Store Manager Interface", "Chat  /  Alerts  /  Dashboard", IKEA_BLUE)
draw_box(5.2, 9.0, 2.8, 0.7, "Skapa Design", "IKEA tokens + fonts", "#3B7CC9")
draw_box(8.4, 9.0, 3.0, 0.7, "Proactive Alerts", "Auto-surfaced on load", "#3B7CC9")
draw_box(11.8, 9.0, 2.5, 0.7, "3 Tabs", "Briefing / Chat / Data", "#3B7CC9")
draw_box(14.7, 9.0, 2.5, 0.7, "PDF Export", "Daily briefing", "#3B7CC9")

# === LAYER 2: LLM Orchestration ===
draw_section(0.4, 6.4, 17.2, 2.1, "#E8D4F7")
ax.text(
    1.0,
    8.3,
    "LLM ORCHESTRATION",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#7B4DAE",
    zorder=4,
)
draw_box(0.8, 7.5, 3.8, 0.7, "LLM Agent Orchestrator", "Reasons, routes, synthesises", "#5B2D8E")
draw_box(5.0, 7.5, 3.2, 0.7, "Claude Sonnet 4.6", "Tool-calling loop x10", "#7B4DAE")
draw_box(8.6, 7.5, 2.8, 0.7, "Memory", "Session + preferences", "#7B4DAE")
draw_box(11.8, 7.5, 2.5, 0.7, "Validators", "Refs / numbers", "#7B4DAE")
draw_box(14.7, 7.5, 2.5, 0.7, "Claude API", "External call", "#1a1a1a")

draw_box(0.8, 6.65, 2.2, 0.55, "20 Tools", "", "#9B6DCE", fontsize=8)
draw_box(
    3.3,
    6.65,
    2.7,
    0.55,
    "System Prompt",
    "IKEA retail expert",
    "#9B6DCE",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    6.3,
    6.65,
    2.7,
    0.55,
    "Report Generator",
    "Critic-refine loop",
    "#9B6DCE",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    9.3,
    6.65,
    2.7,
    0.55,
    "Alert Scheduler",
    "30 min refresh",
    "#9B6DCE",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    12.3, 6.65, 2.5, 0.55, "Session Mgmt", "Per-user state", "#9B6DCE", fontsize=8, sublabel_size=6
)
draw_box(15.1, 6.65, 2.1, 0.55, "FastAPI", "22 endpoints", "#9B6DCE", fontsize=8, sublabel_size=6)

# === LAYER 3: Capability Pillars ===
# Q&A Engine
draw_section(0.4, 4.0, 5.3, 2.1, "#D4F0E8")
ax.text(3.05, 5.9, "Q&A Engine", ha="center", fontsize=10, fontweight="bold", color=TEAL, zorder=4)
draw_box(0.7, 5.05, 4.7, 0.6, "Answers ops questions", "", TEAL, fontsize=8)
draw_box(
    0.7,
    4.25,
    4.7,
    0.6,
    "Conversation Memory",
    "Session + preferences",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# Analysis Sparring
draw_section(6.1, 4.0, 5.8, 2.1, "#D4F0E8")
ax.text(
    9.0, 5.9, "Analysis Sparring", ha="center", fontsize=10, fontweight="bold", color=TEAL, zorder=4
)
draw_box(6.4, 5.05, 5.2, 0.6, "What-if / Forecasts / Deviation", "", TEAL, fontsize=8)
draw_box(
    6.4,
    4.25,
    5.2,
    0.6,
    "Analytics Tools",
    "Sales / Stock / Margin / Actions",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# Proactive Insights
draw_section(12.3, 4.0, 5.3, 2.1, "#D4F0E8")
ax.text(
    14.95,
    5.9,
    "Proactive Insights",
    ha="center",
    fontsize=10,
    fontweight="bold",
    color=TEAL,
    zorder=4,
)
draw_box(12.6, 5.05, 4.7, 0.6, "Auto-surfaced alerts", "", TEAL, fontsize=8)
draw_box(
    12.6,
    4.25,
    4.7,
    0.6,
    "Alert Scheduler",
    "Triggers proactive runs",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# === LAYER 4: Data Layer ===
draw_section(0.4, 1.5, 5.3, 2.2, "#F0E4D0")
ax.text(1.0, 3.5, "DATA STORE", ha="left", fontsize=7, fontweight="bold", color="#8B6914", zorder=4)
draw_box(
    0.7,
    2.6,
    4.7,
    0.7,
    "Sales / Stock / Forecast",
    "5 CSV files  /  450K+ rows",
    BROWN,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    0.7,
    1.75,
    4.7,
    0.6,
    "DataStore (loader.py)",
    "Joins / periods / filters",
    "#A07A1C",
    fontsize=8,
    sublabel_size=6,
)

draw_section(6.1, 1.5, 5.8, 2.2, "#E8E8E8")
ax.text(
    6.7,
    3.5,
    "EXTERNAL CONTEXT",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#484848",
    zorder=4,
)
draw_box(
    6.4,
    2.6,
    5.2,
    0.7,
    "External Context",
    "Holidays / Promos / Seasonal",
    "#484848",
    fontsize=8,
    sublabel_size=6,
)
draw_box(6.4, 1.75, 5.2, 0.6, "19 holidays / 12 promos / 8 regions", "", "#666666", fontsize=7)

draw_section(12.3, 1.5, 5.3, 2.2, "#E8E0E0")
ax.text(
    12.9, 3.5, "KNOWLEDGE BASE", ha="left", fontsize=7, fontweight="bold", color="#888", zorder=4
)
draw_box(
    12.6,
    2.6,
    4.7,
    0.7,
    "Vector Knowledge Base",
    "Embeddings / SOPs / Docs",
    "#AAAAAA",
    fontsize=8,
    sublabel_size=6,
)
draw_box(12.6, 1.75, 4.7, 0.6, "Not yet implemented", "", "#CCCCCC", fontsize=7)

# === Arrows ===
draw_arrow(2.8, 9.0, 2.7, 8.2, IKEA_BLUE, 2.0)
draw_arrow(3.05, 6.65, 3.05, 6.1, "#5B2D8E", 1.5)
draw_arrow(9.0, 6.65, 9.0, 6.1, "#5B2D8E", 1.5)
draw_arrow(14.95, 6.65, 14.95, 6.1, "#5B2D8E", 1.5)
draw_arrow(3.05, 4.25, 3.05, 3.7, TEAL, 1.3)
draw_arrow(9.0, 4.25, 9.0, 3.7, TEAL, 1.3)
draw_arrow(14.95, 4.25, 14.95, 3.7, TEAL, 1.3)

plt.tight_layout(pad=0.3)
plt.savefig(
    "/Users/joost.jansen/Local/agent_framework/challenge_3_riverhacks/assets/architecture-system.png",
    dpi=200,
    bbox_inches="tight",
    facecolor="white",
    edgecolor="none",
)
print("Done")
