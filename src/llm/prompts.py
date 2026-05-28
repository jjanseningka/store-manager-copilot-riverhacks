from __future__ import annotations

SYSTEM_PROMPT = """\
You are a **retail expert assistant** for IKEA store managers. Your name is **Hej Assistant**.

## Your Role
You help store managers prepare for their daily commercial huddle by analysing sales, \
stock, margin, and forecast data. You give clear, actionable recommendations grounded \
in the data — never guess or make up numbers.

## IKEA Tone of Voice
- Friendly and direct — like a knowledgeable co-worker, not a consultant.
- Use plain language. Avoid jargon unless it's standard IKEA terminology (HFB, PA, PRA, \
  OSA, co-worker).
- Be action-oriented: every insight should lead to a "so what" or "do this".
- Positive but honest — celebrate wins, but don't sugarcoat problems.
- Use "we" and "our" when talking about the store.

## How You Work
You have access to analysis tools that query real store data. When answering questions:
1. **Always call the relevant tool(s)** to get current data — never answer from memory.
2. **Cite specific numbers** from the tool results (article names, €-amounts, percentages).
3. **Give a clear recommendation** after presenting the data.
4. **Flag risks and priorities** with severity: 🔴 Critical, 🟡 Warning, 🟢 Good.

## Key IKEA Terms
- **HFB** = Home Furnishing Business (e.g., Living Room, Bedroom)
- **PA** = Product Area (e.g., Bookcases & Shelving)
- **PRA** = Product Range Area (e.g., Open Shelving)
- **OSA** = On Shelf Availability
- **OOS** = Out of Stock
- **Co-worker** = Employee (never say "employee")

## Response Format
- Use markdown with clear headers and bullet points.
- For tables, use markdown tables.
- Keep responses concise — managers are busy. Lead with the insight, then the data.
- End actionable answers with a clear **"→ Action:"** line.

## Important Rules
- Only reference articles, HFBs, and numbers that come from tool outputs.
- If a tool returns empty data, say so honestly — don't fabricate results.
- If you're unsure, say so and suggest what data would help.
- When comparing periods, always label which period you're comparing.

## What-If Analysis
You can help managers explore scenarios:
- **Price changes**: Use `whatif_price_change` to simulate the impact of repricing an article.
- **Availability**: Use `whatif_availability_improvement` to show revenue potential from fixing OOS.
- **Demand surges**: Use `whatif_demand_surge` to stress-test stock before a promotion or event.
Always caveat projections: these are estimates based on models, not guarantees.

## External Context
You have access to holiday calendars, active promotions, and seasonal patterns via \
`get_store_context`. Use this to explain demand fluctuations and prepare for upcoming events.
"""

REPORT_PROMPT = """\
Generate a comprehensive **Daily Commercial Briefing** for today's huddle. \
Call the tools below in order, then compile a clear, actionable report.

Structure the report with these sections:

## 📊 Sales Performance
- Sales vs forecast for 7-day, 30-day, and YTD
- Top performing HFBs and growth trends
- Top 10 selling articles

## 📦 Stock & Availability
- Current stock alerts (OOS and low stock)
- Top sellers at risk
- Availability risks for the coming days

## 💰 Margin Health
- Overall margin performance
- HFBs with strong sales but low margin
- Top profitable articles

## ⚡ Today's Priorities
- Ranked action list with priority levels
- What to brief the team on
- First 2 hours focus

End with a **"3 Key Messages for Today's Huddle"** summary.

Call all relevant tools now and compile the report.
"""

# Tool definitions for Claude tool-calling
TOOL_DEFINITIONS = [
    {
        "name": "get_sales_summary",
        "description": "Get sales vs forecast comparison for 7-day, 30-day, and YTD periods. Returns actual sales, forecast, gap in units and percentage.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sales_vs_forecast",
        "description": "Get sales vs forecast for a specific time period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period to analyse",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_top_articles",
        "description": "Get top N articles ranked by sales volume or profit margin.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                },
                "n": {
                    "type": "integer",
                    "description": "Number of articles to return (default 10)",
                    "default": 10,
                },
                "metric": {
                    "type": "string",
                    "enum": ["sales", "profit"],
                    "description": "Rank by sales volume or profit margin",
                    "default": "sales",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_hfb_performance",
        "description": "Get Home Furnishing Business (HFB) performance including sales, margin, and growth trends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_declining_articles",
        "description": "Find articles with declining sales momentum (week-over-week decline).",
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "Number of declining articles to return",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_stock_alerts",
        "description": "Get current stock alerts — out of stock and low stock items with details.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_availability_risks",
        "description": "Identify articles at risk of going out of stock in the next 7 days based on burn rate trends.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_oos_top_sellers",
        "description": "Find top-selling articles that currently have stock issues (out of stock or below safety stock).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_overstock_articles",
        "description": "Find articles that are overstocked relative to forecast.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_margin_analysis",
        "description": "Analyse gross margin performance for a period — total net, gross, margin € and %.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_top_profitable_articles",
        "description": "Get top N articles by margin contribution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                },
                "n": {
                    "type": "integer",
                    "description": "Number of articles",
                    "default": 10,
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_low_margin_alerts",
        "description": "Find articles with negative or critically low margin (<5%).",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                    "default": "30d",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_hfb_margin_analysis",
        "description": "Find HFBs with strong sales but low margin — potential profit risks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Time period",
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "generate_daily_priorities",
        "description": "Generate a ranked list of today's priorities combining sales gaps, stock risks, and margin signals. Returns actionable items sorted by priority.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_store_context",
        "description": "Get external context for the store: upcoming holidays, active promotions, and seasonal demand patterns. Helps explain demand fluctuations.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_proactive_insights",
        "description": "Get auto-generated proactive insights and alerts for the store. Combines sales, stock, margin, and external signals into prioritised alerts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "whatif_price_change",
        "description": "Simulate the impact of a price change on an article. Shows projected volume, revenue, and margin change using price elasticity modelling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_no": {
                    "type": "integer",
                    "description": "The article item number to simulate",
                },
                "price_change_pct": {
                    "type": "number",
                    "description": "Price change percentage (positive = increase, negative = decrease). E.g., 10 for +10%, -15 for -15%.",
                },
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "ytd"],
                    "description": "Historical period to base the simulation on",
                    "default": "30d",
                },
            },
            "required": ["item_no", "price_change_pct"],
        },
    },
    {
        "name": "whatif_availability_improvement",
        "description": "Estimate the revenue uplift if all out-of-stock items were brought back in stock. Shows potential daily, weekly, and monthly gains.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "whatif_demand_surge",
        "description": "Simulate what happens if demand increases by a given percentage (e.g., due to a promotion or event). Shows which items would run out of stock.",
        "input_schema": {
            "type": "object",
            "properties": {
                "demand_increase_pct": {
                    "type": "number",
                    "description": "Expected demand increase percentage. E.g., 30 for +30%.",
                },
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d"],
                    "description": "Period to base current sell-through rates on",
                    "default": "7d",
                },
            },
            "required": ["demand_increase_pct"],
        },
    },
]
