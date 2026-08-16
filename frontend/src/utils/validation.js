export const FEATURES = [
  { name: "age", kind: "numeric", label: "Age", unit: "years", min: 1, max: 120, step: 1, helper: "Patient's age in years." },
  { name: "sex", kind: "categorical", label: "Sex", options: [{ value: "Male", label: "Male" }, { value: "Female", label: "Female" }], helper: "Biological sex." },
  { name: "cp", kind: "categorical", label: "Chest pain type", options: [{ value: "Typical angina", label: "Typical angina" }, { value: "Atypical angina", label: "Atypical angina" }, { value: "Non-anginal pain", label: "Non-anginal pain" }, { value: "Asymptomatic", label: "Asymptomatic" }], helper: "Type of chest pain reported." },
  { name: "trestbps", kind: "numeric", label: "Resting blood pressure", unit: "mm Hg", min: 90, max: 200, step: 1, helper: "Resting blood pressure on admission." },
  { name: "chol", kind: "numeric", label: "Serum cholesterol", unit: "mg/dl", min: 100, max: 600, step: 1, helper: "Serum cholesterol level." },
  { name: "fbs", kind: "categorical", label: "Fasting blood sugar > 120 mg/dl", options: [{ value: "Yes", label: "Yes" }, { value: "No", label: "No" }], helper: "Whether fasting blood sugar exceeds 120 mg/dl." },
  { name: "restecg", kind: "categorical", label: "Resting ECG result", options: [{ value: "Normal", label: "Normal" }, { value: "ST-T wave abnormality", label: "ST-T wave abnormality" }, { value: "Left ventricular hypertrophy", label: "Left ventricular hypertrophy" }], helper: "Result of the resting electrocardiogram." },
  { name: "thalach", kind: "numeric", label: "Maximum heart rate achieved", unit: "bpm", min: 60, max: 220, step: 1, helper: "Highest heart rate reached during exercise." },
  { name: "exang", kind: "categorical", label: "Exercise-induced angina", options: [{ value: "Yes", label: "Yes" }, { value: "No", label: "No" }], helper: "Angina triggered by exercise." },
  { name: "oldpeak", kind: "numeric", label: "ST depression (oldpeak)", unit: "", min: 0, max: 6.5, step: 0.1, helper: "ST depression induced by exercise relative to rest." },
  { name: "slope", kind: "categorical", label: "Slope of peak exercise ST segment", options: [{ value: "Upsloping", label: "Upsloping" }, { value: "Flat", label: "Flat" }, { value: "Downsloping", label: "Downsloping" }], helper: "Slope of the ST segment during peak exercise." },
  { name: "ca", kind: "categorical", label: "Major vessels coloured by fluoroscopy", options: [{ value: "0 vessels", label: "0 vessels" }, { value: "1 vessel", label: "1 vessel" }, { value: "2 vessels", label: "2 vessels" }, { value: "3 vessels", label: "3 vessels" }, { value: "4 vessels", label: "4 vessels" }], helper: "Number of major vessels visualised by fluoroscopy." },
  { name: "thal", kind: "categorical", label: "Thalassemia", options: [{ value: "Normal", label: "Normal" }, { value: "Fixed defect", label: "Fixed defect" }, { value: "Reversible defect", label: "Reversible defect" }, { value: "Unknown / not reported", label: "Unknown / not reported" }], helper: "Thalassemia blood-flow result." },
];

export function validateFeature(feature, value) {
  if (value === "" || value === null || value === undefined) {
    return `Please provide ${feature.label.toLowerCase()}.`;
  }
  if (feature.kind === "numeric") {
    const num = Number(value);
    if (Number.isNaN(num)) return `Please enter a valid ${feature.label.toLowerCase()}.`;
    if (num < feature.min) return `${feature.label} cannot be below ${feature.min}.`;
    if (num > feature.max) return `${feature.label} cannot exceed ${feature.max}.`;
    return null;
  }
  return null;
}

export function validateAll(values) {
  const errors = {};
  for (const feature of FEATURES) {
    const error = validateFeature(feature, values[feature.name]);
    if (error) errors[feature.name] = error;
  }
  return errors;
}

export function validatePassword(password, confirm) {
  if (!password) return "Password is required.";
  if (password.length < 8) return "Password must be at least 8 characters long.";
  if (!/[A-Z]/.test(password)) return "Password must contain an uppercase letter.";
  if (!/[a-z]/.test(password)) return "Password must contain a lowercase letter.";
  if (!/\d/.test(password)) return "Password must contain a digit.";
  if (confirm !== undefined && password !== confirm) return "Passwords do not match.";
  return null;
}

export function validateEmail(email) {
  if (!email) return "Email is required.";
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return "Please enter a valid email address.";
  return null;
}
