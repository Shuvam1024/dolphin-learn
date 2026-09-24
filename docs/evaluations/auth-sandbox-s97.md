# Auth sandbox note (S97)

Manual sandbox: with `ENVIRONMENT=development` and `NEXT_PUBLIC_ENVIRONMENT=development`, the email form mints an HS256 dev token. With `ENVIRONMENT=production` and `AUTH_JWKS_URL` pointing at a managed IdP JWKS, only RS256 tokens are accepted; `POST /api/v1/dev/token` returns 404. Logout calls `POST /api/v1/auth/revoke` then clears the HttpOnly cookie. There is no password field on any route.
