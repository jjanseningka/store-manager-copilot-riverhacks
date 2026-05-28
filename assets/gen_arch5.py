"""Generate a clean architecture diagram for presentation slides."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(16, 9), dpi=220)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")
fig.patch.set_facecolor("white")

BLUE = "#0058A3"
BLUE_LIGHT = "#E7F0F8"
PURPLE = "#5B2D8E"
PURPLE_LIGHT = "#EFE7F6"
TEAL = "#0A6E5C"
TEAL_LIGHT = "#E6F4F1"
ORANGE = "#CC5500"
ORANGE_LIGHT = "#FFF0E5"
DARK = "#111111"
GREY = "#666666"
GREY_LIGHT = "#F6F6F6"
GREY_BORDER = "#CFCFCF"


def box(x, y, w, h, label, sub="", facecolor=BLUE, edgecolor="none", text_color="white"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.08,rounding_size=0.08",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.8 if edgecolor != "none" else 0,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h * 0.62,
        label,
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=text_color,
        zorder=4,
    )
    if sub:
        ax.text(
            x + w / 2,
            y + h * 0.32,
            sub,
            ha="center",
            va="center",
            fontsize=9,
            color=text_color,
            zorder=4,
        )


def arrow(x1, y1, x2, y2, color, lw=2.2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=16),
        zorder=2,
    )


ax.text(
    8,
    8.55,
    "Hej Assistant Architecture",
    ha="center",
    va="center",
    fontsize=22,
    fontweight="bold",
    color=DARK,
)
ax.text(
    8,
    8.17,
    "User experience, agent reasoning, tools, and prototype data",
    ha="center",
    va="center",
    fontsize=11,
    color=GREY,
)

# Store manager
box(6.25, 7.1, 3.5, 0.85, "Store Manager", "Selects store and uses the experience", BLUE)

# Interface layer
interface_y = 5.75
interface_w = 3.2
interface_h = 0.9
interface_gap = 0.35
interface_x = [1.2, 4.75, 8.3, 11.85]
interface_labels = [
    ("Daily Briefing", "KPIs and AI report"),
    ("Chat Q&A", "Ask store questions"),
    ("Data Explorer", "View raw data"),
    ("Proactive Alerts", "Auto-surfaced issues"),
]

for x, (label, sub) in zip(interface_x, interface_labels, strict=False):
    box(x, interface_y, interface_w, interface_h, label, sub, BLUE)

arrow(8, 7.1, 8, interface_y + interface_h, BLUE, 2.0)

# Agent and quality loop
agent_y = 3.85
box(
    1.25,
    agent_y,
    8.7,
    1.25,
    "Claude AI Agent",
    "Chooses tools, reasons over data, writes answers and reports",
    PURPLE_LIGHT,
    PURPLE,
    DARK,
)
ax.text(
    5.6,
    agent_y + 0.25,
    "20 retail tools available",
    ha="center",
    va="center",
    fontsize=10,
    color=GREY,
    zorder=4,
)

box(
    10.45,
    agent_y,
    4.3,
    1.25,
    "Quality Loop",
    "Critic reviews, agent refines, evaluator scores",
    ORANGE_LIGHT,
    ORANGE,
    DARK,
)
arrow(10.45, agent_y + 0.62, 9.95, agent_y + 0.62, ORANGE, 2.0)

for x in interface_x:
    arrow(x + interface_w / 2, interface_y, 5.6, agent_y + 1.25, PURPLE, 1.7)

# Tool groups
tools_y = 2.05
tool_w = 4.2
tool_h = 0.95
tool_x = [0.9, 5.9, 10.9]
tool_labels = [
    ("Commercial Tools", "Sales, stock, margin"),
    ("Scenario Tools", "What-if and forecasting"),
    ("Context Tools", "Priorities, holidays, seasons"),
]

for x, (label, sub) in zip(tool_x, tool_labels, strict=False):
    box(x, tools_y, tool_w, tool_h, label, sub, TEAL)
    arrow(5.6, agent_y, x + tool_w / 2, tools_y + tool_h, TEAL, 1.7)

# Prototype data layer
data_y = 0.55
data_patch = FancyBboxPatch(
    (1.0, data_y),
    14.0,
    0.95,
    boxstyle="round,pad=0.08,rounding_size=0.08",
    facecolor=GREY_LIGHT,
    edgecolor=GREY_BORDER,
    linewidth=2,
    linestyle=(0, (6, 4)),
    zorder=3,
)
ax.add_patch(data_patch)
ax.text(
    8,
    data_y + 0.62,
    "Simulated IKEA Store Data",
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold",
    color=DARK,
    zorder=4,
)
ax.text(
    8,
    data_y + 0.28,
    "Sales, stock, forecast, products, stores, and seasonal context",
    ha="center",
    va="center",
    fontsize=10,
    color=GREY,
    zorder=4,
)

for x in tool_x:
    arrow(x + tool_w / 2, tools_y, x + tool_w / 2, data_y + 0.95, GREY, 1.6)

plt.tight_layout(pad=0.4)
out = "/Users/joost.jansen/Local/agent_framework/challenge_3_riverhacks/assets/architecture-system.png"
plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Saved -> {out}")
