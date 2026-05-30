# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main (latest) | ✅ |
| < 1.0 | ❌ |

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Instead, please report vulnerabilities privately:

1. **Email**: security@heretek.ai (preferred)
2. **GitHub Security Advisory**: Use the "Report a vulnerability" button on the Security tab

We aim to:
- Acknowledge receipt within 48 hours
- Provide an initial assessment within 5 business days
- Release a fix within 30 days (critical: 7 days)

## Security Best Practices

### For Contributors
- Never commit secrets, API keys, or credentials
- Use `secrets/encrypted.env` with SOPS for sensitive configuration
- All NATS communication must use mTLS
- Validate all inputs in agent message handlers
- Follow the Zero-Trust architecture pattern

### For Deployers
- Rotate API keys regularly
- Keep dependencies updated (monitor Dependabot alerts)
- Run security scans before deployment: `snyk code test && snyk sca test`
- Enable audit logging in production
- Use HTTPS for all external communication

## Vulnerability Disclosure Timeline

| Severity | Acknowledgment | Fix Target |
|----------|---------------|------------|
| Critical | 48 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 5 days | 30 days |
| Low | 10 days | 90 days |
