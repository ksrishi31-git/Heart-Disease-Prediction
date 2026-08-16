import { describe, expect, it } from "vitest";
import {
  FEATURES,
  validateAll,
  validateEmail,
  validateFeature,
  validatePassword,
} from "../utils/validation.js";

describe("validateFeature", () => {
  const age = FEATURES.find((f) => f.name === "age");

  it("requires a value", () => {
    expect(validateFeature(age, "")).toMatch(/provide/i);
  });

  it("rejects out-of-range values", () => {
    expect(validateFeature(age, 200)).toMatch(/cannot exceed/);
    expect(validateFeature(age, 0)).toMatch(/cannot be below/);
  });

  it("accepts plausible values", () => {
    expect(validateFeature(age, 58)).toBeNull();
    expect(validateFeature(age, 29)).toBeNull();
  });

  it("rejects non-numeric input", () => {
    expect(validateFeature(age, "abc")).toMatch(/valid/);
  });
});

describe("validateAll", () => {
  it("returns no errors for a complete valid form", () => {
    const values = {
      age: 58, sex: "Male", cp: "Typical angina", trestbps: 145, chol: 233, fbs: "Yes",
      restecg: "Normal", thalach: 150, exang: "No", oldpeak: 2.3, slope: "Upsloping",
      ca: "0 vessels", thal: "Normal",
    };
    expect(validateAll(values)).toEqual({});
  });

  it("flags every missing field", () => {
    const errors = validateAll({});
    expect(Object.keys(errors).length).toBe(13);
  });
});

describe("validatePassword", () => {
  it("enforces strength rules", () => {
    expect(validatePassword("short", undefined)).toMatch(/8 characters/);
    expect(validatePassword("alllowercase1", undefined)).toMatch(/uppercase/);
    expect(validatePassword("ALLUPPERCASE1", undefined)).toMatch(/lowercase/);
    expect(validatePassword("NoDigitsHere", undefined)).toMatch(/digit/);
  });

  it("accepts a strong password", () => {
    expect(validatePassword("StrongPass1", "StrongPass1")).toBeNull();
  });

  it("detects mismatched confirmation", () => {
    expect(validatePassword("StrongPass1", "StrongPass2")).toMatch(/do not match/);
  });
});

describe("validateEmail", () => {
  it("accepts valid emails", () => {
    expect(validateEmail("student@college.edu")).toBeNull();
  });

  it("rejects invalid emails", () => {
    expect(validateEmail("not-an-email")).toMatch(/valid email/);
    expect(validateEmail("")).toMatch(/required/);
  });
});
