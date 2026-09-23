# packages/contracts

Shared API/DTOs and generated OpenAPI clients. OpenAPI from the FastAPI app is the contract source of truth; keep hand-written stubs minimal.

`src/error.ts` types the error envelope `{ error: { code, message, details, request_id } }`.
