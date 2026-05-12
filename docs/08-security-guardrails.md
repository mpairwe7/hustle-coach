# 8. Security & Guardrails — HustleCoach

## Business-Specific Protections

- **Hype detection**: Blocks "guaranteed returns", "get rich quick"
- **Predatory finance**: Flags dangerous loan recommendations
- **PII protection**: Redacts phone numbers, NIN in conversations
- **Grounding**: All financial advice grounded in knowledge base

## OWASP LLM Top 10

| Risk | Mitigation |
|------|-----------|
| LLM01 Injection | InputGuard + spotlight markers |
| LLM02 Output | Structured JSON, no raw HTML |
| LLM05 Handling | Business plan extraction validates schema |
| LLM06 Agency | Tools are read-only (market lookup, no transactions) |
| LLM08 DoS | Rate limiting, max 2000 char input |
| LLM09 Hallucination | Grounding check, citation requirement, abstention |

## Auth Security

- JWT with bcrypt password hashing
- Password reset flow (email/token)
- Rate limiting per user
- Session TTL: 24 hours
