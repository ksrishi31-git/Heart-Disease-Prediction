import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "../pages/Login.jsx";

vi.mock("../services/api.js", () => ({
  default: { interceptors: { response: { use: vi.fn() } } },
  errorMessage: (error, fallback) => error?.message || fallback || "fallback",
}));

const loginMock = vi.fn().mockResolvedValue({});
vi.mock("../hooks/useAuth.jsx", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: loginMock,
    register: vi.fn(),
    logout: vi.fn(),
    checkSession: vi.fn(),
  }),
}));

describe("Login page", () => {
  it("renders the form", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("shows validation errors for empty/invalid fields", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "not-an-email" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("submits valid credentials", async () => {
    loginMock.mockClear();
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "demo@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "StrongPass1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));
    await waitFor(() => expect(loginMock).toHaveBeenCalledTimes(1));
    expect(loginMock).toHaveBeenCalledWith("demo@example.com", "StrongPass1");
  });
});
