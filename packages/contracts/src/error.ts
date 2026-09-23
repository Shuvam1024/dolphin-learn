/** Mirrors the FastAPI error envelope. OpenAPI remains the source of truth. */
export type ApiErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string;
  };
};
