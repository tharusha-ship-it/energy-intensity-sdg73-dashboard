import pandas as pd

# 1. Load raw dataset
df = pd.read_csv("data/Energy Intensity Level of primary Energy.csv")

# 2. Keep only the columns needed
clean_df = df[["REF_AREA", "REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].copy()

# 3. Rename columns
clean_df = clean_df.rename(columns={
    "REF_AREA": "entity_code",
    "REF_AREA_LABEL": "entity_name",
    "TIME_PERIOD": "year",
    "OBS_VALUE": "energy_intensity"
})
# 4. Clean text fields
clean_df["entity_code"] = clean_df["entity_code"].astype(str).str.strip()
clean_df["entity_name"] = clean_df["entity_name"].astype(str).str.strip()

# 5. Fix data types
clean_df["year"] = pd.to_numeric(clean_df["year"], errors="coerce").astype("Int64")
clean_df["energy_intensity"] = pd.to_numeric(clean_df["energy_intensity"], errors="coerce")

# 6. Define reference-area labels that are NOT individual countries
aggregate_labels = {
    "Arab World",
    "Caribbean small states",
    "Central Europe and the Baltics",
    "Early-demographic dividend",
    "East Asia & Pacific",
    "East Asia & Pacific (IDA & IBRD)",
    "East Asia & Pacific (excluding high income)",
    "Eastern & Southern Africa",
    "Euro area",
    "Europe & Central Asia",
    "Europe & Central Asia (IDA & IBRD)",
    "Europe & Central Asia (excluding high income)",
    "European Union",
    "Fragile and conflict affected situations",
    "Heavily indebted poor countries (HIPC)",
    "High income",
    "IBRD only",
    "IDA & IBRD total",
    "IDA blend",
    "IDA only",
    "IDA total",
    "Late-demographic dividend",
    "Latin America & Caribbean",
    "Latin America & Caribbean (excluding high income)",
    "Latin America & Caribbean (IDA & IBRD)",
    "Least developed countries: UN classification",
    "Low & middle income",
    "Low income",
    "Lower middle income",
    "Middle East & North Africa",
    "Middle East & North Africa (IDA & IBRD)",
    "Middle East, North Africa, Afghanistan & Pakistan",
    "Middle East, North Africa, Afghanistan & Pakistan (IDA & IBRD)",
    "Middle East, North Africa, Afghanistan & Pakistan (excluding high income)",
    "Middle East & North Africa (excluding high income)",
    "Middle income",
    "North America",
    "OECD members",
    "Other small states",
    "Pacific island small states",
    "Post-demographic dividend",
    "Pre-demographic dividend",
    "Small states",
    "South Asia",
    "South Asia (IDA & IBRD)",
    "Sub-Saharan Africa",
    "Sub-Saharan Africa (IDA & IBRD)",
    "Sub-Saharan Africa (excluding high income)",
    "Upper middle income",
    "Western & Central Africa",
    "World"
}

# 7. Add extra column
clean_df["entity_type"] = clean_df["entity_name"].apply(
    lambda x: "Region/Aggregate" if x in aggregate_labels else "Country"
)

# 8. Reorder columns
clean_df = clean_df[[
    "entity_code",
    "entity_name",
    "entity_type",
    "year",
    "energy_intensity"
]]

# 9. Validation checks
print("Shape:", clean_df.shape)
print("\nMissing values:")
print(clean_df.isnull().sum())

print("\nDuplicate entity-year rows:",
      clean_df.duplicated(subset=["entity_code", "year"]).sum())

print("\nYear range:",
      clean_df["year"].min(), "to", clean_df["year"].max())

print("\nUnique entities:",
      clean_df["entity_name"].nunique())

print("\nEntity type counts:")
print(clean_df["entity_type"].value_counts())

print("\nUnique Region/Aggregate labels:")
print(sorted(clean_df.loc[
    clean_df["entity_type"] == "Region/Aggregate", "entity_name"
].unique().tolist()))

# 10. Save new processed file
clean_df.to_csv("energy_intensity_dashboard.csv", index=False)

print("\nPreview:")
print(clean_df.head())