# Architectural Decision Note: Client-Side Session Storage

## Chosen Strategy
We store session identifier keys inside **HTTP-Only, SameSite=Lax Cookies** rather than local browser storage objects (localStorage / sessionStorage).

## Security Justification
1. **Mitigation of Cross-Site Scripting (XSS):** By applying the `httponly=True` header parameter, browser-side JavaScript frameworks are completely blocked from reading or interacting with the cookie string. If a hacker successfully executes a malicious script injection attack on our frontend, they cannot extract or steal the active user session token.
2. **Mitigation of Cross-Site Request Forgery (CSRF):** Enforcing the `samesite="lax"` rule configuration ensures that the browser restricts cookie payload delivery during cross-domain third-party web requests, protecting infrastructure tracking pipelines.
3. **Session Persistence Boundaries:** Utilizing the explicit server-side `max_age=86400` config argument converts the session identifier from a volatile, volatile memory instance into a hardened storage entry committed directly to the user's filesystem, fulfilling our criteria requirements across application restarts.
