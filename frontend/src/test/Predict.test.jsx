import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Predict from "../pages/Predict.jsx";

vi.mock("../services/api.js", () => ({
  default: { interceptors: { response: { use: vi.fn() } } },
  errorMessage: (error, fallback) => error?.response?.data?.detail || fallback || "fallback",
}));

const mockCreate = vi.fn();
vi.mock("../services/predictions.js", () => ({
  predictionsApi: { create: (...args) => mockCreate(...args) },
  modelsApi: {},
}));

const RESULT = {
  prediction_id: "abc-123",
  created_at: "2026-08-15T00:00:00Z",
  model_version: "heart-disease-model-v2",
  prediction: 1,
  classification: "Heart Disease Detected",
  label: "Positive",
  probability: 0.693,
  risk_score_percent: 69.3,
  model: {
    model_key: "logistic_regression",
    model_name: "Logistic Regression",
    metrics: {
      accuracy: 0.8632,
      precision: 0.8627,
      sensitivity: 0.8932,
      specificity: 0.8273,
      f1: 0.8771,
      roc_auc: 0.9111,
    },
  },
};

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/Age/i), { target: { value: "58" } });
  fireEvent.click(screen.getByLabelText("Sex: Male"));
  fireEvent.change(screen.getByLabelText(/Chest pain type/i), {
    target: { value: "Typical angina" },
  });
  fireEvent.change(screen.getByLabelText(/Resting blood pressure/i), {
    target: { value: "145" },
  });
  fireEvent.change(screen.getByLabelText(/Serum cholesterol/i), {
    target: { value: "233" },
  });
  fireEvent.click(screen.getByLabelText("Fasting blood sugar > 120 mg/dl: Yes"));
  fireEvent.change(screen.getByLabelText(/Resting ECG result/i), {
    target: { value: "Normal" },
  });
  fireEvent.change(screen.getByLabelText(/Maximum heart rate/i), {
    target: { value: "150" },
  });
  fireEvent.click(screen.getByLabelText("Exercise-induced angina: No"));
  fireEvent.change(screen.getByLabelText(/ST depression/i), {
    target: { value: "2.3" },
  });
  fireEvent.change(screen.getByLabelText(/Slope of peak exercise/i), {
    target: { value: "Upsloping" },
  });
  fireEvent.change(screen.getByLabelText(/Major vessels/i), {
    target: { value: "0 vessels" },
  });
  fireEvent.change(screen.getByLabelText(/Thalassemia/i), {
    target: { value: "Normal" },
  });
}

describe("Predict page", () => {
  beforeEach(() => {
    mockCreate.mockClear();
  });

  it("renders all four form sections", () => {
    render(
      <MemoryRouter>
        <Predict />
      </MemoryRouter>,
    );
    expect(screen.getByText("Basic Information")).toBeInTheDocument();
    expect(screen.getByText("Symptoms")).toBeInTheDocument();
    expect(screen.getByText("Vital Measurements")).toBeInTheDocument();
    expect(screen.getByText("Medical Test Information")).toBeInTheDocument();
  });

  it("blocks submission when required fields are missing", () => {
    render(
      <MemoryRouter>
        <Predict />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /run prediction/i }));
    expect(screen.getByText(/please fix the highlighted fields/i)).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("rejects impossible values (age > 120)", () => {
    render(
      <MemoryRouter>
        <Predict />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/Age/i), { target: { value: "999" } });
    fireEvent.click(screen.getByRole("button", { name: /run prediction/i }));
    expect(screen.getByText(/cannot exceed 120/i)).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("submits and renders a single unified prediction result", async () => {
    mockCreate.mockResolvedValueOnce({ data: RESULT });
    render(
      <MemoryRouter>
        <Predict />
      </MemoryRouter>,
    );
    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: /run prediction/i }));

    await waitFor(() => expect(mockCreate).toHaveBeenCalledTimes(1));
    expect(mockCreate).toHaveBeenCalledWith({
      age: "58", sex: "Male", cp: "Typical angina", trestbps: "145", chol: "233",
      fbs: "Yes", restecg: "Normal", thalach: "150", exang: "No",
      oldpeak: "2.3", slope: "Upsloping", ca: "0 vessels", thal: "Normal",
    });

    expect(screen.getByText("Heart Disease Detected")).toBeInTheDocument();

    expect(screen.queryByText(/3 of 3 models agree/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Decision Tree")).not.toBeInTheDocument();
    expect(screen.queryByText("Random Forest")).not.toBeInTheDocument();

    expect(screen.getByText("Prediction Model")).toBeInTheDocument();
    expect(screen.getByText("Logistic Regression")).toBeInTheDocument();
    expect(screen.getByText(/Why Logistic Regression\?/)).toBeInTheDocument();
    expect(screen.queryByText(/Why this model was selected/i)).not.toBeInTheDocument();

    expect(screen.getByText("Model-estimated probability")).toBeInTheDocument();
    expect(screen.getByText("69.3%")).toBeInTheDocument();

    expect(screen.getByText("Model Performance")).toBeInTheDocument();
    expect(screen.getByText("86.32%")).toBeInTheDocument();
    expect(screen.getByText("89.32%")).toBeInTheDocument();
    expect(screen.getByText("82.73%")).toBeInTheDocument();
    expect(screen.getByText("91.11%")).toBeInTheDocument();
    expect(screen.getByText("87.71%")).toBeInTheDocument();

    expect(screen.getByText(/not a medical diagnosis/i)).toBeInTheDocument();
  });

  it("does not offer the user a model choice", async () => {
    mockCreate.mockResolvedValueOnce({ data: RESULT });
    render(
      <MemoryRouter>
        <Predict />
      </MemoryRouter>,
    );
    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: /run prediction/i }));
    await waitFor(() => expect(mockCreate).toHaveBeenCalledTimes(1));

    expect(screen.queryByLabelText(/select.*model/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/3 of 3 models agree/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Decision Tree")).not.toBeInTheDocument();
    expect(screen.queryByText("Random Forest")).not.toBeInTheDocument();
  });
});
