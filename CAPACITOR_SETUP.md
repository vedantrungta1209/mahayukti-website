# MahaYukti native wrapper (Capacitor) — setup & status

The `ios/` and `android/` projects are thin native shells. They load the **live site**
(`server.url` in `capacitor.config.json` → `https://mahayukti.com/app.html`), so the WebView origin
is genuinely `https://mahayukti.com` and the registered LinkedIn redirect URIs
(`/auth/linkedin/callback/`, `/auth/linkedin-signin/callback/`) keep working unchanged.
`www/index.html` is only a placeholder that Capacitor's tooling needs; it is not shipped as app content.

- App ID / bundle ID: `com.mahayukti.app` (no earlier ID existed anywhere in the repo or git history). App name: MahaYukti.
- Capacitor 8.x; plugins: `@capacitor/push-notifications`.
- Start URL is `/app.html` rather than the marketing homepage `/`. To change, edit `server.url` in `capacitor.config.json` (and `www/index.html`), then `npx cap sync`.
- `server.allowNavigation` lists `mahayukti.com`, `linkedin.com`/`www.linkedin.com`, `*.supabase.co` so those stay *inside* the WebView.
  Without this, LinkedIn would open in Safari/Chrome and the OAuth return would land outside the app session.

## Status — what is verified vs not

| Item | Status |
|---|---|
| Capacitor config + both platform projects generated, `npx cap sync` runs | Done |
| Android `assembleDebug` | **Verified** — built successfully on a real Mac (not the cloud sandbox) after installing JDK 21 (Capacitor 8's `@capacitor/android` library module hardcodes `sourceCompatibility 21`; JDK 17/earlier won't compile it). Real `app-debug.apk` produced (5.6MB) in `android/app/build/outputs/apk/debug/`. Note: `android/capacitor-cordova-android-plugins/` is gitignored by Capacitor's own convention — always run `npm install && npx cap sync` after a fresh clone before building, or Gradle fails looking for it. |
| iOS build | **NOT built** — needs full Xcode.app (the Command Line Tools alone aren't enough), which isn't installed on this Mac. Xcode project edited by hand for push (entitlements file, AppDelegate hooks, background mode) — needs to be opened and checked in Xcode once installed. |
| Push notifications | **Scaffolded only.** Native hooks are in; it cannot deliver anything until the credentials below exist AND the web app calls the plugin (see "Web-app work still needed"). |
| Signing, store listings, credentials | Not done — requires your accounts |

## Risks to know before submitting

1. **Capacitor's docs say `server.url` is "not intended for use in production".** It works, but it means the app
   needs network to open at all and there is no offline shell.
2. **App Store Review Guideline 4.2 (minimum functionality):** Apple can reject apps that are just a website in a wrapper.
   Native push notifications (once actually used by the web app) are the main thing that mitigates this; consider adding more
   native value before/if rejected. Google Play is generally more lenient but also has a "minimum functionality" policy.
3. Because the app is the live site, every web deploy instantly changes the shipped app (no store review for web changes).
4. `_headers` sets `X-Frame-Options: DENY` and a restrictive `Permissions-Policy` — fine for the WebView, but re-test anything camera/mic related.

## Open the projects

```bash
npm install
npx cap sync          # after any config/plugin change
npx cap open ios      # needs macOS + Xcode (15+; project targets iOS 15)
npx cap open android  # Android Studio (JDK 21, SDK 36)
```
CLI Android build: `cd android && ./gradlew assembleDebug` (needs `ANDROID_HOME` / `android/local.properties`, which is git-ignored, and `JAVA_HOME` pointed at a JDK 21).

**If you don't already have a JDK 21:** `brew install openjdk@21` tries to compile it from source on this Mac and fails, demanding full Xcode (Homebrew has no pre-built bottle for this exact setup). Skip that — download a ready-to-run one instead, no Xcode needed:
```bash
curl -sSL -o jdk21.tar.gz "https://api.adoptium.net/v3/binary/latest/21/ga/mac/x64/jdk/hotspot/normal/eclipse?project=jdk"
tar -xzf jdk21.tar.gz
export JAVA_HOME="$PWD/jdk-21*/Contents/Home"
```
(Installing Android Studio instead also works and bundles its own compatible JDK — either path is fine.)

## Push notifications — what you must do

### Android (FCM)
1. Firebase console → create/choose project → add Android app with package `com.mahayukti.app`.
2. Download `google-services.json` and put it at **`android/app/google-services.json`**
   (git-ignored on purpose; `android/app/build.gradle` applies the plugin only if the file exists).
3. `POST_NOTIFICATIONS` permission (Android 13+) is already in the manifest; the app must still call `PushNotifications.requestPermissions()`.
4. Backend sends via FCM HTTP v1 (service-account key from Firebase → Project settings → Service accounts).

### iOS (APNs)
1. Enroll in the Apple Developer Program (paid) if not already.
2. developer.apple.com → Identifiers → App ID `com.mahayukti.app` → enable **Push Notifications**.
3. Keys → create an **APNs Auth Key (.p8)**; note Key ID + Team ID. Store the .p8 securely (do not commit).
4. In Xcode → target App → Signing & Capabilities: pick your Team; confirm **Push Notifications** and **Background Modes → Remote notifications** are shown
   (entitlement `App/App.entitlements` and `UIBackgroundModes` were added by hand; add the capability in the UI if Xcode doesn't show it).
5. `App.entitlements` has `aps-environment = development`. Xcode switches it to production for App Store/TestFlight archives with automatic signing; verify in the archive.
6. To use FCM as the sender for iOS too, upload the .p8 in Firebase → Project settings → Cloud Messaging, and add Firebase's iOS SDK + `GoogleService-Info.plist`
   (not done here — Capacitor's plugin returns a raw APNs token on iOS, so either send via APNs directly or add Firebase Messaging).

### Web-app work still needed (not done in this branch)
`app.html` does not yet use the plugin. Because the app loads the remote site, `window.Capacitor` is injected by the native shell,
so `app.html` can call `Capacitor.Plugins.PushNotifications` (`requestPermissions`, `register`, listen for `registration`), then store the token
in Supabase (e.g. a `device_tokens` table) and a server job must send the pushes. None of that exists yet.

## Test locally
- Android emulator/device: `npx cap run android`
- iOS simulator: `npx cap run ios` (simulators can't receive real APNs pushes — use a physical device)
- Verify LinkedIn sign-in end to end inside the app (login → LinkedIn → returns into the app, not Safari/Chrome).
  Check also that LinkedIn doesn't block sign-in in embedded WebViews; if it does, a browser-based flow (`@capacitor/browser`) plus deep links would be needed, which does require a registered redirect change.

## Path to TestFlight / Play internal testing
**iOS:** Developer Program → App ID with Push → create the app in App Store Connect (bundle ID `com.mahayukti.app`) → open `ios/App/App.xcworkspace`/`App.xcodeproj`,
set Team, add app icon (1024px) → Product → Archive → Distribute → App Store Connect → TestFlight internal testers.
**Android:** Play Console (one-time $25) → create app → generate an upload keystore (keep it safe, never commit) → `./gradlew bundleRelease` signed with it →
upload the `.aab` to Internal testing → add testers. Add `google-services.json` first if you want push.
Default Capacitor placeholder icons/splash are in place — replace before public release.
