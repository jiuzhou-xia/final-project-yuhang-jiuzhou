import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Chicago Housing Affordability Dashboard", layout="wide")
st.title("Chicago Housing Affordability Dashboard")
st.caption("Core metrics: PIR / PTI, with API as auxiliary metric")

@st.cache_data
def load_data():
    return pd.read_csv("../output/merged_annual_updated.csv")


def recompute_metrics(df, p_base=300000, down_payment=0.2, term_years=30, rate_shock_bp=0):
    out = df.copy()
    base_hpi = out["home_price_index"].iloc[0]
    out["home_price_proxy"] = p_base * (out["home_price_index"] / base_hpi)

    out["mortgage_rate_scn"] = out["mortgage_rate"] + (rate_shock_bp / 100.0)
    out["r_month"] = (out["mortgage_rate_scn"] / 100.0) / 12.0

    n = term_years * 12
    out["loan_amount"] = out["home_price_proxy"] * (1 - down_payment)

    out["mortgage_payment_monthly"] = out["loan_amount"] * (
        out["r_month"] * (1 + out["r_month"]) ** n / ((1 + out["r_month"]) ** n - 1)
    )

    out["income_monthly"] = out["income_median"] / 12.0
    out["PIR"] = out["mortgage_payment_monthly"] / out["income_monthly"]
    out["PTI"] = out["home_price_proxy"] / out["income_median"]

    out["API"] = out["home_price_index"] * (out["mortgage_rate_scn"] / 100.0) / out["income_pc_real"]

    base_pir = out["PIR"].iloc[0]
    out["PIR_index"] = out["PIR"] / base_pir * 100
    return out


df = load_data().sort_values("year").reset_index(drop=True)
df = df[df["year"] >= 2000]

st.sidebar.header("Controls")
min_y, max_y = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", min_value=min_y, max_value=max_y, value=(min_y, max_y))

p_base = st.sidebar.slider("Anchored base home price ($)", 150000, 800000, 300000, 10000)
down_payment = st.sidebar.slider("Down payment ratio", 0.05, 0.40, 0.20, 0.01)
rate_shock_bp = st.sidebar.slider("Mortgage-rate shock (basis points)", -200, 200, 0, 25)

show_animation = st.sidebar.checkbox("Enable animated trend chart", value=True)

calc = recompute_metrics(df, p_base=p_base, down_payment=down_payment, term_years=30, rate_shock_bp=rate_shock_bp)
flt = calc[(calc["year"] >= year_range[0]) & (calc["year"] <= year_range[1])].copy()

# ===== KPI =====
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Latest PIR", f"{flt['PIR'].iloc[-1]:.2f}")
with k2:
    st.metric("Latest PTI", f"{flt['PTI'].iloc[-1]:.2f}")
with k3:
    st.metric("Latest Mortgage Rate", f"{flt['mortgage_rate_scn'].iloc[-1]:.2f}%")
with k4:
    st.metric("Latest Income Median", f"${flt['income_median'].iloc[-1]:,.0f}")

# ===== Trend chart =====
st.subheader("Trend Overview")
long_df = pd.DataFrame({
    "year": np.concatenate([flt["year"].values] * 3),
    "series": (["Home Price Index"] * len(flt)) + (["Mortgage Rate"] * len(flt)) + (["Income Median"] * len(flt)),
    "value": np.concatenate([
        (flt["home_price_index"] / flt["home_price_index"].iloc[0] * 100).values,
        (flt["mortgage_rate_scn"] / flt["mortgage_rate_scn"].iloc[0] * 100).values,
        (flt["income_median"] / flt["income_median"].iloc[0] * 100).values,
    ])
})

if show_animation:
    y_min, y_max = int(flt["year"].min()), int(flt["year"].max())
    years_sorted = sorted(flt["year"].unique())
    year_selected = st.slider("Trend year", min_value=y_min, max_value=y_max, value=int(years_sorted[0]), key="trend_year")
    range_half = st.slider("Range (± years)", min_value=1, max_value=15, value=5, key="trend_range")
    w_left = max(y_min, year_selected - range_half)
    w_right = min(y_max, year_selected + range_half)
    sub = flt[(flt["year"] >= w_left) & (flt["year"] <= w_right)]
    long_df_frame = pd.DataFrame({
        "year": np.concatenate([sub["year"].values] * 3),
        "series": (["Home Price Index"] * len(sub)) + (["Mortgage Rate"] * len(sub)) + (["Income Median"] * len(sub)),
        "value": np.concatenate([
            (sub["home_price_index"] / flt["home_price_index"].iloc[0] * 100).values,
            (sub["mortgage_rate_scn"] / flt["mortgage_rate_scn"].iloc[0] * 100).values,
            (sub["income_median"] / flt["income_median"].iloc[0] * 100).values,
        ]),
    })
    v_min, v_max = long_df["value"].min() * 0.9, long_df["value"].max() * 1.1
    chart_trend = (
        alt.Chart(long_df_frame)
        .mark_line()
        .encode(x="year", y=alt.Y("value", scale=alt.Scale(domain=[v_min, v_max])), color="series")
        .properties(title="Normalized Drivers (base=100)", height=300)
    )
    st.altair_chart(chart_trend, use_container_width=True)
else:
    v_min, v_max = long_df["value"].min() * 0.9, long_df["value"].max() * 1.1
    chart_trend = (
        alt.Chart(long_df)
        .mark_line()
        .encode(x="year", y=alt.Y("value", scale=alt.Scale(domain=[v_min, v_max])), color="series")
        .properties(title="Normalized Drivers (base=100)", height=300)
    )
    st.altair_chart(chart_trend, use_container_width=True)

# ===== Core affordability chart =====
st.subheader("Core Affordability Metrics")
base_core = alt.Chart(flt)
c_pir = base_core.mark_line(point=True, color="#1f77b4").encode(alt.X("year"), alt.Y("PIR", title="PIR"))
c_pti = base_core.mark_line(point=True, color="#ff7f0e").encode(alt.X("year"), alt.Y("PTI", title="PTI", axis=alt.Axis(orient="right")))
chart_core = alt.layer(c_pir, c_pti).resolve_scale(y="independent").properties(title="PIR / PTI (blue: PIR left, orange: PTI right)", height=300)
st.altair_chart(chart_core, use_container_width=True)


# ===== Correlation heatmap =====
# --- Fix NaN in bubble size ---
sc_df = flt.copy()
sc_df["income_median"] = pd.to_numeric(sc_df["income_median"], errors="coerce")
sc_df = sc_df.dropna(subset=["mortgage_rate_scn", "PIR", "income_median"])
sc_df = sc_df[sc_df["income_median"] > 0]
# ===== Scatter =====
st.subheader("Rate vs PIR")
chart_sc = (
    alt.Chart(sc_df)
    .mark_circle()
    .encode(
        alt.X("mortgage_rate_scn", title="Mortgage Rate (%)"),
        alt.Y("PIR", title="PIR"),
        size=alt.Size("income_median", title="median income"),
        tooltip=["year", "home_price_index", "income_median", "mortgage_rate_scn", "PIR"],
    )
    .properties(title="Mortgage Rate vs PIR (bubble size = median income)", height=300)
)
st.altair_chart(chart_sc, use_container_width=True)

# ===== Data table =====
st.subheader("Data (filtered)")
show_cols = [
    "year", "home_price_index", "mortgage_rate_scn", "income_median", "permits",
    "home_price_proxy", "mortgage_payment_monthly", "PIR", "PTI", "PIR_index", "API"
]
st.dataframe(flt[show_cols].reset_index(drop=True), use_container_width=True)

csv = flt[show_cols].to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv, file_name="chicago_affordability_filtered.csv", mime="text/csv")
