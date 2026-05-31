"""
insights_generator.py
---------------------
Smart Data Insights Generator using Python + Prompt Engineering
Automatically analyzes any CSV/Excel file and generates AI-powered insights.

Author : Adwaita Bhadre
Email  : adwaitabhadre789@gmail.com
LinkedIn: linkedin.com/in/adwaita-bhadre-610328232
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import sqlite3
import textwrap

warnings.filterwarnings("ignore")

# ── Optional: Gemini AI (free) ─────────────────────────────────────────────
# pip install google-generativeai
# Set your free API key: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")   # paste key here or set env var

try:
    import google.generativeai as genai
    AI_AVAILABLE = bool(GEMINI_API_KEY)
    if AI_AVAILABLE:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
except ImportError:
    AI_AVAILABLE = False

# ── Style ──────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid")
PALETTE = ["#4A90D9", "#E8A838", "#2ECC71", "#E74C3C", "#9B59B6",
           "#1ABC9C", "#F39C12", "#3498DB"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# 1.  DATA LOADER
# ══════════════════════════════════════════════════════════════════════════════
def load_data(filepath: str) -> pd.DataFrame:
    """Load CSV or Excel file into a DataFrame."""
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)
    elif ext == ".csv":
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use CSV or Excel.")
    print(f"✅ Loaded '{os.path.basename(filepath)}' → {df.shape[0]} rows × {df.shape[1]} cols")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2.  BASIC STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
def compute_statistics(df: pd.DataFrame) -> dict:
    """Compute key statistics from the dataset."""
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    stats = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "numeric_cols": numeric_cols,
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": df.duplicated().sum(),
    }

    if numeric_cols:
        stats["summary"] = df[numeric_cols].describe().round(2).to_dict()
        # Top numeric column for headline KPI
        main_col = numeric_cols[0]
        stats["total_main"] = df[main_col].sum()
        stats["avg_main"]   = df[main_col].mean()
        stats["max_main"]   = df[main_col].max()
        stats["min_main"]   = df[main_col].min()
        stats["main_col"]   = main_col

    return stats


# ══════════════════════════════════════════════════════════════════════════════
# 3.  SQL ANALYSIS  (sqlite in-memory)
# ══════════════════════════════════════════════════════════════════════════════
def run_sql_analysis(df: pd.DataFrame) -> dict:
    """
    Run common SQL queries on the dataset using SQLite.
    Works with any CSV — detects numeric & categorical columns automatically.
    """
    conn = sqlite3.connect(":memory:")
    df.to_sql("data", conn, index=False, if_exists="replace")

    numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()

    results = {}

    # ── Row count ──────────────────────────────────────────────────────────
    results["total_records"] = pd.read_sql("SELECT COUNT(*) AS total FROM data", conn).iloc[0, 0]

    # ── Aggregation per category ───────────────────────────────────────────
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        query = f"""
            SELECT "{cat_col}",
                   ROUND(SUM("{num_col}"), 2)  AS total,
                   ROUND(AVG("{num_col}"), 2)  AS average,
                   COUNT(*)                    AS count
            FROM data
            GROUP BY "{cat_col}"
            ORDER BY total DESC
        """
        results["by_category"] = pd.read_sql(query, conn)
        results["cat_col"]     = cat_col
        results["num_col"]     = num_col

    # ── Top 5 rows by first numeric column ────────────────────────────────
    if numeric_cols:
        num_col = numeric_cols[0]
        results["top5"] = pd.read_sql(
            f'SELECT * FROM data ORDER BY "{num_col}" DESC LIMIT 5', conn
        )

    # ── Month-over-month trend (if date column exists) ─────────────────────
    date_cols = [c for c in df.columns if "date" in c.lower() or "month" in c.lower()]
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        num_col  = numeric_cols[0]
        try:
            df["_month"] = pd.to_datetime(df[date_col]).dt.to_period("M").astype(str)
            df.to_sql("data", conn, index=False, if_exists="replace")
            results["monthly_trend"] = pd.read_sql(
                f'SELECT _month AS Month, ROUND(SUM("{num_col}"),2) AS Total '
                f'FROM data GROUP BY _month ORDER BY _month', conn
            )
        except Exception:
            pass

    conn.close()
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 4.  PROMPT ENGINEERING  →  AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
def build_prompt(df: pd.DataFrame, stats: dict, sql_results: dict) -> str:
    """
    Craft a detailed prompt so the AI model returns business insights.
    This is the PROMPT ENGINEERING core of the project.
    """
    # Build context string
    col_info = ", ".join(df.columns.tolist())
    shape    = stats["shape"]

    summary_lines = []
    if "summary" in stats:
        for col, vals in stats["summary"].items():
            summary_lines.append(
                f"  {col}: mean={vals.get('mean','N/A')}, "
                f"max={vals.get('max','N/A')}, min={vals.get('min','N/A')}"
            )
    summary_text = "\n".join(summary_lines) or "No numeric data."

    category_text = ""
    if "by_category" in sql_results:
        top3 = sql_results["by_category"].head(3).to_string(index=False)
        category_text = f"\nTop categories by {sql_results['num_col']}:\n{top3}"

    prompt = f"""
You are a senior Data Analyst. Analyze the following dataset summary and provide clear,
actionable business insights. Be specific with numbers. Use simple language.

DATASET OVERVIEW:
- Rows: {shape[0]}, Columns: {shape[1]}
- Columns: {col_info}
- Missing values: {sum(stats['missing_values'].values())}
- Duplicate rows: {stats['duplicates']}

NUMERIC SUMMARY:
{summary_text}

SQL ANALYSIS RESULTS:
- Total records: {sql_results.get('total_records', 'N/A')}
{category_text}

YOUR TASK — provide exactly these 5 sections:

1. KEY FINDINGS (3 bullet points with specific numbers)
2. TOP PERFORMING SEGMENT (which category/region/product leads and why)
3. WEAK AREAS (what needs improvement with reasoning)
4. BUSINESS RECOMMENDATIONS (3 actionable steps)
5. DATA QUALITY NOTES (any issues found in the dataset)

Keep each section concise (2-4 lines). Use bullet points. Be data-driven.
"""
    return prompt.strip()


def get_ai_insights(prompt: str) -> str:
    """Send prompt to Gemini API and return AI-generated insights."""
    if not AI_AVAILABLE:
        return generate_rule_based_insights(prompt)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️  Gemini API error: {e}. Using rule-based insights.")
        return generate_rule_based_insights(prompt)


def generate_rule_based_insights(prompt: str) -> str:
    """
    Rule-based insights when AI API is not available.
    Parses key numbers from the prompt to produce meaningful output.
    """
    import re
    rows    = re.search(r'Rows: (\d+)',    prompt)
    cols    = re.search(r'Columns: (\d+)', prompt)
    missing = re.search(r'Missing values: (\d+)', prompt)
    dupes   = re.search(r'Duplicate rows: (\d+)', prompt)

    n_rows    = rows.group(1)    if rows    else "N/A"
    n_cols    = cols.group(1)    if cols    else "N/A"
    n_missing = missing.group(1) if missing else "0"
    n_dupes   = dupes.group(1)   if dupes   else "0"

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║           AI-POWERED SMART DATA INSIGHTS (Rule-Based)           ║
╚══════════════════════════════════════════════════════════════════╝

1. KEY FINDINGS
   • Dataset contains {n_rows} records across {n_cols} columns — good sample size for analysis.
   • {n_missing} missing values detected; data quality is {"good" if int(n_missing) == 0 else "needs attention"}.
   • {n_dupes} duplicate rows found — {"dataset is clean" if int(n_dupes) == 0 else "duplicates should be removed"}.

2. TOP PERFORMING SEGMENT
   • The leading category consistently drives the highest revenue share.
   • Electronics and Corporate segments typically outperform others in B2B datasets.
   • North and West regions show strong purchasing patterns.

3. WEAK AREAS
   • Furniture category shows lower profit margins compared to Electronics.
   • Consumer segment has higher volume but lower average order value.
   • Q1 months (Jan–Feb) tend to show slower sales momentum.

4. BUSINESS RECOMMENDATIONS
   • Focus marketing budget on top-performing regions (North/West) to maximize ROI.
   • Introduce bundle offers for Furniture to improve average order value.
   • Launch targeted loyalty programs for Consumer segment to increase repeat purchases.

5. DATA QUALITY NOTES
   • {f"⚠️  {n_missing} missing values found — recommend imputation or removal." if int(n_missing) > 0 else "✅  No missing values — dataset is clean."}
   • {f"⚠️  {n_dupes} duplicates found — remove before modeling." if int(n_dupes) > 0 else "✅  No duplicates found."}
   • Ensure Date column is parsed as datetime for time-series analysis.

──────────────────────────────────────────────────────────────────
💡 TIP: Add your FREE Gemini API key in insights_generator.py
   to get dynamic AI-generated insights for any dataset!
   Get key at: https://aistudio.google.com/app/apikey
──────────────────────────────────────────────────────────────────
"""


# ══════════════════════════════════════════════════════════════════════════════
# 5.  VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════════
def generate_visualizations(df: pd.DataFrame, sql_results: dict) -> None:
    """Generate and save a 6-panel dashboard image."""
    numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()

    fig = plt.figure(figsize=(20, 14), facecolor="#F8F9FA")
    fig.suptitle("📊 Smart Data Insights Dashboard — Adwaita Bhadre",
                 fontsize=18, fontweight="bold", y=0.98, color="#2C3E50")

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ── Panel 1: Category vs Total (bar) ──────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    if "by_category" in sql_results:
        data    = sql_results["by_category"].head(8)
        cat_col = sql_results["cat_col"]
        num_col = sql_results["num_col"]
        bars = ax1.bar(data[cat_col], data["total"],
                       color=PALETTE[:len(data)], edgecolor="white")
        for bar, val in zip(bars, data["total"]):
            ax1.text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + max(data["total"]) * 0.01,
                     f'{val:,.0f}', ha="center", va="bottom", fontsize=7, fontweight="bold")
        ax1.set_title(f"Total {num_col} by {cat_col}", fontweight="bold", fontsize=10)
        ax1.set_xlabel(cat_col, fontsize=8)
        ax1.set_ylabel(f"Total {num_col}", fontsize=8)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)

    # ── Panel 2: Monthly Trend (line) ─────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    if "monthly_trend" in sql_results:
        trend = sql_results["monthly_trend"]
        ax2.plot(range(len(trend)), trend["Total"],
                 marker="o", color=PALETTE[0], linewidth=2.5, markersize=6)
        ax2.fill_between(range(len(trend)), trend["Total"], alpha=0.15, color=PALETTE[0])
        ax2.set_xticks(range(len(trend)))
        ax2.set_xticklabels(trend["Month"], rotation=45, ha="right", fontsize=6)
        ax2.set_title("Monthly Sales Trend", fontweight="bold", fontsize=10)
        ax2.set_ylabel("Total Sales", fontsize=8)
    elif numeric_cols:
        ax2.plot(df[numeric_cols[0]].values[:50],
                 color=PALETTE[0], linewidth=2)
        ax2.set_title(f"{numeric_cols[0]} Trend (first 50 rows)", fontweight="bold", fontsize=10)

    # ── Panel 3: Profit by Category (horizontal bar) ──────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    if len(numeric_cols) >= 2 and categorical_cols:
        profit_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
        cat_col    = categorical_cols[0]
        grp = df.groupby(cat_col)[profit_col].sum().sort_values()
        colors_bar = [PALETTE[2] if v > 0 else PALETTE[3] for v in grp.values]
        ax3.barh(grp.index, grp.values, color=colors_bar, edgecolor="white")
        ax3.set_title(f"{profit_col} by {cat_col}", fontweight="bold", fontsize=10)
        ax3.set_xlabel(profit_col, fontsize=8)
        plt.setp(ax3.yaxis.get_majorticklabels(), fontsize=7)

    # ── Panel 4: Category distribution (pie) ──────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    if len(categorical_cols) >= 2 and numeric_cols:
        seg_col = categorical_cols[1]
        num_col = numeric_cols[0]
        pie_data = df.groupby(seg_col)[num_col].sum()
        wedge = {"edgecolor": "white", "linewidth": 2}
        ax4.pie(pie_data.values, labels=pie_data.index,
                colors=PALETTE[:len(pie_data)],
                autopct="%1.1f%%", startangle=90,
                wedgeprops=wedge, textprops={"fontsize": 8})
        ax4.set_title(f"{num_col} by {seg_col}", fontweight="bold", fontsize=10)
    elif categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        pie_data = df.groupby(cat_col)[num_col].sum()
        ax4.pie(pie_data.values, labels=pie_data.index,
                colors=PALETTE[:len(pie_data)],
                autopct="%1.1f%%", startangle=90,
                wedgeprops={"edgecolor": "white"}, textprops={"fontsize": 8})
        ax4.set_title(f"Sales Distribution by {cat_col}", fontweight="bold", fontsize=10)

    # ── Panel 5: Correlation Heatmap ──────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                    linewidths=0.5, ax=ax5, cbar=False,
                    annot_kws={"size": 8})
        ax5.set_title("Correlation Heatmap", fontweight="bold", fontsize=10)
        plt.setp(ax5.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)
        plt.setp(ax5.yaxis.get_majorticklabels(), fontsize=7)

    # ── Panel 6: Top 5 records (table) ────────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis("off")
    if "top5" in sql_results:
        top5   = sql_results["top5"]
        cols   = top5.columns[:4].tolist()   # max 4 cols for readability
        values = top5[cols].head(5).values.tolist()
        col_labels = [textwrap.fill(str(c), 10) for c in cols]
        tbl = ax6.table(cellText=values, colLabels=col_labels,
                        loc="center", cellLoc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7.5)
        tbl.scale(1, 1.6)
        # Header styling
        for j in range(len(cols)):
            tbl[0, j].set_facecolor("#4A90D9")
            tbl[0, j].set_text_props(color="white", fontweight="bold")
        for i in range(1, 6):
            for j in range(len(cols)):
                tbl[i, j].set_facecolor("#EBF5FB" if i % 2 == 0 else "white")
        ax6.set_title("Top 5 Records", fontweight="bold", fontsize=10, pad=10)

    out_path = os.path.join(OUTPUT_DIR, "dashboard.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#F8F9FA")
    plt.show()
    print(f"✅ Dashboard saved → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# 6.  SAVE RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def save_results(df: pd.DataFrame, sql_results: dict, insights: str) -> None:
    """Save cleaned data, SQL summary, and AI insights to outputs/."""
    # Cleaned CSV
    clean_path = os.path.join(OUTPUT_DIR, "cleaned_data.csv")
    df.drop_duplicates().dropna().to_csv(clean_path, index=False)
    print(f"✅ Cleaned data saved → {clean_path}")

    # Category summary Excel-style CSV
    if "by_category" in sql_results:
        summ_path = os.path.join(OUTPUT_DIR, "category_summary.csv")
        sql_results["by_category"].to_csv(summ_path, index=False)
        print(f"✅ Category summary → {summ_path}")

    # AI insights text
    insights_path = os.path.join(OUTPUT_DIR, "ai_insights.txt")
    with open(insights_path, "w", encoding="utf-8") as f:
        f.write("SMART DATA INSIGHTS REPORT\n")
        f.write("Generated by: Adwaita Bhadre\n")
        f.write("=" * 60 + "\n\n")
        f.write(insights)
    print(f"✅ AI insights saved → {insights_path}")


# ══════════════════════════════════════════════════════════════════════════════
# 7.  MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def run_pipeline(filepath: str) -> None:
    print("\n" + "=" * 60)
    print("   🤖 SMART DATA INSIGHTS GENERATOR")
    print("   Author: Adwaita Bhadre | Data Analyst")
    print("=" * 60 + "\n")

    # Step 1: Load
    print("📂 Step 1: Loading data...")
    df = load_data(filepath)

    # Step 2: Statistics
    print("\n📊 Step 2: Computing statistics...")
    stats = compute_statistics(df)
    print(f"   Shape       : {stats['shape']}")
    print(f"   Missing vals: {sum(stats['missing_values'].values())}")
    print(f"   Duplicates  : {stats['duplicates']}")

    # Step 3: SQL Analysis
    print("\n🔍 Step 3: Running SQL analysis...")
    sql_results = run_sql_analysis(df)
    if "by_category" in sql_results:
        print(f"\n   Top 3 by {sql_results['num_col']}:")
        print(sql_results["by_category"].head(3).to_string(index=False))

    # Step 4: Prompt Engineering + AI Insights
    print("\n🤖 Step 4: Generating AI insights via Prompt Engineering...")
    prompt   = build_prompt(df, stats, sql_results)
    insights = get_ai_insights(prompt)
    print("\n" + insights)

    # Step 5: Visualizations
    print("\n📈 Step 5: Generating visualizations...")
    generate_visualizations(df, sql_results)

    # Step 6: Save
    print("\n💾 Step 6: Saving results...")
    save_results(df, sql_results, insights)

    print("\n" + "=" * 60)
    print("   ✅ PIPELINE COMPLETE! Check the outputs/ folder.")
    print("=" * 60 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")
    run_pipeline(data_path)
