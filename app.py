import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Energy Intensity Dashboard",
    page_icon="📊",
    layout="wide",
)

REQUIRED_COLUMNS = {
    "entity_code",
    "entity_name",
    "entity_type",
    "year",
    "energy_intensity",
}


def find_data_file() -> Path | None:
    """Search common locations for the cleaned dataset."""
    candidates = [
        Path("energy_intensity_dashboard.csv"),
        Path("data/energy_intensity_dashboard.csv"),
        Path("./energy_intensity_dashboard.csv"),
        Path("./data/energy_intensity_dashboard.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing_cols))
        )

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["energy_intensity"] = pd.to_numeric(df["energy_intensity"], errors="coerce")

    df = df.dropna(subset=["entity_name", "entity_type", "year", "energy_intensity"])
    df["year"] = df["year"].astype(int)

    df["entity_name"] = df["entity_name"].astype(str).str.strip()
    df["entity_code"] = df["entity_code"].astype(str).str.strip()
    df["entity_type"] = df["entity_type"].astype(str).str.strip()

    df = df.sort_values(["entity_type", "entity_name", "year"]).reset_index(drop=True)
    return df


def apply_global_filters(
    df: pd.DataFrame,
    entity_type_filter: str,
    year_range: tuple[int, int]
) -> pd.DataFrame:
    filtered = df[
        (df["year"] >= year_range[0]) & (df["year"] <= year_range[1])
    ].copy()

    if entity_type_filter != "All":
        filtered = filtered[filtered["entity_type"] == entity_type_filter].copy()

    return filtered


def format_value(value: float | int | None, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def kpi_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label=label, value=value, help=help_text)

def get_table_config():
    return {
        "year": st.column_config.NumberColumn("year", format="%d"),
        "energy_intensity": st.column_config.NumberColumn("energy_intensity", format="%.2f"),
        "first_year": st.column_config.NumberColumn("first_year", format="%d"),
        "latest_year": st.column_config.NumberColumn("latest_year", format="%d"),
        "latest_energy_intensity": st.column_config.NumberColumn("latest_energy_intensity", format="%.2f"),
    }

def make_line_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str = ""
):
    if x == "year":
        x_encoding = alt.X(
            f"{x}:Q",
            title="Year",
            axis=alt.Axis(format="d")
        )
    else:
        x_encoding = alt.X(
            f"{x}:Q",
            title=x.replace("_", " ").title()
        )

    chart = alt.Chart(data).mark_line(point=True).encode(
        x=x_encoding,
        y=alt.Y(f"{y}:Q", title=y.replace("_", " ").title()),
        tooltip=list(data.columns),
    )

    if color:
        chart = chart.encode(
        color=alt.Color(
            f"{color}:N",
            title=color.replace("_", " ").title(),
            legend=alt.Legend(orient="bottom")
        )
    )

    return chart.properties(title=title).interactive()


def make_bar_chart(data: pd.DataFrame, x: str, y: str, title: str = ""):
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{x}:Q", title=x.replace("_", " ").title()),
            y=alt.Y(f"{y}:N", sort="-x", title=y.replace("_", " ").title()),
            tooltip=list(data.columns),
        )
        .properties(title=title)
        .interactive()
    )


# -----------------------------
# App start
# -----------------------------
st.title("Energy Intensity Dashboard")
st.caption(
    "Interactive dashboard built from the cleaned World Bank energy intensity dataset."
)

data_file = find_data_file()

if data_file is None:
    st.error(
        "Could not find 'energy_intensity_dashboard.csv'. "
        "Place it in the project root or in a 'data/' folder."
    )
    st.stop()

try:
    df = load_data(str(data_file))
except Exception as exc:
    st.exception(exc)
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to page",
    ["Overview", "Entity Explorer", "Compare Entities", "Data Table"],
)

st.sidebar.header("Global Filters")

entity_types = sorted(df["entity_type"].dropna().unique().tolist())
default_entity_type = "Country" if "Country" in entity_types else "All"

all_options = ["All"] + entity_types
default_index = all_options.index(default_entity_type) if default_entity_type in all_options else 0

entity_type_filter = st.sidebar.selectbox(
    "Entity type",
    all_options,
    index=default_index,
)

min_year = int(df["year"].min())
max_year = int(df["year"].max())

year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered_df = apply_global_filters(df, entity_type_filter, year_range)

if entity_type_filter == "All":
    st.warning(
        "You are mixing countries with regional/aggregate entities. "
        "This is fine for exploration, but weak for direct comparison."
    )

if filtered_df.empty:
    st.warning("No data is available for the current filter combination.")
    st.stop()

latest_year = int(filtered_df["year"].max())
latest_df = filtered_df[filtered_df["year"] == latest_year].copy()

# -----------------------------
# Page 1: Overview
# -----------------------------
if page == "Overview":
    st.subheader("Overview")
    st.write(
        "Use this page to inspect the dataset at a high level using the current filters."
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_card("Records", f"{len(filtered_df):,}")

    with col2:
        kpi_card("Entities", f"{filtered_df['entity_name'].nunique():,}")

    with col3:
        kpi_card("Entities in latest year", f"{latest_df['entity_name'].nunique():,}")

    with col4:
        kpi_card("Latest year", str(latest_year))

    with col5:
        median_latest = latest_df["energy_intensity"].median()
        kpi_card(
            "Latest median intensity",
            format_value(median_latest),
            help_text="Median energy intensity for entities visible in the latest selected year.",
        )

    trend_df = (
        filtered_df.groupby("year", as_index=False)["energy_intensity"]
        .median()
        .rename(columns={"energy_intensity": "median_energy_intensity"})
    )

    st.altair_chart(
        make_line_chart(
            trend_df,
            x="year",
            y="median_energy_intensity",
            title="Median energy intensity over time",
        ),
        use_container_width=True,
    )

    st.write(f"Rankings below use the latest visible year in the current filters ({latest_year}).")

    rank_n = st.slider(
        "Number of entities in rankings",
        min_value=5,
        max_value=20,
        value=10,
        step=1,
    )

    lowest = latest_df.nsmallest(rank_n, "energy_intensity")[["entity_name", "energy_intensity"]]
    highest = latest_df.nlargest(rank_n, "energy_intensity")[["entity_name", "energy_intensity"]]

    c1, c2 = st.columns(2)

    with c1:
        st.altair_chart(
            make_bar_chart(
                lowest,
                x="energy_intensity",
                y="entity_name",
                title=f"Lowest energy intensity entities in {latest_year}",
            ),
            use_container_width=True,
        )

    with c2:
        st.altair_chart(
            make_bar_chart(
                highest,
                x="energy_intensity",
                y="entity_name",
                title=f"Highest energy intensity entities in {latest_year}",
            ),
            use_container_width=True,
        )

# -----------------------------
# Page 2: Entity Explorer
# -----------------------------
elif page == "Entity Explorer":
    st.subheader("Entity Explorer")

    entities = sorted(filtered_df["entity_name"].unique().tolist())
    selected_entity = st.selectbox("Select one entity", entities)

    entity_df = filtered_df[filtered_df["entity_name"] == selected_entity].copy()

    if entity_df.empty:
        st.warning("No data is available for the selected entity.")
        st.stop()

    entity_df = entity_df.sort_values("year")
    first_row = entity_df.iloc[0]
    last_row = entity_df.iloc[-1]

    absolute_change = last_row["energy_intensity"] - first_row["energy_intensity"]

    if first_row["energy_intensity"] != 0:
        percent_change = (absolute_change / first_row["energy_intensity"]) * 100
        delta_text = f"{percent_change:,.2f}%"
    else:
        delta_text = "N/A"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("First year", str(int(first_row["year"])))

    with c2:
        kpi_card("First value", format_value(first_row["energy_intensity"]))

    with c3:
        kpi_card("Latest value", format_value(last_row["energy_intensity"]))

    with c4:
        st.metric(
            "Change from first to latest",
            format_value(absolute_change),
            delta=delta_text,
        )

    st.altair_chart(
        make_line_chart(
            entity_df[["year", "energy_intensity"]],
            x="year",
            y="energy_intensity",
            title=f"Energy intensity trend for {selected_entity}",
        ),
        use_container_width=True,
    )

    st.dataframe(
        entity_df[["entity_code", "entity_name", "entity_type", "year", "energy_intensity"]],
        use_container_width=True,
        hide_index=True,
        column_config=get_table_config(),
    )

# ----------------------------
# Page 3: Compare Entities
# ----------------------------
elif page == "Compare Entities":
    st.subheader("Compare Entities")

    entities = sorted(filtered_df["entity_name"].dropna().unique().tolist())
    default_selection = entities[:3] if len(entities) >= 3 else entities

    selected_entities = st.multiselect(
        "Select up to 5 entities",
        entities,
        default=default_selection,
        max_selections=5,
    )

    if len(selected_entities) < 2:
        st.info("Select at least 2 entities to compare.")
        st.stop()

    comparison_df = filtered_df[
        filtered_df["entity_name"].isin(selected_entities)
    ].copy()

    st.altair_chart(
        make_line_chart(
            comparison_df,
            x="year",
            y="energy_intensity",
            color="entity_name",
            title="Energy intensity comparison over time",
        ),
        use_container_width=True,
    )

    year_counts = (
        comparison_df.groupby("year")["entity_name"]
        .nunique()
        .reset_index(name="entity_count")
    )

    common_years = year_counts[
        year_counts["entity_count"] == len(selected_entities)
    ]["year"]

    if common_years.empty:
        st.warning(
            "No common year is available for all selected entities within the current filters."
        )
        st.stop()

    comparison_year = int(common_years.max())

    latest_comparison = comparison_df[
        comparison_df["year"] == comparison_year
    ].copy()

    st.caption(
        f"Bar chart uses the latest common year shared by all selected entities: {comparison_year}"
    )

    comparison_bar = (
        alt.Chart(latest_comparison)
        .mark_bar()
        .encode(
            x=alt.X("energy_intensity:Q", title="Energy Intensity"),
            y=alt.Y("entity_name:N", sort="-x", title="Entity Name"),
            color=alt.Color("entity_name:N", legend=None),
            tooltip=["entity_name", "year", "energy_intensity"],
        )
        .properties(title=f"Latest common year comparison ({comparison_year})")
        .interactive()
    )

    st.altair_chart(comparison_bar, use_container_width=True)

    st.dataframe(
        latest_comparison[["entity_name", "year", "energy_intensity"]]
        .sort_values("energy_intensity", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config=get_table_config(),
    )
# -----------------------------
# Page 4: Data Table
# -----------------------------
elif page == "Data Table":
    st.subheader("Data Table")
    st.write("This page is mainly for transparency, spot-checking, and testing evidence.")

    st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config=get_table_config(),
)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name="filtered_energy_intensity_data.csv",
        mime="text/csv",
    )

    summary_df = (
        filtered_df.groupby(["entity_name", "entity_type"], as_index=False)
        .agg(
            first_year=("year", "min"),
            latest_year=("year", "max"),
            latest_energy_intensity=("energy_intensity", "last"),
        )
        .sort_values(["entity_type", "entity_name"])
    )

    st.markdown("#### Summary by entity")
    st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    column_config=get_table_config(),
)