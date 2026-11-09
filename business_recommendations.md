# Customer Churn & Sales Trend Analysis: Business Recommendations

**Dataset:** UCI Online Retail, a UK-based online gift retailer. 541,909 transaction lines, 1 Dec 2010 to 9 Dec 2011. After cleaning: 522,537 lines, of which about 75% have a CustomerID.

## Headline findings
| Area | Finding |
|---|---|
| Seasonality | Sep-Nov brought in 35% of all revenue. November (£1.45M) was 2.0x August (£724K). Revenue was flat at £0.5-0.75M a month from Jan to Aug. |
| Customer concentration | The top 20% of customers generate 74.6% of identified revenue. Champions are 26% of customers and 67% of revenue. |
| Churn | 43.2% of customers who bought before the last 90 days did not return in them. |
| Churn vs. orders | Churn falls with order count: 62.5% (1 order), 47.8% (2), 31.7% (3-4), 13.9% (5-9), 3.8% (10+). |
| Retention | On average only about 19% of a new cohort buys again in month 1 (Jan-2011+ cohorts). |
| Timing | 74% of revenue lands between 10:00 and 15:59. Tuesday and Thursday are the strongest days, Sunday is the weakest (7.8%). |
| Geography | The UK is 85% of revenue. The Netherlands, EIRE and Australia have very few customers (9, 3, 9) but huge average orders (£960 to £3,053), so they look like wholesale accounts. |

## Recommendations
1. **Protect the Champions (1,136 customers, 67% of revenue).** Add VIP perks such as early access to new lines, dedicated support and volume pricing. Losing a handful of them costs more than losing hundreds of one-time buyers.
2. **Run a win-back campaign for "At Risk (high value)" (273 customers).** They averaged 4.9 orders and £1,699 spend but have been silent for about 138 days. They represent £464K of historical revenue, so personalised outreach has a clear payoff.
3. **Get customers to the third order.** Churn drops from 62.5% to 31.7% once a customer reaches 3-4 orders. Trigger a post-purchase flow (reorder reminder, bundle offer) 30-60 days after a first order, when 1-order customers are most at risk.
4. **Plan the year around Sep-Nov.** Lock in stock and logistics by August, launch Christmas campaigns in early September, and treat November as a capacity-planning event. Smooth the troughs (Feb £508K, Apr £515K) with promotions or B2B outreach.
5. **Time marketing to buying behaviour.** Send emails and promotions on Tuesday and Thursday mornings. Test Sunday-specific offers, since Sunday is the weakest day (7.8% of revenue).
6. **Treat international markets in two ways.** Assign account managers to the high-value wholesale-style markets (Netherlands, EIRE, Australia). Use scalable marketing in Germany and France, which have 94 and 87 customers and average orders of about £465-£480.
7. **Fix customer tracking.** About a quarter of lines have no CustomerID (likely guest checkout). Capturing an email or ID would bring those buyers into retention analysis and win-back campaigns.

## Caveats
- The data covers one year, so seasonality is observed once. December 2011 is partial and was excluded from trend percentages.
- There are no Saturday transactions in this dataset, so weekday patterns should be read with that in mind.
- "Churn" is defined as no purchase in the final 90 days. Gift-focused buyers may naturally buy once or twice a year, so this can overstate true churn.
- The Dec-2010 cohort is excluded from the retention average because it includes customers who joined before the data starts.
- Many customers appear to be trade buyers, so spend is skewed by a small number of very large accounts.
