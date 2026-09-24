# Architectural Decision Note: Client-Side Session Storage

## Chosen Strategy
We store session identifier keys inside **HTTP-Only, SameSite=Lax Cookies** rather than local browser storage objects (localStorage / sessionStorage).

## Security Justifications
1. **XSS Mitigation:** Applying the `httponly=True` flag ensures browser-side JavaScript frameworks cannot read or extract the session token string, blocking client-side script injection extraction vectors.
2. **CSRF Mitigation:** Enforcing `samesite="lax"` restricts cookie payload delivery during cross-domain third-party web requests, protecting session tracking loops.

## Risk & Trade-Off Analysis (Stated Sprint Deliverables)
We have made two explicit trade-offs during this implementation that balance infrastructure reality against user convenience:

1. **The Storage Trade-Off (Convenience vs. Hardening):** Utilizing `max_age=86400` forces the browser to commit the session token to the user's local filesystem so it survives browser restarts. **This is not hardened or encrypted storage.** The browser stores persistent cookies in plaintext on disk. This token is a bearer credential—anyone with local file access can steal it. We accept this risk to fulfill the requirement of close-and-reopen survival.
2. **The Transport Trade-Off (Development vs. Production):** We have explicitly set `secure=False` to allow testing across plain HTTP local loopback addresses (supporting browsers like Safari that strictly reject Secure cookies on HTTP). The trade-off is that this token is transmitted unencrypted. In a staging or production deployment, **this flag must be flipped to `secure=True`** and served strictly over HTTPS to prevent network packet sniffing attacks.
