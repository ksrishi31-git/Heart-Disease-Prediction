import pandas as pd

df = pd.read_csv("datasets/heart.csv")
print("Shape:", df.shape)
print("\nColumns:", list(df.columns))
print("\nDtypes:\n", df.dtypes)
print("\nTarget distribution:\n", df["target"].value_counts())
print("\nMissing values:\n", df.isna().sum().to_dict())

categorical = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]
for col in categorical:
    print(f"\n{col} values: {sorted(df[col].unique())}")

print("\nNumerical ranges:")
for col in ["age", "trestbps", "chol", "thalach", "oldpeak"]:
    print(f"  {col}: min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}")

print("\nDuplicated rows:", df.duplicated().sum())
