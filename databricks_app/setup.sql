-- One-time setup: run in a Databricks SQL editor or notebook before deploying the app.
CREATE SCHEMA IF NOT EXISTS main.clienthub;

CREATE TABLE IF NOT EXISTS main.clienthub.hospital_opportunities (
    opportunity_id STRING,
    hospital_name STRING,
    market_category STRING,
    location STRING,
    ehr_platform STRING,
    bed_count INT,
    account_lead STRING,
    stage STRING,
    overview STRING,
    strategic_priorities STRING,
    clickup_url STRING
);

-- Pin state used by the app (created here so the app's service principal only needs SELECT/MODIFY)
CREATE TABLE IF NOT EXISTS main.clienthub.pinned_opportunities (
    opportunity_id STRING,
    pinned_by STRING,
    pinned_at TIMESTAMP
);

-- Example Data Population across 5 Market Categories
-- MERGE keeps this idempotent so re-running the script does not create duplicate opportunities
MERGE INTO main.clienthub.hospital_opportunities AS t
USING (
    SELECT * FROM VALUES
    ('OPP-001', 'Duke University Health System', 'Academic Medical Centers', 'Durham, NC', 'Epic', 1500, 'Natalie Zachariah', 'Discovery', 'Top-tier academic medical system looking to modernize AI workflow automation across clinical trial data.', 'Expand predictive care pipelines; integrate LLM notes parsing.', 'https://app.clickup.com/90141168460/v/dc/2kyda4uc-29274'),
    ('OPP-002', 'UNC Health Network', 'Integrated Delivery Networks (IDNs)', 'Chapel Hill, NC', 'Epic', 950, 'Sarah Jenkins', 'Proposal Sent', 'Multi-hospital IDN seeking seamless EHR analytics pipelines and customer reporting dashboards.', 'Reduce bed turnaround time; streamline patient transition reporting.', 'https://app.clickup.com/90141168460/v/dc/2kyda4uc-29274'),
    ('OPP-003', 'WakeMed Health & Hospitals', 'Regional Health Systems', 'Raleigh, NC', 'Epic', 941, 'Alex Rivera', 'In Review', 'Regional community-focused system upgrading clinical intelligence infrastructure.', 'Automate ICU capacity alerts and staffing forecasts.', 'https://app.clickup.com/90141168460/v/dc/2kyda4uc-29274'),
    ('OPP-004', 'Triangle Orthopedic Surgical Center', 'Specialty & Surgical Groups', 'Durham, NC', 'AthenaHealth', 120, 'Marcus Vance', 'Qualified', 'High-volume outpatient surgical facility looking to automate pre-op scheduling workflows.', 'Automate prior authorizations and post-op follow-up analytics.', 'https://app.clickup.com/90141168460/v/dc/2kyda4uc-29274'),
    ('OPP-005', 'Johnston Health Community Network', 'Community Hospital Networks', 'Smithfield, NC', 'MEDITECH', 199, 'Elena Rostova', 'Discovery', 'Rural community health network focused on upgrading rural access telemetry and analytics.', 'Improve telehealth data streaming into central Delta tables.', 'https://app.clickup.com/90141168460/v/dc/2kyda4uc-29274')
    AS s(opportunity_id, hospital_name, market_category, location, ehr_platform, bed_count, account_lead, stage, overview, strategic_priorities, clickup_url)
) AS s
ON t.opportunity_id = s.opportunity_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
