"""Generate a clean, PowerPoint-ready architecture diagram."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(16, 10), dpi=200)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis("off")
fig.patch.set_facecolor("white")

# ---- Colours (IKEA-inspired) ----
IKEA_BLUE = "#0058A3"
IKEA_YELLOW = "#FFDA1A"
IKEA_DARK = "#111111"
TEAL = "#0A6E5C"
BROWN = "#8B6914"
GREY_BG = "#F5F5F5"
GREY_BORDER = "#DFDFDF"
WHITE = "#FFFFFF"


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
        transform=ax.transData,
        zorder=3,
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(
            x + w / 2,
            y + h / 2 + 0.12,
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


def draw_section(x, y, w, h, label, color="#E8E8E8"):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor=GREY_BORDER,
        linewidth=1.5,
        transform=ax.transData,
        zorder=1,
        alpha=0.5,
    )
    ax.add_patch(box)
    ax.text(
        x + 0.15,
        y + h - 0.2,
        label,
        ha="left",
        va="top",
        fontsize=8,
        fontweight="bold",
        color="#484848",
        zorder=2,
    )


def draw_arrow(x1, y1, x2, y2, color="#999999", style="->", lw=1.2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw),
        zorder=2,
    )


# ==========================================
# LAYER 1: Store Manager Interface (top)
# ==========================================
draw_section(0.3, 8.5, 15.4, 1.3, "", "#D4E8F7")
draw_box(1, 8.8, 3.5, 0.7, "Store Manager Interface", "Chat · Alerts · Dashboard", IKEA_BLUE)
draw_box(5.2, 8.8, 2.5, 0.7, "Skapa Design", "IKEA tokens + fonts", "#3B7CC9")
draw_box(8.4, 8.8, 2.8, 0.7, "Proactive Alerts", "Auto-surfaced on load", "#3B7CC9")
draw_box(11.9, 8.8, 3.2, 0.7, "3 Tabs", "Briefing · Chat · Data", "#3B7CC9")

# ==========================================
# LAYER 2: LLM Agent Orchestrator
# ==========================================
draw_section(0.3, 6.2, 15.4, 2.0, "", "#E8D4F7")
draw_box(2.5, 7.2, 3.5, 0.7, "LLM Agent Orchestrator", "Reasons, routes, synthesises", "#5B2D8E")
draw_box(6.5, 7.2, 3, 0.7, "Claude Sonnet 4.6", "Tool-calling loop ×10", "#7B4DAE")
draw_box(10, 7.2, 2.5, 0.7, "Memory", "Session + preferences", "#7B4DAE")
draw_box(13, 7.2, 2.2, 0.7, "Validators", "Refs · numbers", "#7B4DAE")

# Tool count badge
draw_box(2.5, 6.5, 2, 0.5, "20 Tools", "", "#9B6DCE", fontsize=8)
draw_box(5, 6.5, 2.5, 0.5, "System Prompt", "IKEA tone", "#9B6DCE", fontsize=8, sublabel_size=6)
draw_box(
    8, 6.5, 2.5, 0.5, "Report Generator", "Critic-refine", "#9B6DCE", fontsize=8, sublabel_size=6
)
draw_box(
    11, 6.5, 2.5, 0.5, "Alert Scheduler", "30 min refresh", "#9B6DCE", fontsize=8, sublabel_size=6
)

# ==========================================
# LAYER 3: Three pillars
# ==========================================
# Q&A Engine
draw_section(0.3, 3.8, 4.7, 2.1, "", "#D4F0E8")
ax.text(2.65, 5.7, "Q&A Engine", ha="center", fontsize=9, fontweight="bold", color=TEAL, zorder=4)
draw_box(0.6, 4.9, 4.1, 0.55, "Answers ops questions", "", TEAL, fontsize=8)
draw_box(
    0.6,
    4.15,
    4.1,
    0.55,
    "Conversation Memory",
    "Session + preferences",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# Analysis Sparring
draw_section(5.3, 3.8, 5.4, 2.1, "", "#D4F0E8")
ax.text(
    8, 5.7, "Analysis Sparring", ha="center", fontsize=9, fontweight="bold", color=TEAL, zorder=4
)
draw_box(5.6, 4.9, 4.8, 0.55, "What-if · Forecasts · Deviation", "", TEAL, fontsize=8)
draw_box(
    5.6,
    4.15,
    4.8,
    0.55,
    "Analytics Tools",
    "Sales · Stock · Margin · Actions",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# Proactive Insights
draw_section(11, 3.8, 4.7, 2.1, "", "#D4F0E8")
ax.text(
    13.35,
    5.7,
    "Proactive Insights",
    ha="center",
    fontsize=9,
    fontweight="bold",
    color=TEAL,
    zorder=4,
)
draw_box(11.3, 4.9, 4.1, 0.55, "Auto-surfaced alerts", "", TEAL, fontsize=8)
draw_box(
    11.3,
    4.15,
    4.1,
    0.55,
    "Alert Scheduler",
    "Triggers proactive runs",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# ==========================================
# LAYER 4: Data stores (bottom)
# ==========================================
draw_section(0.3, 1.5, 4.7, 2.0, "", "#F0E4D0")
draw_box(
    0.6,
    2.5,
    4.1,
    0.65,
    "Forecast Data Store",
    "Demand · Accuracy · Overrides",
    BROWN,
    fontsize=8,
    sublabel_size=6,
)
draw_box(0.6, 1.7, 4.1, 0.55, "5 CSV files · 450K+ rows", "", "#A07A1C", fontsize=7)

draw_section(5.3, 1.5, 5.4, 2.0, "", "#E8E8E8")
draw_box(
    5.6,
    2.5,
    4.8,
    0.65,
    "External Context",
    "Holidays · Promos · Seasonal",
    "#484848",
    fontsize=8,
    sublabel_size=6,
)
draw_box(5.6, 1.7, 4.8, 0.55, "19 holidays · 12 promos · 8 regions", "", "#666666", fontsize=7)

draw_section(11, 1.5, 4.7, 2.0, "", "#E8E8E8")
draw_box(
    11.3,
    2.5,
    4.1,
    0.65,
    "Vector Knowledge Base",
    "Embeddings · SOPs · Docs",
    "#999999",
    fontsize=8,
    sublabel_size=6,
)
draw_box(11.3, 1.7, 4.1, 0.55, "❌ Roadmap", "", "#BBBBBB", fontsize=7)

# ==========================================
# Arrows (vertical flow)
# ==========================================
# UI → Orchestrator
draw_arrow(2.75, 8.8, 4.25, 7.9, IKEA_BLUE, "->", 1.8)

# Orchestrator → Three pillars
draw_arrow(2.65, 6.5, 2.65, 5.9, "#5B2D8E", "->", 1.5)
draw_arrow(8, 6.5, 8, 5.9, "#5B2D8E", "->", 1.5)
draw_arrow(13.35, 6.5, 13.35, 5.9, "#5B2D8E", "->", 1.5)

# Pillars → Data stores
draw_arrow(2.65, 4.15, 2.65, 3.5, TEAL, "->", 1.3)
draw_arrow(8, 4.15, 8, 3.5, TEAL, "->", 1.3)
draw_arrow(13.35, 4.15, 13.35, 3.5, TEAL, "->", 1.3)

# Claude API (external, right side)
draw_box(13.8, 7.75, 1.5, 0.45, "Claude API", "", "#1a1a1a", fontsize=7)
draw_arrow(9.5, 7.55, 13.8, 7.95, "#999", "->", 1.0)

# ==========================================
# Title
# ==========================================
ax.text(
    8,
    9.7,
    "Hej Assistant — System Architecture",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold",
    color=IKEA_DARK,
)
ax.text(
    8,
    9.35,
    "AI-powered daily commercial briefing for IKEA store managers",
    ha="center",
    va="center",
    fontsize=9,
    color="#666666",
    style="italic",
)

plt.tight_layout(pad=0.5)
plt.savefig(
    "/Users/joost.jansen/Local/agent_framework/challenge_3_riverhacks/assets/architecture-system.png",
    dpi=200,
    bbox_inches="tight",
    facecolor="white",
    edgecolor="none",
)
print("Done — saved to assets/architecture-system.png")
