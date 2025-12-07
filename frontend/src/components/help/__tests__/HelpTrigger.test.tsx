import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useHelpStore } from "@/stores/helpStore";
import { HelpTrigger } from "../HelpTrigger";

// Mock the help store
vi.mock("@/stores/helpStore", () => ({
  useHelpStore: vi.fn(),
}));

describe("HelpTrigger", () => {
  const mockToggleHelp = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: false,
      activeSection: null,
      toggleHelp: mockToggleHelp,
    });
  });

  it("renders the help icon button", () => {
    render(<HelpTrigger sectionId="test-section" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "Show help for test-section");
  });

  it("calls toggleHelp when clicked", () => {
    render(<HelpTrigger sectionId="test-section" />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(mockToggleHelp).toHaveBeenCalledWith("test-section");
  });

  it("shows active state when sidebar is open for this section", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      toggleHelp: mockToggleHelp,
    });

    render(<HelpTrigger sectionId="test-section" />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("shows inactive state when different section is active", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "other-section",
      toggleHelp: mockToggleHelp,
    });

    render(<HelpTrigger sectionId="test-section" />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("applies custom className", () => {
    render(<HelpTrigger sectionId="test-section" className="custom-class" />);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("custom-class");
  });

  it("uses custom label for accessibility", () => {
    render(<HelpTrigger sectionId="test-section" label="Custom help label" />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "Custom help label");
  });

  it("renders with different sizes", () => {
    const { rerender } = render(<HelpTrigger sectionId="test-section" size="sm" />);
    expect(screen.getByRole("button")).toBeInTheDocument();

    rerender(<HelpTrigger sectionId="test-section" size="lg" />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("renders with card variant for always-visible help icons", () => {
    render(<HelpTrigger sectionId="test-section" variant="card" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
    // Card variant should have brand-colored background for visibility
    expect(button).toHaveClass("bg-pea-purple/5");
  });

  it("renders with subtle variant", () => {
    render(<HelpTrigger sectionId="test-section" variant="subtle" />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("stops event propagation on click", () => {
    // Verify that stopPropagation is called when clicking the help trigger
    // This prevents clicks from bubbling up to parent containers
    render(<HelpTrigger sectionId="test-section" />);
    const button = screen.getByRole("button");

    // Create a mock event to verify stopPropagation behavior
    const clickEvent = new MouseEvent("click", { bubbles: true });
    const stopPropagationSpy = vi.spyOn(clickEvent, "stopPropagation");

    fireEvent(button, clickEvent);
    expect(mockToggleHelp).toHaveBeenCalledWith("test-section");
    expect(stopPropagationSpy).toHaveBeenCalled();
  });
});
