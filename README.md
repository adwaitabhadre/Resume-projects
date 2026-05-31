# 🤖 Smart Data Insights Generator
### AI-Powered Automatic Data Analysis using Python + Prompt Engineering

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.0-green.svg)](https://pandas.pydata.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-orange.svg)](https://sqlite.org)
[![AI](https://img.shields.io/badge/AI-Prompt%20Engineering-purple.svg)](https://aistudio.google.com)

---

## 📌 Project Overview

An intelligent data analysis tool that automatically loads any CSV or Excel dataset, runs SQL queries, applies **Prompt Engineering** to generate AI-powered business insights, and creates a professional visual dashboard — with zero manual analysis needed.

> **"Upload your data → Get AI-powered insights in seconds."**

---

## 🎯 Problem Statement

Business analysts spend hours manually analyzing data, writing reports, and identifying patterns. This tool **automates the entire process** using Python, SQL, and AI — from raw data to actionable business insights.

---

## 🛠️ Tech Stack

| Skill | Usage |
|-------|-------|
| **Python** | Core pipeline logic |
| **Prompt Engineering** | Crafting structured prompts for AI insights |
| **SQL (SQLite)** | 5 analytical queries on in-memory DB |
| **Pandas & NumPy** | Data cleaning, EDA, transformations |
| **Matplotlib & Seaborn** | 6-panel visual dashboard |
| **Excel/CSV** | Supported input formats |
| **Google Gemini AI** | Optional live AI-generated insights |

---

## 📁 Project Structure

```
smart-data-insights/
│
├── data/
│   └── sales_data.csv          ← Sample retail sales dataset (80 records)
│
├── notebooks/
│   └── smart_data_insights.ipynb  ← Main notebook (run this!)
│
├── src/
│   └── insights_generator.py   ← Standalone Python script
│
├── outputs/                    ← Auto-generated results
│   ├── dashboard.png           ← 6-panel visual dashboard
│   ├── cleaned_data.csv        ← Cleaned dataset
│   ├── category_summary.csv    ← SQL analysis results
│   ├── monthly_trend.csv       ← Monthly revenue trend
│   └── ai_insights.txt         ← AI-generated business insights
│
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/smart-data-insights.git
cd smart-data-insights
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Notebook
```bash
jupyter notebook notebooks/smart_data_insights.ipynb
```

### 4. (Optional) Enable Live AI Insights
Get your **FREE** Gemini API key at: https://aistudio.google.com/app/apikey  
Then paste it in the notebook cell:
```python
GEMINI_API_KEY = 'your-key-here'
```

### 5. Use Your Own Data
Replace the data path in the notebook with any CSV or Excel file:
```python
DATA_PATH = 'your_data.csv'   # or your_file.xlsx
```

---

## 📊 What Gets Generated

### 6-Panel Visual Dashboard
| Panel | Chart Type | Shows |
|-------|-----------|-------|
| 1 | Bar Chart | Total Sales by Category |
| 2 | Line Chart | Monthly Sales Trend |
| 3 | Horizontal Bar | Profit by Region |
| 4 | Pie Chart | Sales by Customer Segment |
| 5 | Ranked Bar | Top 5 Products |
| 6 | Heatmap | Correlation Matrix |

### SQL Queries Executed
1. Total & Average Sales by Category
2. Regional Sales & Profit Breakdown
3. Month-over-Month Revenue Trend
4. Top 10 Best Selling Products
5. Customer Segment Analysis

### AI Insights Report (5 sections)
1. Key Findings (with specific numbers)
2. Top Performing Areas
3. Underperforming Areas
4. Business Recommendations
5. Risk Factors

---

## 💡 Prompt Engineering Approach

The core AI feature uses a structured **chain-of-thought prompt** that:
- Injects real statistics from the dataset
- Specifies the exact output format (5 sections)
- Provides business context for domain-relevant insights
- Uses role-prompting ("You are a senior Data Analyst...")

```python
PROMPT = f"""
You are a senior Data Analyst. Analyze the following data...
Total Revenue: ₹{total_sales:,.0f}
Profit Margin: {profit_margin}%
...
YOUR TASK: Provide KEY FINDINGS, RECOMMENDATIONS, RISK FACTORS...
"""
```

---

## 📈 Key Results

- Analyzed **80 transactions** across 4 regions, 2 categories, 12 products
- Generated **5 SQL analytical queries** automatically
- Produced **6 interactive visualizations** in one dashboard
- Reduced manual analysis time from hours to **under 30 seconds**
- Works with **any CSV or Excel dataset** — fully reusable

---

## 🔁 Works With Any Dataset
Just change the file path and the tool auto-adapts to your columns:
- Sales data ✅
- HR data ✅
- Marketing data ✅
- Financial data ✅
- Survey data ✅

---

## 👩‍💻 Author

**Adwaita Bhadre**  
Data Analyst | Python · SQL · Power BI · Prompt Engineering  
📧 adwaitabhadre789@gmail.com  
🔗 [LinkedIn](https://linkedin.com/in/adwaita-bhadre-610328232)

---

## 📄 License
MIT License — free to use, modify, and distribute.
