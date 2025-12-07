import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useHelpStore } from "@/stores/helpStore";
import { HelpSidebar } from "../HelpSidebar";

// Mock the help store
vi.mock("@/stores/helpStore", () => ({
  useHelpStore: vi.fn(),
}));

// Mock the help content
vi.mock("../content", () => ({
  getHelpSection: vi.fn((id: string) => {
    if (id === "test-section") {
      return {
        id: "test-section",
        title: "Test Section",
        titleTh: "ส่วนทดสอบ",
        icon: () => null,
        description: "Test description",
        descriptionTh: "คำอธิบายทดสอบ",
        features: [
          {
            title: "Feature 1",
            titleTh: "คุณสมบัติ 1",
            description: "Feature description",
            descriptionTh: "คำอธิบายคุณสมบัติ",
          },
        ],
        tips: [
          {
            text: "Test tip",
            textTh: "เคล็ดลับทดสอบ",
          },
        ],
        relatedSections: [],
        docsUrl: "/docs/test",
      };
    }
    return null;
  }),
}));

describe("HelpSidebar", () => {
  const mockCloseHelp = vi.fn();
  const mockOpenHelp = vi.fn();
  const mockSetLanguage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sidebar when open", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    expect(screen.getByRole("complementary")).toBeInTheDocument();
    expect(screen.getByText("Test Section")).toBeInTheDocument();
  });

  it("displays section content in English", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    expect(screen.getByText("Test description")).toBeInTheDocument();
    expect(screen.getByText("Feature 1")).toBeInTheDocument();
  });

  it("displays section content in Thai", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "th",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    expect(screen.getByText("ส่วนทดสอบ")).toBeInTheDocument();
    expect(screen.getByText("คำอธิบายทดสอบ")).toBeInTheDocument();
  });

  it("calls closeHelp when close button is clicked", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    const closeButton = screen.getByLabelText("Close help sidebar");
    fireEvent.click(closeButton);
    expect(mockCloseHelp).toHaveBeenCalled();
  });

  it("toggles language when language button is clicked", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "th",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    const langButton = screen.getByLabelText("Switch to English");
    fireEvent.click(langButton);
    expect(mockSetLanguage).toHaveBeenCalledWith("en");
  });

  it("shows placeholder when no section is active", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: null,
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    expect(screen.getByText("Select a help topic")).toBeInTheDocument();
  });

  it("has correct accessibility attributes", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: true,
      activeSection: "test-section",
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    const sidebar = screen.getByRole("complementary");
    expect(sidebar).toHaveAttribute("aria-label", "Help sidebar");
    expect(sidebar).toHaveAttribute("aria-hidden", "false");
  });

  it("is hidden when closed", () => {
    (useHelpStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isOpen: false,
      activeSection: null,
      language: "en",
      closeHelp: mockCloseHelp,
      openHelp: mockOpenHelp,
      setLanguage: mockSetLanguage,
    });

    render(<HelpSidebar />);
    // When aria-hidden="true", the element is not queryable by role
    // So we use queryByRole with hidden: true option
    const sidebar = screen.getByRole("complementary", { hidden: true });
    expect(sidebar).toHaveAttribute("aria-hidden", "true");
  });
});
