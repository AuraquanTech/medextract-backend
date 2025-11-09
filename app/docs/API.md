GET /health
GET /ready
POST /api/analyze            {context, meta} -> AnalyzeResponse
POST /api/experts/find       {context, case_summary, specialties, urgency}
POST /api/similar/search     {context, case_summary, top_k}
POST /api/whatif/simulate    {context, original_timeline, hypothetical_changes}
GET  /api/audit/verify
POST /webhooks/stripe        (signed)
