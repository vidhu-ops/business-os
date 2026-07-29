-- IIDATECH proprietary data + evidence storage (PostgreSQL)

CREATE TABLE IF NOT EXISTS competitor_pricing (
    id SERIAL PRIMARY KEY,
    industry TEXT NOT NULL,
    company TEXT,
    product TEXT,
    plan TEXT,
    price DOUBLE PRECISION,
    currency TEXT,
    billing_interval TEXT,
    region TEXT DEFAULT 'Global',
    source_url TEXT,
    last_verified TEXT,
    trust_score DOUBLE PRECISION DEFAULT 0
);

CREATE TABLE IF NOT EXISTS buyer_voice (
    id SERIAL PRIMARY KEY,
    industry TEXT NOT NULL,
    source TEXT,
    source_type TEXT,
    pain_category TEXT,
    complaint TEXT,
    desired_outcome TEXT,
    willingness_to_pay_signal TEXT,
    sentiment_score DOUBLE PRECISION,
    frequency INTEGER DEFAULT 0,
    region TEXT DEFAULT 'Global'
);

CREATE TABLE IF NOT EXISTS supplier_costs (
    id SERIAL PRIMARY KEY,
    industry TEXT NOT NULL,
    product TEXT,
    supplier_name TEXT,
    moq INTEGER,
    unit_cost DOUBLE PRECISION,
    packaging_cost DOUBLE PRECISION,
    shipping_cost DOUBLE PRECISION,
    region TEXT DEFAULT 'Global',
    source_url TEXT,
    trust_score DOUBLE PRECISION DEFAULT 0
);

CREATE TABLE IF NOT EXISTS industry_benchmarks (
    id SERIAL PRIMARY KEY,
    industry TEXT NOT NULL,
    metric TEXT,
    value DOUBLE PRECISION,
    unit TEXT,
    geography TEXT DEFAULT 'Global',
    source_type TEXT,
    trust_score DOUBLE PRECISION DEFAULT 0,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id SERIAL PRIMARY KEY,
    record_id TEXT UNIQUE,
    topic TEXT,
    industry TEXT,
    geography TEXT,
    region TEXT,
    company TEXT,
    title TEXT,
    url TEXT,
    claim_type TEXT,
    trust_score DOUBLE PRECISION DEFAULT 0,
    evidence_tier TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_id TEXT UNIQUE,
    topic TEXT NOT NULL,
    industry TEXT,
    geography TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_scores (
    id SERIAL PRIMARY KEY,
    report_id TEXT NOT NULL,
    section TEXT,
    score DOUBLE PRECISION,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_competitor_pricing_industry ON competitor_pricing(industry);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_company ON competitor_pricing(company);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_region ON competitor_pricing(region);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_trust_score ON competitor_pricing(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_last_verified ON competitor_pricing(last_verified);

CREATE INDEX IF NOT EXISTS idx_buyer_voice_industry ON buyer_voice(industry);
CREATE INDEX IF NOT EXISTS idx_buyer_voice_region ON buyer_voice(region);
CREATE INDEX IF NOT EXISTS idx_buyer_voice_frequency ON buyer_voice(frequency DESC);

CREATE INDEX IF NOT EXISTS idx_supplier_costs_industry ON supplier_costs(industry);
CREATE INDEX IF NOT EXISTS idx_supplier_costs_region ON supplier_costs(region);
CREATE INDEX IF NOT EXISTS idx_supplier_costs_trust_score ON supplier_costs(trust_score DESC);

CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_industry ON industry_benchmarks(industry);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_geography ON industry_benchmarks(geography);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_trust_score ON industry_benchmarks(trust_score DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_records_topic ON evidence_records(topic);
CREATE INDEX IF NOT EXISTS idx_evidence_records_industry ON evidence_records(industry);
CREATE INDEX IF NOT EXISTS idx_evidence_records_company ON evidence_records(company);
CREATE INDEX IF NOT EXISTS idx_evidence_records_trust_score ON evidence_records(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_records_last_verified ON evidence_records(last_verified);
CREATE INDEX IF NOT EXISTS idx_evidence_records_geography ON evidence_records(geography);
CREATE INDEX IF NOT EXISTS idx_evidence_records_region ON evidence_records(region);

CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic);
CREATE INDEX IF NOT EXISTS idx_reports_industry ON reports(industry);
CREATE INDEX IF NOT EXISTS idx_reports_geography ON reports(geography);

CREATE INDEX IF NOT EXISTS idx_report_scores_report_id ON report_scores(report_id);

-- Provider search cache + cost tracking
CREATE TABLE IF NOT EXISTS search_cache (
    id SERIAL PRIMARY KEY,
    query_hash TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    provider TEXT NOT NULL,
    result_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    hit_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS provider_stats (
    id SERIAL PRIMARY KEY,
    provider TEXT UNIQUE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    avg_latency_ms DOUBLE PRECISION DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_cost_log (
    id SERIAL PRIMARY KEY,
    report_id TEXT,
    provider TEXT,
    model TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_provider ON search_cache(provider);
CREATE INDEX IF NOT EXISTS idx_search_cache_created_at ON search_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_provider_stats_provider ON provider_stats(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_report_id ON api_cost_log(report_id);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_provider ON api_cost_log(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_created_at ON api_cost_log(created_at);
-- Semantic retrieval memory columns (applied via ensure_semantic_schema migration)
-- ALTER TABLE competitor_pricing ADD COLUMN embedding_vector TEXT;
-- ALTER TABLE competitor_pricing ADD COLUMN embedding_model TEXT;
-- ALTER TABLE competitor_pricing ADD COLUMN embedding_updated_at TEXT;
-- Same columns on: buyer_voice, supplier_costs, industry_benchmarks, evidence_records, reports
