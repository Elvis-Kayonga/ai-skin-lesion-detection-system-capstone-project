// Turns a screening result into one plain-language next step for the health worker.
// It never says a lesion is fine: the best case is "no warning signs found", with what to watch for.

// Classes that are skin cancer or can become one. Seeing one of these as the most likely class always
// means "see a doctor", even when the model is confident and the server's review flag did not fire.
export const NEEDS_DOCTOR = {
  mel: "melanoma, a serious type of skin cancer",
  bcc: "basal cell carcinoma, a common skin cancer",
  akiec: "actinic keratosis, a rough patch that can turn into skin cancer",
};

export function referralAdvice(result) {
  const reason = result.review_reason || "";
  const possibleMelanoma = result.review_recommended && /melanoma/i.test(reason);
  const unsure = result.review_recommended && /uncertainty/i.test(reason);
  const riskyTop = NEEDS_DOCTOR[result.predicted_class];

  if (possibleMelanoma || result.predicted_class === "mel") {
    return {
      level: "urgent",
      title: "See a doctor soon",
      body:
        "The system found signs of a possible melanoma, a serious type of skin cancer. " +
        "Refer this person to a doctor or skin specialist as soon as possible. " +
        "Show them this result.",
    };
  }
  if (riskyTop) {
    return {
      level: "urgent",
      title: "See a doctor",
      body:
        `The most likely type is ${riskyTop}. A doctor should look at this spot. ` +
        "Refer this person to a doctor or skin specialist and show them this result.",
    };
  }
  if (unsure) {
    return {
      level: "check",
      title: "Not sure: a doctor should check",
      body:
        "The system is not sure what this is, so it cannot give a reliable answer. " +
        "Try a new photo in bright light, close up and in focus. If it is still unsure, refer this person to a doctor.",
    };
  }
  return {
    level: "watch",
    title: "No warning signs found",
    body:
      "The system did not find warning signs in this photo. This is not a diagnosis and does not prove the skin is healthy. " +
      "See a doctor if the spot grows, changes shape or colour, bleeds, itches or hurts, or if the person is worried.",
  };
}
