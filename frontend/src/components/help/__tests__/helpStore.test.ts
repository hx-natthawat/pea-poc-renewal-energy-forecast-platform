import { beforeEach, describe, expect, it } from "vitest";
import { useHelpStore } from "@/stores/helpStore";

describe("helpStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useHelpStore.setState({
      isOpen: false,
      activeSection: null,
      language: "th",
    });
  });

  it("has correct initial state", () => {
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.activeSection).toBe(null);
    expect(state.language).toBe("th");
  });

  it("opens help with a section", () => {
    useHelpStore.getState().openHelp("test-section");
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.activeSection).toBe("test-section");
  });

  it("closes help", () => {
    useHelpStore.getState().openHelp("test-section");
    useHelpStore.getState().closeHelp();
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(false);
  });

  it("toggles help - opens when closed", () => {
    useHelpStore.getState().toggleHelp("test-section");
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.activeSection).toBe("test-section");
  });

  it("toggles help - closes when same section clicked", () => {
    useHelpStore.getState().openHelp("test-section");
    useHelpStore.getState().toggleHelp("test-section");
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(false);
  });

  it("toggles help - switches section when different section clicked", () => {
    useHelpStore.getState().openHelp("section-a");
    useHelpStore.getState().toggleHelp("section-b");
    const state = useHelpStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.activeSection).toBe("section-b");
  });

  it("sets language", () => {
    useHelpStore.getState().setLanguage("en");
    expect(useHelpStore.getState().language).toBe("en");

    useHelpStore.getState().setLanguage("th");
    expect(useHelpStore.getState().language).toBe("th");
  });
});
