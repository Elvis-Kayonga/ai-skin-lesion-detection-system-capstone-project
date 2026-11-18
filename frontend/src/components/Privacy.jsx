/** Privacy Policy and Terms of Use, written in plain language. Keep in step with the backend: if what is
 * stored changes (backend/app/models.py), update this page too. */
export default function Privacy() {
  return (
    <section className="card privacy">
      <div className="card-head">
        <h2>Privacy Policy and Terms of Use</h2>
        <p className="muted small">Last updated: November 2026</p>
      </div>

      <h3>Privacy Policy</h3>
      <ul>
        <li><strong>What this app is.</strong> A university capstone prototype that gives AI-assisted pre-screening support for skin lesions. It is not a diagnosis and does not replace a clinician.</li>
        <li><strong>What we collect.</strong> The photo you upload, the result the model gives, and a random guest id with a scrambled (hashed) password that your browser creates automatically. We do not ask for or store your name, phone number, age, location or any patient details.</li>
        <li><strong>Do not upload photos of real patients.</strong> This prototype is for test images only.</li>
        <li><strong>How we protect it.</strong> Every request needs a private access token that expires after 8 hours. You can only see the cases made in your own browser. Passwords are stored only as bcrypt hashes.</li>
        <li><strong>Where it is stored.</strong> On the server that runs the app (a local computer during the capstone). Any real use in Rwanda would store data in Rwanda, as Law N° 058/2021, Article 50 requires.</li>
        <li><strong>Who can see it.</strong> Only you, through your browser, and the developer for testing. We do not sell or share data.</li>
        <li><strong>Your choices.</strong> Clearing your browser data removes your link to your past cases. A button to delete a case is planned but not built yet.</li>
      </ul>

      <h3>Terms of Use</h3>
      <ul>
        <li>The app is for research and education only. Two of the training datasets are non-commercial (CC BY-NC), so it may not be used commercially.</li>
        <li>Results can be wrong, especially on dark skin, on phone photos and for rare lesion types. Always follow the "Review recommended" flag and consult a qualified clinician.</li>
        <li>Only upload images you have the right to use.</li>
      </ul>
    </section>
  );
}
