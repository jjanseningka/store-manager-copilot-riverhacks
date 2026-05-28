"""Generate a clean, minimal architecture diagram for PowerPoint."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(16, 9), dpi=200)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")
fig.patch.set_facecolor("white")

IKEA_BLUE = "#0058A3"
TEAL = "#0A6E5C"
PURPLE = "#5B2D8E"
BROWN = "#8B6914"
GREY = "#666666"
LIGHT_BLUE = "#D4E8F7"
LIGHT_PURPLE = "#E8D4F7"
LIGHT_GREEN = "#D4F0E8"
LIGHT_BROWN = "#F0E4D0"


def box(x, y, w, h, label, sub="", color=IKEA_BLUE, tc="white", fs=9, ss=7):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.08", facecolor=color, edgecolor="none", zorder=3
        )
    )
    if sub:
        ax.text(
            x + w / 2,
            y + h / 2 + 0.12,
            label,
            ha="center",
            va="center",
            fontsize=fs,
            fontweight="bold",
            color=tc,
            zorder=4,
        )
        ax.text(
            x + w / 2,
            y + h / 2 - 0.12,
            sub,
            ha="center",
            va="center",
            fontsize=ss,
            color=tc,
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
            fontsize=fs,
            fontweight="bold",
            color=tc,
            zorder=4,
        )


def section(x, y, w, h, color):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="#DFDFDF",
            linewidth=1.5,
            zorder=1,
            alpha=0.5,
        )
    )


def arrow(x1, y1, x2, y2, color="#999", lw=1.5):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=lw),
        zorder=2,
    )


# ── Title ──
ax.text(
    8,
    8.55,
    "Hej Assistant — Architecture",
    ha="center",
    fontsize=18,
    fontweight="bold",
    color="#111",
)
ax.text(
    8,
    8.2,
    "AI daily commercial briefing for IKEA store managers",
    ha="center",
    fontsize=10,
    color="#666",
    style="italic",
)

# ════════════════════════════════════════
# LAYER 1: USER INTERFACE
# ════════════════════════════════════════
section(0.4, 6.8, 15.2, 1.1, LIGHT_BLUE)
ax.text(
    1.0, 7.7, "USER INTERFACE", ha="left", fontsize=7, fontweight="bold", color="#4A90C4", zorder=4
)

box(0.7, 6.95, 3.5, 0.8, "Store Manager", "Login · select store", IKEA_BLUE)
box(4.5, 6.95, 3.5, 0.8, "Daily Briefing", "Generated report", "#3B7CC9")
box(8.3, 6.95, 3.5, 0.8, "Chat Q&A", "Ask anything", "#3B7CC9")
box(12.1, 6.95, 3.2, 0.8, "Proactive Alerts", "Action tracking", "#3B7CC9")

# ════════════════════════════════════════
# LAYER 2: AGENT (the core)
# ════════════════════════════════════════
section(0.4, 4.2, 15.2, 2.3, LIGHT_PURPLE)
ax.text(1.0, 6.3, "AI AGENT", ha="left", fontsize=7, fontweight="bold", color="#7B4DAE", zorder=4)

box(0.7, 5.5, 4.8, 0.7, "Claude Sonnet 4.6", "Tool-calling agent", PURPLE)
box(5.8, 5.5, 4.8, 0.7, "20 Retail Tools", "Sales · Stock · Margin · What-if", PURPLE)
box(10.9, 5.5, 4.4, 0.7, "Quality Loop", "Critic → Refine → Evaluate", PURPLE)

box(0.7, 4.5, 3.2, 0.7, "Daily Briefing", "Auto-generates report", "#9B6DCE", fs=8, ss=6)
box(4.2, 4.5, 3.2, 0.7, "Conversational Q&A", "Answers any question", "#9B6DCE", fs=8, ss=6)
box(7.7, 4.5, 3.8, 0.7, "Proactive Insights", "8 alert categories", "#9B6DCE", fs=8, ss=6)
box(11.8, 4.5, 3.5, 0.7, "What-If Analysis", "Price · Stock · Demand", "#9B6DCE", fs=8, ss=6)

# ════════════════════════════════════════
# LAYER 3: DATA
# ════════════════════════════════════════
section(0.4, 2.0, 9.5, 1.9, LIGHT_BROWN)
ax.text(1.0, 3.7, "DATA", ha="left", fontsize=7, fontweight="bold", color=BROWN, zorder=4)

box(0.7, 2.9, 2.8, 0.6, "Sales", "363K transactions", BROWN, fs=8, ss=6)
box(3.8, 2.9, 2.8, 0.6, "Stock", "87K snapshots", BROWN, fs=8, ss=6)
box(6.9, 2.9, 2.7, 0.6, "Forecast", "87K rows", BROWN, fs=8, ss=6)
box(0.7, 2.15, 2.8, 0.55, "Products", "30 articles", "#A07A1C", fs=8, ss=6)
box(3.8, 2.15, 2.8, 0.55, "8 Stores", "Multi-store", "#A07A1C", fs=8, ss=6)
box(6.9, 2.15, 2.7, 0.55, "Periods", "7d · 30d · YTD", "#A07A1C", fs=8, ss=6)

section(10.2, 2.0, 5.4, 1.9, "#E8E8E8")
ax.text(10.8, 3.7, "CONTEXT", ha="left", fontsize=7, fontweight="bold", color="#484848", zorder=4)

box(10.5, 2.9, 4.8, 0.6, "Holidays · Promotions", "19 events · 12 campaigns", "#484848", fs=8, ss=6)
box(10.5, 2.15, 4.8, 0.55, "Seasonal Demand", "Monthly factors · 8 regions", GREY, fs=8, ss=6)

# ════════════════════════════════════════
# ARROWS
# ════════════════════════════════════════
# UI → Agent
arrow(2.45, 6.95, 3.1, 6.2, IKEA_BLUE, 2)
arrow(6.25, 6.95, 6.25, 6.2, IKEA_BLUE, 1.5)
arrow(10.05, 6.95, 10.05, 6.2, IKEA_BLUE, 1.5)
arrow(13.7, 6.95, 13.1, 6.2, IKEA_BLUE, 1.5)

# Agent → Data
arrow(3.1, 4.5, 3.1, 3.9, TEAL, 1.5)
arrow(8.2, 4.5, 8.2, 3.9, TEAL, 1.5)
arrow(13.5, 4.5, 12.9, 3.9, TEAL, 1.5)

# Quality loop feedback
ax.annotate(
    "",
    xy=(5.8, 5.85),
    xytext=(10.9, 5.85),
    arrowprops=dict(arrowstyle="->", color="#CC5500", lw=1.5, connectionstyle="arc3,rad=-0.15"),
    zorder=2,
)
ax.text(8.35, 6.15, "refine", ha="center", fontsize=7, color="#CC5500", style="italic", zorder=4)

plt.tight_layout(pad=0.3)
out = "/Users/joost.jansen/Local/agent_framework/challenge_3_riverhacks/assets/architecture-system.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Saved → {out}")
