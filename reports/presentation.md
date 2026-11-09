# 🎙️ Executive Presentation Script: The 10,000 Customer Reality

**Project:** Customer Messy Data EDA & Strategic Intelligence  
**Author:** Levi Flores (`@levifvy`)  
**Target Audience:** Chief Executive Officer (CEO), Chief Marketing Officer (CMO), Chief Technology Officer (CTO)  
**Target Duration:** 5 minutes (678 spoken words at ~136 words/minute)  
**Format:** Non-Technical Storytelling Slide Deck with Speaker Script  

---

## ⏱️ Presentation Timing & Structure Overview

| Slide | Section / Objective | Time Window | Spoken Words | Primary Visual |
|---|---|---|---|---|
| **Slide 1** | **The Hook:** The 10,000 Customer Illusion | 0:00 – 0:45 | 111 words | Title Banner & Macro KPI Scorecard |
| **Slide 2** | **The Reality:** Data Quality & The 40.7% Trap | 0:45 – 1:30 | 111 words | `m2_iqr_outlier_boxplots.png` |
| **Slide 3** | **Finding 1 (`Q1`):** Who Are They? Urban Indian Concentration | 1:30 – 2:30 | 154 words | `a1_raw_vs_normalized_metrics.png` |
| **Slide 4** | **Finding 2 (`Q2`):** What Do They Spend? The Uniform Spender | 2:30 – 3:30 | 116 words | `e5_bivariate_spend_by_demographics.png` |
| **Slide 5** | **Finding 3 (`Q3`):** Do They Return? Retention & The Reachability Void | 3:30 – 4:15 | 109 words | `m6_signup_and_activity_trends.png` |
| **Slide 6** | **The Ask:** 3 Strategic Recommendations & Financial Impact | 4:15 – 5:00 | 77 words | Roadmap Matrix & Closing Slide |

---

## 📽️ Slide-by-Slide Script & Visual Guide

### Slide 1: The 10,000 Customer Illusion
- **Slide Title:** *Beyond the Headcount: What 10,000 Raw Records Actually Tell Us*
- **Visual:** Executive KPI Scorecards — 10,000 Registered Records | $2,460 Median Spend | 43.9% Reachability.
- **Timing:** `[0:00 – 0:45]` (45 seconds — 111 words)

> **Speaker Script:**  
> "Good morning. When leadership looks at our database, the top-line number looks reassuring: 10,000 registered customer accounts. On paper, it suggests a thriving, mature digital business.
>
> But when our data team looked beneath the surface, we discovered a completely different reality. 
> 
> Before we could answer where our revenue comes from or who our most loyal customers are, we had to confront a critical truth: more than 40% of the raw data was corrupted by invalid sentinels, placeholder codes, and contradictory entries.
>
> Today, I will walk you through what happens when we filter out the noise, what our real customer base looks like, and the three strategic decisions we must make immediately."

---

### Slide 2: The Reality: Cleaning the 40.7% Corruption Trap
- **Slide Title:** *Data Integrity Audit: Separating Genuine Customers from Noise*
- **Visual:** `![Data Cleaning & Outlier Remediation](../assets/charts/m2_iqr_outlier_boxplots.png)`
- **Timing:** `[0:45 – 1:30]` (45 seconds — 111 words)

> **Speaker Script:**  
> "Our first breakthrough was forensic data cleaning. We found customers recorded as minus-5 years old, others supposedly aged 200, and thousands of purchase entries hardcoded as minus-999 or N/A. 
>
> If an analyst had simply taken raw averages, our business decisions would have been completely misled. By applying rigorous domain rules, we identified that only 2,466 customers have verified purchase amounts, and 2,465 have valid ages.
>
> Crucially, we proved that replacing missing numbers with crude medians would artificially cut our data variance in half. Instead, we preserved statistical integrity by building transparent data flags. 
>
> With clean ground truth established, we can now answer leadership's three core business questions with complete confidence."

---

### Slide 3: Finding 1 (`Q1`): Who Are Our Customers?
- **Slide Title:** *Demographic Discovery: The Urban Indian Power Base*
- **Visual:** `![Normalized Geographic Metrics](../assets/charts/a1_raw_vs_normalized_metrics.png)`
- **Timing:** `[1:30 – 2:30]` (60 seconds — 154 words)

> **Speaker Script:**  
> "First: Who are our customers, and where are they located?
>
> The data reveals that our active customer base is an established, middle-aged cohort, with a median age of 43 years (mean 43.7), evenly split between men (3,800) and women (3,745). 
>
> Geographically, every known city is one of eight large Indian metropolitan centers, and the base is spread evenly across them: each holds between 1,056 and 1,144 accounts, led by Hyderabad, Mumbai and Pune. While international country labels were mistakenly attached to many accounts in the raw files, every valid city tells a clear story: we are an urban Indian retail powerhouse.
>
> Furthermore, when we normalize revenue per 1,000 customers, we see remarkable commercial consistency across cities: each metropolitan hub generates between 2.29 million dollars (Kolkata) and 2.56 million dollars (Chennai) per 1,000 buyers, and that gap is not statistically significant. Our customers may live in different cities, but their commercial value is the same."

---

### Slide 4: Finding 2 (`Q2`): What Do They Spend?
- **Slide Title:** *Commercial Analysis: High-Value Spenders Are Demographically Blind*
- **Visual:** `![Spend by Demographics](../assets/charts/e5_bivariate_spend_by_demographics.png)`
- **Timing:** `[2:30 – 3:30]` (60 seconds — 116 words)

> **Speaker Script:**  
> "Second: What drives customer spend, and who are our VIPs?
>
> Our typical buyer spends a median of $2,460 per transaction, with high spenders exceeding $3,500. But here is the most surprising takeaway for our marketing strategy: spend is virtually uncorrelated with age, gender, or city.
>
> Younger shoppers aged 18 to 29 spend statistically the same as customers over 60, and men and women spend statistically the same amounts. 
>
> This means traditional demographic targeting is leaving money on the table. We should not be segmenting our marketing campaigns by age or gender. Instead, the lever is the spend tier itself: 724 customers already spend above $3,500, and they deserve dedicated retention journeys regardless of their demographic bracket."

---

### Slide 5: Finding 3 (`Q3`): Do They Return?
- **Slide Title:** *Customer Experience: The Reachability Void and The Rating Paradox*
- **Visual:** `![Signup Cohorts and Activity Trends](../assets/charts/m6_signup_and_activity_trends.png)`
- **Timing:** `[3:30 – 4:15]` (45 seconds — 109 words)

> **Speaker Script:**  
> "Third: Can we reach them, and are they satisfied?
>
> Here we uncover our largest operational risk. Fifty-six percent of our customer base is completely unreachable—they lack both a valid email and a working phone number. Only 6.3% can be reached on both channels.
>
> Furthermore, in customer satisfaction, half of all valid reviews recorded an anomalous score of 10 on a standard 1-to-5 survey scale, most likely a survey-scale configuration error that we should confirm with the survey owner. Among genuine ratings on the 1-to-5 scale, the average score is 2.96, reflecting lukewarm sentiment.
>
> Our retention bridge is broken because we cannot reliably communicate with over half our audience."

---

### Slide 6: The Strategic Ask: 3 Actionable Recommendations
- **Slide Title:** *Strategic Roadmap: Three Immediate Interventions*
- **Visual:** Three-Pillar Action Plan Matrix with Department Owners & Expected Business Outcomes.
- **Timing:** `[4:15 – 5:00]` (45 seconds — 77 words)

> **Speaker Script:**  
> "To monetize these discoveries, we propose three immediate initiatives:
>
> 1. **Engineering:** Deploy real-time input validation at checkout to eliminate fake phone numbers and malformed emails, capturing the 56% unreachable revenue base.
> 2. **Marketing:** Shift ad spend from demographic buckets to behavioral spend tiers, deploying VIP retention journeys for all buyers above $3,500.
> 3. **Customer Experience:** Redesign our mobile post-purchase feedback survey to fix the 10-point scale bug and actively re-engage detractors.
>
> Thank you. I welcome your questions."
