// End-to-end tests of the main user journeys, run in every browser project.
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const SAMPLES = path.resolve("../sample_images");
const LESION = path.join(SAMPLES, "ISIC_0030440.jpg");
const BLURRY = path.join(SAMPLES, "blurry_example_will_be_rejected.jpg");
const NOT_IMAGE = path.join(SAMPLES, "not_an_image_will_be_rejected.txt");
const DISCLAIMER = "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.";
const FILE_INPUT = 'input[accept="image/jpeg,image/png"]';

test.beforeAll(() => {
  for (const f of [LESION, BLURRY, NOT_IMAGE]) expect(fs.existsSync(f), f).toBeTruthy();
});

async function openApp(page) {
  await page.goto("/");
  await expect(page.getByText("1. Add a photo of the lesion")).toBeVisible();
}

async function analyse(page, file) {
  await page.setInputFiles(FILE_INPUT, file);
  await page.getByRole("button", { name: "2. Analyse image" }).click();
}

test("opens straight into the app, with the disclaimer and limitations visible", async ({ page }) => {
  await openApp(page);
  await expect(page.locator("input[type=password]")).toHaveCount(0);            // no login screen
  await expect(page.getByRole("note")).toContainText(DISCLAIMER);                // top bar
  await expect(page.locator("footer")).toContainText(DISCLAIMER);                // footer
  await expect(page.getByText("Know the limits")).toBeVisible();
});

test("analyses a lesion photo and shows the full result", async ({ page }) => {
  await openApp(page);
  await analyse(page, LESION);
  const result = page.locator("section.result");
  await expect(result).toBeVisible();
  await expect(result.locator(".top-class")).not.toBeEmpty();
  await expect(result.locator(".bar-row")).toHaveCount(7);                        // all 7 classes
  await expect(result.locator(".pill")).toHaveText(/(Low|Medium|High) uncertainty/);
  await expect(result.getByAltText("Grad-CAM heatmap overlay")).toBeVisible();
  await expect(result.locator(".disclaimer")).toHaveText(DISCLAIMER);
  // If the model flags the case, the banner must give a reason
  if (await result.locator(".notice.warn").count()) {
    await expect(result.locator(".notice.warn")).toContainText(/High uncertainty|Melanoma probability/);
  }
});

test("rejects a blurry photo with a clear message and shows no result", async ({ page }) => {
  await openApp(page);
  await analyse(page, BLURRY);
  await expect(page.locator(".error-box")).toContainText("too blurry");
  await expect(page.locator("section.result")).toHaveCount(0);
});

test("rejects a file that is not an image", async ({ page }) => {
  await openApp(page);
  await analyse(page, NOT_IMAGE);
  await expect(page.locator(".error-box")).toContainText("JPEG or PNG");
});

test("keeps the case history after a page reload, and can reopen a case", async ({ page }) => {
  await openApp(page);
  await analyse(page, LESION);
  const topClass = await page.locator("section.result .top-class").textContent();
  await page.reload();
  await openApp(page);
  await page.getByRole("button", { name: /History/ }).click();
  await expect(page.locator("tbody tr").first()).toContainText(topClass.trim());
  await page.getByRole("button", { name: "View" }).first().click();
  await expect(page.locator("section.result .top-class")).toHaveText(topClass.trim());
});

test("shows the full limitations panel", async ({ page }) => {
  await openApp(page);
  await page.getByRole("button", { name: "Limitations", exact: true }).click();
  await expect(page.getByText("About and limitations")).toBeVisible();
  await expect(page.getByText(/Fitzpatrick V to VI/)).toBeVisible();
});

test("takes a photo with the camera and analyses it", async ({ page, browserName }) => {
  test.skip(browserName === "webkit", "WebKit has no fake camera for automated tests");
  await openApp(page);
  await page.getByRole("button", { name: "Take a photo" }).click();
  await expect(page.getByRole("button", { name: "Capture photo" })).toBeEnabled();
  await page.getByRole("button", { name: "Capture photo" }).click();
  await expect(page.locator("img.preview")).toBeVisible();
  await page.getByRole("button", { name: "2. Analyse image" }).click();
  // The fake camera shows a synthetic test pattern: the app must either analyse it or reject it
  // with a clear quality message. Both are correct behaviour; a crash or silence is not.
  await expect(page.locator("section.result, .error-box")).toBeVisible();
});

test("fits the screen without sideways scrolling", async ({ page }) => {
  await openApp(page);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
