"""Google OAuth flow for connecting a parent's Gmail + Google Calendar.

The web-based consent runs in an in-app browser (iOS ASWebAuthenticationSession):
the app fetches an authorization URL from `/oauth/google/authorize-url`, opens it,
the user grants scopes, Google redirects to `/oauth/google/callback`, the backend
exchanges the code for an (encrypted) refresh token stored in
`integration_accounts`, then redirects to the app's custom URL scheme.

The live token exchange needs a registered Google OAuth client
(GOOGLE_OAUTH_CLIENT_ID/SECRET) and is gated behind verification for the
restricted gmail.readonly scope; until then only test users can complete it.
"""
