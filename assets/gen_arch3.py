"""Generate a clean, PowerPoint-ready architecture diagram — v3 (full current system)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 13), dpi=200)
ax.set_xlim(0, 20)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor("white")

# Colours (IKEA-inspired)
IKEA_BLUE = "#0058A3"
IKEA_DARK = "#111111"
TEAL = "#0A6E5C"
BROWN = "#8B6914"
GREY_BORDER = "#DFDFDF"
PURPLE = "#5B2D8E"
PURPLE_LIGHT = "#9B6DCE"
GREEN_BG = "#D4F0E8"
BLUE_BG = "#D4E8F7"
PURPLE_BG = "#E8D4F7"
BROWN_BG = "#F0E4D0"
GREY_BG = "#E8E8E8"
ORANGE = "#CC5500"
ORANGE_BG = "#FCEADB"


def draw_box(
    x,
    y,
    w,
    h,
    label,
    sublabel="",
    color=IKEA_BLUE,
    text_color="white",
    fontsize=9,
    sublabel_size=7,
    alpha=1.0,
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
        alpha=alpha,
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(
            x + w / 2,
            y + h / 2 + 0.14,
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
            y + h / 2 - 0.14,
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


def draw_double_arrow(x1, y1, x2, y2, color="#999999", lw=1.5):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color=color, lw=lw),
        zorder=2,
    )


# ======== TITLE ========
ax.text(
    10,
    12.55,
    "Hej Assistant  —  System Architecture",
    ha="center",
    va="center",
    fontsize=20,
    fontweight="bold",
    color=IKEA_DARK,
)
ax.text(
    10,
    12.15,
    "AI-powered daily commercial briefing for IKEA store managers",
    ha="center",
    va="center",
    fontsize=11,
    color="#666666",
    style="italic",
)

# ================================================================
# LAYER 1: PRESENTATION (top)
# ================================================================
draw_section(0.4, 10.6, 19.2, 1.3, BLUE_BG)
ax.text(
    1.0,
    11.7,
    "PRESENTATION LAYER",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#4A90C4",
    zorder=4,
)

draw_box(0.7, 10.8, 3.2, 0.9, "Store Manager UI", "Login · Tabs · Responsive", IKEA_BLUE)
draw_box(4.2, 10.8, 2.6, 0.9, "Multi-User Login", "6 profiles + create", "#3B7CC9")
draw_box(7.1, 10.8, 2.6, 0.9, "Proactive Alerts", "Action tracking", "#3B7CC9")
draw_box(10.0, 10.8, 2.6, 0.9, "3 Tabs", "Briefing / Chat / Data", "#3B7CC9")
draw_box(12.9, 10.8, 2.2, 0.9, "Skapa Design", "IKEA tokens", "#3B7CC9")
draw_box(15.4, 10.8, 2.0, 0.9, "PDF Export", "Briefings", "#3B7CC9")
draw_box(17.7, 10.8, 1.6, 0.9, "Caching", "Per store", "#3B7CC9")

# ================================================================
# LAYER 2: API + ORCHESTRATION
# ================================================================
draw_section(0.4, 7.8, 19.2, 2.5, PURPLE_BG)
ax.text(
    1.0,
    10.1,
    "API & LLM ORCHESTRATION",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#7B4DAE",
    zorder=4,
)

# Top row: main components
draw_box(0.7, 9.2, 3.5, 0.7, "FastAPI Server", "25+ REST endpoints", PURPLE)
draw_box(4.5, 9.2, 3.2, 0.7, "RetailAgent", "Orchestrates tool calls", PURPLE)
draw_box(8.0, 9.2, 3.2, 0.7, "Claude Sonnet 4.6", "Tool-calling loop ×10", "#7B4DAE")
draw_box(11.5, 9.2, 2.8, 0.7, "Session Manager", "Per-user chat state", "#7B4DAE")
draw_box(14.6, 9.2, 2.5, 0.7, "Auth & Users", "Token-based login", "#7B4DAE")
draw_box(17.4, 9.2, 2.0, 0.7, "Claude API", "External", "#1a1a1a")

# Bottom row: sub-components
draw_box(
    0.7,
    8.1,
    2.3,
    0.7,
    "20 Tool Defs",
    "Registered tools",
    PURPLE_LIGHT,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    3.3,
    8.1,
    2.5,
    0.7,
    "System Prompt",
    "IKEA retail expert",
    PURPLE_LIGHT,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    6.1,
    8.1,
    2.8,
    0.7,
    "Report Generator",
    "Critic → Refine loop",
    PURPLE_LIGHT,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    9.2, 8.1, 2.5, 0.7, "Evaluator", "5-point rubric", PURPLE_LIGHT, fontsize=8, sublabel_size=6
)
draw_box(
    12.0,
    8.1,
    2.5,
    0.7,
    "Alert Scheduler",
    "30 min background",
    PURPLE_LIGHT,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    14.8, 8.1, 2.3, 0.7, "Validators", "Refs · numbers", PURPLE_LIGHT, fontsize=8, sublabel_size=6
)
draw_box(17.4, 8.1, 2.0, 0.7, "Memory", "Conv. history", PURPLE_LIGHT, fontsize=8, sublabel_size=6)

# ================================================================
# LAYER 3: CAPABILITY PILLARS
# ================================================================

# --- Q&A Engine ---
draw_section(0.4, 5.2, 4.6, 2.3, GREEN_BG)
ax.text(2.7, 7.3, "Q&A Engine", ha="center", fontsize=11, fontweight="bold", color=TEAL, zorder=4)
draw_box(
    0.7,
    6.4,
    4.0,
    0.65,
    "Conversational Q&A",
    "Natural language queries",
    TEAL,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    0.7,
    5.55,
    4.0,
    0.65,
    "Conversation Memory",
    "Per-session + preferences",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# --- Analysis Sparring ---
draw_section(5.3, 5.2, 5.4, 2.3, GREEN_BG)
ax.text(
    8.0, 7.3, "Analysis Sparring", ha="center", fontsize=11, fontweight="bold", color=TEAL, zorder=4
)
draw_box(
    5.6,
    6.4,
    4.8,
    0.65,
    "What-If Scenarios",
    "Price · Availability · Demand surge",
    TEAL,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    5.6,
    5.55,
    4.8,
    0.65,
    "Analytics Tools",
    "Sales / Stock / Margin / Actions",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# --- Proactive Insights ---
draw_section(11.0, 5.2, 4.6, 2.3, GREEN_BG)
ax.text(
    13.3,
    7.3,
    "Proactive Insights",
    ha="center",
    fontsize=11,
    fontweight="bold",
    color=TEAL,
    zorder=4,
)
draw_box(
    11.3,
    6.4,
    4.0,
    0.65,
    "Auto-Surfaced Alerts",
    "8 insight categories",
    TEAL,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    11.3,
    5.55,
    4.0,
    0.65,
    "Action Tracking",
    "Per-user · timestamped",
    "#0D8A73",
    fontsize=8,
    sublabel_size=6,
)

# --- Quality Loop ---
draw_section(15.9, 5.2, 3.7, 2.3, ORANGE_BG)
ax.text(
    17.75, 7.3, "Quality Loop", ha="center", fontsize=11, fontweight="bold", color=ORANGE, zorder=4
)
draw_box(
    16.2,
    6.4,
    3.1,
    0.65,
    "Critic Agent",
    "Reviews draft reports",
    ORANGE,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    16.2,
    5.55,
    3.1,
    0.65,
    "Evaluator Agent",
    "Scores 5 criteria /25",
    "#B8600A",
    fontsize=8,
    sublabel_size=6,
)

# ================================================================
# LAYER 4: DATA LAYER
# ================================================================

# --- Data Store ---
draw_section(0.4, 2.6, 6.0, 2.3, BROWN_BG)
ax.text(1.0, 4.7, "DATA STORE", ha="left", fontsize=7, fontweight="bold", color=BROWN, zorder=4)
draw_box(
    0.7,
    3.8,
    5.4,
    0.7,
    "Sales · Stock · Forecast · Products · Stores",
    "5 CSV files  ·  450K+ rows",
    BROWN,
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    0.7,
    2.85,
    5.4,
    0.65,
    "DataStore (loader.py)",
    "6 join helpers · period filters",
    "#A07A1C",
    fontsize=8,
    sublabel_size=6,
)

# --- External Context ---
draw_section(6.8, 2.6, 6.0, 2.3, GREY_BG)
ax.text(
    7.4,
    4.7,
    "EXTERNAL CONTEXT",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#484848",
    zorder=4,
)
draw_box(
    7.1,
    3.8,
    5.4,
    0.7,
    "Holidays · Promotions · Seasonal",
    "19 events · 12 campaigns · 8 regions",
    "#484848",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    7.1,
    2.85,
    5.4,
    0.65,
    "Store Region Mapping",
    "bu_sk → country → calendar",
    "#666666",
    fontsize=8,
    sublabel_size=6,
)

# --- Report Cache ---
draw_section(13.2, 2.6, 6.4, 2.3, "#E0E8E0")
ax.text(
    13.8,
    4.7,
    "REPORT & INSIGHTS CACHE",
    ha="left",
    fontsize=7,
    fontweight="bold",
    color="#3B6B3B",
    zorder=4,
)
draw_box(
    13.5,
    3.8,
    5.8,
    0.7,
    "Report Cache",
    "Per-store · with timestamps · force refresh",
    "#3B6B3B",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    13.5,
    2.85,
    5.8,
    0.65,
    "Insights Cache + Alert Actions",
    "Per-store · per-user actions",
    "#4D8B4D",
    fontsize=8,
    sublabel_size=6,
)

# ================================================================
# LAYER 5: DEPLOYMENT (bottom strip)
# ================================================================
draw_section(0.4, 1.2, 19.2, 1.1, "#F0F0F0")
ax.text(1.0, 2.1, "DEPLOYMENT", ha="left", fontsize=7, fontweight="bold", color="#888", zorder=4)
draw_box(0.7, 1.4, 3.0, 0.7, "Railway", "Cloud hosting", "#333", fontsize=8, sublabel_size=6)
draw_box(
    4.0, 1.4, 3.0, 0.7, "Python 3.11", "FastAPI + Uvicorn", "#333", fontsize=8, sublabel_size=6
)
draw_box(
    7.3, 1.4, 3.0, 0.7, "Static Files", "HTML/CSS/JS served", "#333", fontsize=8, sublabel_size=6
)
draw_box(
    10.6, 1.4, 3.0, 0.7, "Anthropic API", "Claude Sonnet 4.6", "#333", fontsize=8, sublabel_size=6
)
draw_box(
    13.9,
    1.4,
    2.8,
    0.7,
    "In-Memory State",
    "No database needed",
    "#333",
    fontsize=8,
    sublabel_size=6,
)
draw_box(
    17.0, 1.4, 2.6, 0.7, "ENV Config", "API keys · password", "#333", fontsize=8, sublabel_size=6
)

# ================================================================
# ARROWS — Data flow
# ================================================================

# Presentation → API
draw_arrow(2.3, 10.8, 2.45, 9.9, IKEA_BLUE, 2.0)
draw_arrow(5.5, 10.8, 5.5, 9.9, IKEA_BLUE, 1.5)

# API → Capability pillars
draw_arrow(2.7, 8.1, 2.7, 7.5, PURPLE, 1.5)
draw_arrow(8.0, 8.1, 8.0, 7.5, PURPLE, 1.5)
draw_arrow(13.3, 8.1, 13.3, 7.5, PURPLE, 1.5)
draw_arrow(17.75, 8.1, 17.75, 7.5, ORANGE, 1.5)

# Capability pillars → Data layer
draw_arrow(2.7, 5.55, 3.4, 4.9, TEAL, 1.3)
draw_arrow(8.0, 5.55, 8.0, 4.9, TEAL, 1.3)
draw_arrow(13.3, 5.55, 16.4, 4.9, TEAL, 1.3)

# Data → Deployment
draw_arrow(3.4, 2.85, 3.4, 2.3, "#8B6914", 1.0)
draw_arrow(9.8, 2.85, 9.8, 2.3, "#666", 1.0)

# Quality loop feedback arrow (curved)
ax.annotate(
    "",
    xy=(8.9, 8.45),
    xytext=(16.2, 8.45),
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5, connectionstyle="arc3,rad=-0.2"),
    zorder=2,
)
ax.text(
    12.5,
    8.85,
    "feedback → refine",
    ha="center",
    fontsize=6.5,
    color=ORANGE,
    style="italic",
    zorder=4,
)

# Claude API external call
draw_double_arrow(11.2, 9.55, 17.4, 9.55, "#1a1a1a", 1.5)

plt.tight_layout(pad=0.3)
out = "/Users/joost.jansen/Local/agent_framework/challenge_3_riverhacks/assets/architecture-system.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Saved → {out}")
