---
name: data-cleaning
description: >-
  Execute reproducible data quality diagnosis, sentinel value remediation, strict schema casting,
  documented imputation decisions, and cleaning audit table generation for the Customer Messy Data
  EDA project. Activate this skill when performing tasks E1, E2, E3, M1, A3, A7, X1, or X4.
---

# Data Cleaning & Quality Remediation Skill (`data-cleaning`)

This skill defines the mandatory step-by-step protocol for `DataCleanerAgent` when diagnosing, cleaning, validating, and modularizing transformations on `data/raw/messy_customer_data.csv`.

---

## 1. Golden Rules of Data Cleaning

1. **Raw Data Immutability:** Never modify or overwrite `data/raw/messy_customer_data.csv`. Always load from `data/raw/` and write outputs to `data/processed/`.
2. **Two-Pass Loading for Diagnosis:**
   - **Pass 1 (Literal String Audit):** Load with `pd.read_csv(RAW_PATH, keep_default_na=False)` to distinguish literal empty strings (`""`) from string sentinels (`"N/A"`, `"not_a_date"`, `"missing"`, `"abc123"`, `"0"`).
   - **Pass 2 (Typed Conversion):** Apply domain sentinel masks defined in [`specs/ontology.md`](../../../specs/ontology.md) before casting to `float64`, `datetime64[us]`, `category`, or `bool`.
3. **Preserve Variance Over Blind Imputation:** When missingness exceeds `50%` (as in `age` at `75.35%` and `purchase_amount` at `75.34%`), **never overwrite the primary column with mean/median imputation**, as doing so collapses the standard deviation by $\sim 50\%$ and distorts bivariate correlations. Instead:
   - Keep `np.nan` in the primary analytical column (`age`, `purchase_amount`, `feedback_score`).
   - Provide explicit boolean missingness indicators (`is_age_missing`, `is_purchase_missing`) and optional suffix columns (`age_imputed_median`) only when required for specific downstream algorithms.

---

## 2. Step-by-Step Cleaning Protocol

### Step 1: Standardize Column Names (`snake_case`)
Rename all 12 raw columns deterministically:
```python
COLUMN_MAPPING: dict[str, str] = {
    "CustomerID": "customer_id",
    "Name": "name",
    "Gender": "gender",
    "Age": "age",
    "City": "city",
    "Signup_Date": "signup_date",
    "Last_purchase_date": "last_purchase_date",
    "purchase_amount": "purchase_amount",
    "feedback_score": "feedback_score",
    "email": "email",
    "Phone_number": "phone_number",
    "Country": "country",
}
```

### Step 2: Reconstruct Primary Key (`customer_id`)
Verify that non-empty `CustomerID` values (`'C2'`, `'3'`, `'C4'`, `'5'`, etc.) match the 1-based row index, then assign a uniform 5-digit padded identifier:
```python
df["customer_id"] = [f"C{i:05d}" for i in range(1, len(df) + 1)]
assert df["customer_id"].is_unique, "Primary key customer_id must be 100% unique"
```

### Step 3: Clean Categorical & Text Attributes (`name`, `gender`, `city`, `country`)
Normalize whitespace and casing, unify synonymous labels, and assign `'Unknown'` to missing values:
```python
df["name"] = df["name"].astype(str).str.strip().str.title().replace({"": "Unknown", "Nan": "Unknown"})

GENDER_MAP = {"m": "Male", "male": "Male", "f": "Female", "female": "Female", "": "Unknown"}
df["gender"] = (
    df["gender"].astype(str).str.strip().str.lower().map(GENDER_MAP).fillna("Unknown").astype("category")
)

df["city"] = df["city"].astype(str).str.strip().str.title().replace({"": "Unknown", "Nan": "Unknown"}).astype("category")
df["country"] = df["country"].astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown"}).astype("category")
```

### Step 4: Remediate Numeric Sentinels (`age`, `purchase_amount`, `feedback_score`)
Apply domain range filters from [`specs/ontology.md`](../../../specs/ontology.md):
```python
# Age: valid human customer range [18, 100]; sentinels are -5 and 200
age_num = pd.to_numeric(df["age"], errors="coerce")
df["age"] = age_num.where((age_num >= 18) & (age_num <= 100), np.nan)

# Purchase amount: strictly positive (> 0); sentinels are -999 and 'N/A'
amt_num = pd.to_numeric(df["purchase_amount"].replace({"N/A": np.nan, "-999": np.nan, "": np.nan}), errors="coerce")
df["purchase_amount"] = amt_num.where(amt_num > 0, np.nan)

# Feedback score: valid ratings >= 1 (1..5 and 10); sentinel is -1
fb_num = pd.to_numeric(df["feedback_score"].replace({"-1": np.nan, "": np.nan}), errors="coerce")
df["feedback_score"] = fb_num.where(fb_num >= 1, np.nan)
```

### Step 5: Parse Dates & Flag Chronological Inversions (`signup_date`, `last_purchase_date`)
```python
df["signup_date"] = pd.to_datetime(
    df["signup_date"].replace({"not_a_date": np.nan, "": np.nan}),
    format="%d/%m/%Y",
    errors="coerce",
)
df["last_purchase_date"] = pd.to_datetime(
    df["last_purchase_date"].replace({"missing": np.nan, "": np.nan}),
    format="%d/%m/%Y",
    errors="coerce",
)
df["is_date_inverted"] = (
    df["signup_date"].notna()
    & df["last_purchase_date"].notna()
    & (df["last_purchase_date"] < df["signup_date"])
)
```

### Step 6: Validate Contact Channels (`email`, `phone_number`)
```python
email_s = df["email"].astype(str).str.strip()
df["email"] = email_s.where(email_s.str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True), np.nan)
df["has_valid_email"] = df["email"].notna()

phone_s = df["phone_number"].astype(str).str.strip()
df["phone_number"] = phone_s.where(phone_s.str.match(r"^\d{10}$"), np.nan)
df["has_valid_phone"] = df["phone_number"].notna()
```

---

## 3. Mandatory Audit Table Generation

Whenever `DataCleanerAgent` updates cleaning logic (tasks `E2`, `M1`, `A3`, `X4`), it must output a summary audit table quantifying:
1. `Column` (raw and cleaned name)
2. `Blank Count ("")`
3. `Sentinel / Corrupted Count`
4. `Total Invalid (%)`
5. `Valid Count` & `Valid (%)`
6. `Remediation Rule & Analytical Justification`

---

## 4. Verification & Post-Cleaning Assertions

Run these assertions before saving any dataset to `data/processed/`:
```python
assert len(df) == 10000, f"Expected 10,000 rows, got {len(df)}"
assert df["customer_id"].is_unique, "customer_id must have zero duplicates"
assert df["age"].dropna().between(18, 100).all(), "Out-of-range values remain in age"
assert (df["purchase_amount"].dropna() > 0).all(), "Non-positive values remain in purchase_amount"
assert set(df["gender"].unique()).issubset({"Male", "Female", "Unknown"}), "Unmapped gender labels remain"
```
