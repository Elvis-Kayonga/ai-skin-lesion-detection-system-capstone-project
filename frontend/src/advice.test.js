import { describe, expect, it } from "vitest";
import { referralAdvice } from "./advice.js";

const base = { predicted_class: "nv", review_recommended: false, review_reason: "" };

describe("referralAdvice", () => {
  it("sends a possible melanoma to a doctor urgently", () => {
    const a = referralAdvice({ ...base, review_recommended: true, review_reason: "Melanoma probability 12% >= 5%" });
    expect(a.level).toBe("urgent");
    expect(a.title).toMatch(/doctor/i);
  });

  it("refers cancer-type top classes even without the review flag", () => {
    for (const cls of ["bcc", "akiec", "mel"]) {
      expect(referralAdvice({ ...base, predicted_class: cls }).level).toBe("urgent");
    }
  });

  it("asks for a doctor check when the model is unsure", () => {
    const a = referralAdvice({ ...base, review_recommended: true, review_reason: "High uncertainty (entropy 0.9 >= 0.60)" });
    expect(a.level).toBe("check");
  });

  it("never says the skin is fine, only that no warning signs were found", () => {
    const a = referralAdvice(base);
    expect(a.level).toBe("watch");
    expect(a.body).toMatch(/not a diagnosis/);
    expect(a.body).toMatch(/See a doctor if/);
  });
});
