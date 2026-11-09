"""Project 03: Customer Churn / Sales Trend Analysis (UCI Online Retail dataset).

Data: https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/
      master/data/retail-data/all/online-retail-dataset.csv
Save it next to this script as online_retail.csv.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

NAVY, CORAL, TEAL, GOLD = "#1f3a5f", "#e4572e", "#2a9d8f", "#e9b44c"
sns.set_theme(style="whitegrid", context="talk", font_scale=0.8)
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 15,
                     "savefig.bbox": "tight", "figure.dpi": 110})
pd.set_option("display.width", 130)
pd.set_option("display.max_columns", 30)


def section(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def save(fig, name):
    fig.savefig(name); plt.close(fig)


# ------------------------------------------------------------------
# 1. LOAD & INSPECT
# ------------------------------------------------------------------
try:
    raw = pd.read_csv("online_retail.csv")
except UnicodeDecodeError:
    raw = pd.read_csv("online_retail.csv", encoding="latin-1")

section("1. RAW DATA")
print(raw.shape)
print(raw.head(3))
print(raw.isnull().sum()[raw.isnull().sum() > 0])

# ------------------------------------------------------------------
# 2. CLEANING
# ------------------------------------------------------------------
section("2. CLEANING")
n0 = len(raw)
df = raw.copy()
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M")
df["InvoiceNo"] = df["InvoiceNo"].astype(str)

dups = df.duplicated().sum()
df = df.drop_duplicates()
cancelled = df["InvoiceNo"].str.startswith("C")
print(f"Exact duplicate rows removed : {dups:,}")
print(f"Cancellation lines (C-invoice): {cancelled.sum():,}  (kept separately)")
returns = df[cancelled].copy()
df = df[~cancelled]
bad = (df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)
print(f"Zero/negative qty or price    : {bad.sum():,}  (removed)")
df = df[~bad]
no_id = df["CustomerID"].isnull().sum()
print(f"Rows without CustomerID       : {no_id:,} ({no_id/len(df):.1%}) "
      f"-> kept for sales trends, excluded from customer analysis")
# Non-product stock codes (postage, fees, manual adjustments)
non_product = df["StockCode"].astype(str).str.match(r"^(POST|DOT|M|BANK CHARGES|CRUK|C2|AMAZONFEE|S|B|D|PADS|gift.*)$",
                                                    case=False)
print(f"Non-product lines (postage etc): {non_product.sum():,}  (removed)")
df = df[~non_product]
print(f"Rows: {n0:,} -> {len(df):,}")

# ------------------------------------------------------------------
# 3. FEATURE ENGINEERING & DATE EXTRACTION
# ------------------------------------------------------------------
df["Revenue"] = df["Quantity"] * df["UnitPrice"]
d = df["InvoiceDate"]
df["Date"] = d.dt.normalize()
df["Year"] = d.dt.year
df["Month"] = d.dt.month
df["YearMonth"] = d.dt.to_period("M")
df["Quarter"] = d.dt.quarter
df["DayOfWeek"] = d.dt.day_name()
df["Hour"] = d.dt.hour
df["IsWeekend"] = d.dt.dayofweek >= 5
df["Country_Group"] = np.where(df["Country"] == "United Kingdom", "UK", "International")

section("3. ENGINEERED FEATURES")
print(df[["InvoiceDate", "Revenue", "YearMonth", "Quarter", "DayOfWeek", "Hour",
          "IsWeekend", "Country_Group"]].head())

# ------------------------------------------------------------------
# 4. PIVOT TABLES & TREND CALCULATIONS
# ------------------------------------------------------------------
# December 2011 is incomplete (data ends 9 Dec) -> flagged and excluded from trend %
last_day = df["Date"].max()
section(f"4. DATA RANGE: {df['Date'].min().date()} -> {last_day.date()}")

monthly = df.groupby("YearMonth").agg(
    revenue=("Revenue", "sum"),
    orders=("InvoiceNo", "nunique"),
    customers=("CustomerID", "nunique"),
    units=("Quantity", "sum"),
)
monthly["aov"] = monthly["revenue"] / monthly["orders"]
monthly["mom_growth_%"] = monthly["revenue"].pct_change() * 100
monthly["rolling_3m_avg"] = monthly["revenue"].rolling(3).mean()
complete = monthly.iloc[:-1]       # drop partial last month
section("4a. MONTHLY TREND (last month is partial)")
print(monthly.round(1))

h1 = complete["revenue"].iloc[:6].sum(); h2 = complete["revenue"].iloc[-6:].sum()
print(f"\nPeak month: {complete['revenue'].idxmax()} "
      f"(£{complete['revenue'].max():,.0f}); lowest: {complete['revenue'].idxmin()}")
q4 = df[df["Quarter"] == 4]["Revenue"].sum() / df["Revenue"].sum()
print(f"Nov+Oct+Dec share of total revenue (Q4): {q4:.1%}")

section("4b. PIVOT: Revenue by Month x Country_Group")
piv_cg = df.pivot_table(values="Revenue", index="YearMonth", columns="Country_Group",
                        aggfunc="sum").round(0)
print(piv_cg)

section("4c. PIVOT: Revenue by DayOfWeek x Hour (£)")
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
piv_dh = df.pivot_table(values="Revenue", index="DayOfWeek", columns="Hour",
                        aggfunc="sum", fill_value=0).reindex(order, fill_value=0)
print((piv_dh.sum(axis=1) / piv_dh.values.sum()).round(3).rename("share_of_revenue"))
print("Busiest hour:", piv_dh.sum().idxmax(), "| Busiest weekday:", piv_dh.sum(axis=1).idxmax())
print("NOTE: the dataset contains no Saturday transactions (a known quirk of this retailer data).")
print("Share of revenue between 10:00 and 15:59:", round(piv_dh.loc[:, 10:15].values.sum() / piv_dh.values.sum(), 3))

section("4d. TOP COUNTRIES (ex-UK)")
country = df.groupby("Country").agg(revenue=("Revenue", "sum"),
                                    customers=("CustomerID", "nunique"),
                                    orders=("InvoiceNo", "nunique"))
country["aov"] = country["revenue"] / country["orders"]
print(country.drop("United Kingdom").sort_values("revenue", ascending=False).head(10).round(0))
print(f"UK share of revenue: {country.loc['United Kingdom','revenue']/country['revenue'].sum():.1%}")

section("4e. TOP PRODUCTS")
prod = df.groupby("Description").agg(revenue=("Revenue", "sum"), units=("Quantity", "sum"))
print(prod.sort_values("revenue", ascending=False).head(10).round(0))

# ------------------------------------------------------------------
# 5. CUSTOMER SEGMENTATION (RFM) & CHURN
# ------------------------------------------------------------------
cust_df = df.dropna(subset=["CustomerID"]).copy()
cust_df["CustomerID"] = cust_df["CustomerID"].astype(int)
snapshot = cust_df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = cust_df.groupby("CustomerID").agg(
    recency=("InvoiceDate", lambda s: (snapshot - s.max()).days),
    frequency=("InvoiceNo", "nunique"),
    monetary=("Revenue", "sum"),
    first_purchase=("InvoiceDate", "min"),
)
rfm["R"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(r):
    if r.R >= 4 and r.F >= 4: return "Champions"
    if r.R >= 3 and r.F >= 3: return "Loyal"
    if r.R >= 4 and r.F <= 2: return "New / Recent"
    if r.R <= 2 and r.F >= 4: return "At Risk (high value)"
    if r.R <= 2 and r.F >= 3: return "At Risk"
    if r.R <= 2: return "Hibernating"
    return "Needs Attention"


rfm["Segment"] = rfm.apply(segment, axis=1)
seg = rfm.groupby("Segment").agg(
    customers=("monetary", "size"), revenue=("monetary", "sum"),
    avg_recency_days=("recency", "mean"), avg_orders=("frequency", "mean"),
    avg_spend=("monetary", "mean"))
seg["customer_%"] = seg["customers"] / seg["customers"].sum() * 100
seg["revenue_%"] = seg["revenue"] / seg["revenue"].sum() * 100
seg = seg.sort_values("revenue", ascending=False)
section("5a. RFM SEGMENTS")
print(seg.round(1))

# Pareto
sorted_m = rfm["monetary"].sort_values(ascending=False)
top20 = sorted_m.head(int(len(sorted_m) * 0.2)).sum() / sorted_m.sum()
section("5b. CONCENTRATION")
print(f"Top 20% of customers generate {top20:.1%} of identified-customer revenue")
print(f"Single-order customers: {(rfm.frequency == 1).mean():.1%}")

# Churn: customer is 'churned' if no purchase in the final 90 days,
# measured among customers who bought before that window.
cut = snapshot - pd.Timedelta(days=90)
before = cust_df[cust_df["InvoiceDate"] < cut]
active_before = set(before["CustomerID"].unique())
active_after = set(cust_df[cust_df["InvoiceDate"] >= cut]["CustomerID"].unique())
churned = active_before - active_after
churn_rate = len(churned) / len(active_before)
rf2 = before.groupby("CustomerID").agg(orders=("InvoiceNo", "nunique"),
                                       spend=("Revenue", "sum"))
rf2["churned"] = rf2.index.isin(churned)
rf2["order_band"] = pd.cut(rf2["orders"], [0, 1, 2, 4, 9, 10000],
                           labels=["1", "2", "3-4", "5-9", "10+"])
section("5c. CHURN (no purchase in final 90 days)")
print(f"Customers active before cut-off: {len(active_before):,}; churned: {len(churned):,} "
      f"({churn_rate:.1%})")
churn_by_orders = rf2.groupby("order_band", observed=True)["churned"].agg(["size", "mean"])
churn_by_orders["mean"] = (churn_by_orders["mean"] * 100).round(1)
print(churn_by_orders.rename(columns={"size": "customers", "mean": "churn_%"}))
print("Revenue (pre-cutoff) from churned customers: "
      f"£{rf2.loc[rf2.churned,'spend'].sum():,.0f} "
      f"({rf2.loc[rf2.churned,'spend'].sum()/rf2['spend'].sum():.1%})")

# Cohort retention
cust_df["OrderMonth"] = cust_df["InvoiceDate"].dt.to_period("M")
cust_df["CohortMonth"] = cust_df.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period("M")
cust_df["CohortIndex"] = (cust_df["OrderMonth"] - cust_df["CohortMonth"]).apply(lambda x: x.n)
cohort = cust_df.groupby(["CohortMonth", "CohortIndex"])["CustomerID"].nunique().unstack()
retention = cohort.divide(cohort[0], axis=0) * 100
section("5d. COHORT RETENTION - average of Jan-2011+ cohorts (Dec-2010 cohort excluded: it includes pre-existing customers)")
print(retention.iloc[1:][[1, 2, 3, 6]].mean().round(1))
print("Dec-2010 cohort for comparison:", retention.iloc[0][[1, 3, 6]].round(1).to_dict())

# ------------------------------------------------------------------
# 6. VISUALS
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))
x = complete.index.astype(str)
ax.bar(x, complete["revenue"] / 1e3, color=NAVY, alpha=0.85, label="Monthly revenue")
ax.plot(x, complete["rolling_3m_avg"] / 1e3, color=CORAL, lw=3, marker="o", label="3-month average")
ax.set_title("Revenue is flat through summer, then surges Sep-Nov (Dec 2011 partial, excluded)")
ax.set_ylabel("Revenue (£ thousands)"); ax.tick_params(axis="x", rotation=45)
ax.legend(frameon=False)
save(fig, "sales_1_monthly_trend.png")

fig, ax = plt.subplots(figsize=(11, 4.8))
sns.heatmap(piv_dh / 1e3, cmap=sns.light_palette(TEAL, as_cmap=True), linewidths=0.3,
            cbar_kws={"label": "Revenue (£ thousands)"}, ax=ax)
ax.grid(False); ax.set_title("When customers buy: weekday x hour"); ax.set_xlabel("Hour of day")
ax.set_ylabel("")
save(fig, "sales_2_weekday_hour_heatmap.png")

top_c = country.drop("United Kingdom").sort_values("revenue", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(10, 5.5))
sns.barplot(x=top_c["revenue"] / 1e3, y=top_c.index, color=TEAL, ax=ax)
ax.set_title("Top 10 international markets"); ax.set_xlabel("Revenue (£ thousands)"); ax.set_ylabel("")
save(fig, "sales_3_top_countries.png")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
s2 = seg.sort_values("revenue_%")
axes[0].barh(s2.index, s2["revenue_%"], color=NAVY, label="% of revenue")
axes[0].set_title("Revenue share by segment"); axes[0].set_xlabel("% of revenue")
axes[1].barh(s2.index, s2["customer_%"], color=GOLD)
axes[1].set_title("Customer share by segment"); axes[1].set_xlabel("% of customers")
fig.tight_layout()
save(fig, "sales_4_rfm_segments.png")

fig, ax = plt.subplots(figsize=(12, 6.5))
sns.heatmap(retention.iloc[:, :13], annot=True, fmt=".0f", cmap="YlGnBu", vmax=60,
            cbar_kws={"label": "% of cohort still buying"}, ax=ax)
ax.grid(False)
ax.set_yticklabels([str(i.get_text())[:7] for i in ax.get_yticklabels()], rotation=0)
ax.set_title("Cohort retention by first-purchase month"); ax.set_xlabel("Months since first purchase")
ax.set_ylabel("")
save(fig, "sales_5_cohort_retention.png")

cum = sorted_m.cumsum() / sorted_m.sum() * 100
fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(np.arange(1, len(cum) + 1) / len(cum) * 100, cum.values, color=CORAL, lw=3)
ax.axvline(20, ls="--", color="grey"); ax.axhline(top20 * 100, ls="--", color="grey")
ax.set_title(f"Pareto: top 20% of customers = {top20:.0%} of revenue")
ax.set_xlabel("% of customers (ranked by spend)"); ax.set_ylabel("Cumulative % of revenue")
save(fig, "sales_6_pareto.png")

# ------------------------------------------------------------------
# 7. EXPORTS
# ------------------------------------------------------------------
monthly.to_csv("output_monthly_trend.csv")
rfm.drop(columns="first_purchase").to_csv("output_rfm_customers.csv")
seg.round(2).to_csv("output_rfm_segments.csv")
print("\nDone. Charts: sales_1..6_*.png; tables: output_*.csv")
