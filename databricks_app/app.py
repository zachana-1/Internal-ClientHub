import os

import streamlit as st
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

st.set_page_config(page_title="ClientHub - Market Opportunities", layout="wide")

# Databricks Apps inject host + service principal credentials; the warehouse comes from app.yaml
cfg = Config()
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

# Tables are created by setup.sql (run once before deploying)
OPPS_TABLE = "main.clienthub.hospital_opportunities"
PINS_TABLE = "main.clienthub.pinned_opportunities"

def _connect():
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    )

def run_query(query, params=None):
    with _connect() as conn, conn.cursor() as cursor:
        cursor.execute(query, params or {})
        return cursor.fetchall_arrow().to_pandas()

def run_statement(statement, params=None):
    with _connect() as conn, conn.cursor() as cursor:
        cursor.execute(statement, params or {})

def get_current_user():
    # Databricks Apps forward the signed-in user's email in request headers
    return st.context.headers.get("X-Forwarded-Email") or "unknown"

# Load Pinned IDs from Delta Lake
def get_pinned_ids():
    try:
        df_pinned = run_query(f"SELECT opportunity_id FROM {PINS_TABLE}")
        return set(df_pinned["opportunity_id"].tolist())
    except Exception:
        return set()

# Toggle pin state in Delta Lake
def toggle_pin(opportunity_id, is_pinned):
    if is_pinned:
        run_statement(f"DELETE FROM {PINS_TABLE} WHERE opportunity_id = :opp_id", {"opp_id": opportunity_id})
    else:
        run_statement(
            f"INSERT INTO {PINS_TABLE} VALUES (:opp_id, :user, current_timestamp())",
            {"opp_id": opportunity_id, "user": get_current_user()},
        )
    st.rerun()

if not WAREHOUSE_ID:
    st.error("DATABRICKS_WAREHOUSE_ID is not set. Add a SQL warehouse resource to the app (see app.yaml).")
    st.stop()

pinned_ids = get_pinned_ids()

st.title("🏥 Market Opportunities & Hospital Group Directory")
st.caption("Read-only snapshot synced from ClickUp | Managed natively via Unity Catalog")

# -------------------------------------------------------------------------
# Sidebar: Category Selection & Pinned Filter
# -------------------------------------------------------------------------
categories = [
    "All Categories",
    "Academic Medical Centers",
    "Regional Health Systems",
    "Community Hospital Networks",
    "Integrated Delivery Networks (IDNs)",
    "Specialty & Surgical Groups"
]

st.sidebar.header("Filter & Search")
selected_category = st.sidebar.selectbox("Market Category", categories)
show_pinned_only = st.sidebar.checkbox("📌 Show Pinned Only", value=False)

# Fetch Opportunities from Delta Lake
# (Note: In production, this reads from your main.clienthub.clickup_doc_snapshots or tasks table)
df_opps = run_query(f"SELECT * FROM {OPPS_TABLE} ORDER BY opportunity_id")

if selected_category != "All Categories":
    df_opps = df_opps[df_opps["market_category"] == selected_category]

if show_pinned_only:
    df_opps = df_opps[df_opps["opportunity_id"].isin(pinned_ids)]

# -------------------------------------------------------------------------
# Metric Summary Header
# -------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Groups", len(df_opps))
col2.metric("Pinned Target Accounts", len(df_opps[df_opps['opportunity_id'].isin(pinned_ids)]))
avg_beds = df_opps["bed_count"].mean()
col3.metric("Avg Bed Count", f"{int(avg_beds):,}" if pd.notna(avg_beds) else "N/A")
col4.metric("Active Market Sectors", df_opps['market_category'].nunique() if not df_opps.empty else 0)

st.divider()

# -------------------------------------------------------------------------
# Interactive Hospital Group Directory
# -------------------------------------------------------------------------
if df_opps.empty:
    st.info("No hospital opportunities found matching your filters.")
else:
    for idx, row in df_opps.iterrows():
        opp_id = row["opportunity_id"]
        is_pinned = opp_id in pinned_ids
        
        # UI Card Box
        with st.container():
            c1, c2, c3 = st.columns([0.05, 0.7, 0.25])
            
            # Pin Button
            pin_label = "📌" if is_pinned else "📍"
            if c1.button(pin_label, key=f"pin_{opp_id}", help="Pin or unpin this account"):
                toggle_pin(opp_id, is_pinned)
                
            # Hospital Group Title & Quick Attributes
            c2.markdown(f"### {row['hospital_name']} `{row['market_category']}`")
            beds = f"{int(row['bed_count']):,}" if pd.notna(row["bed_count"]) else "N/A"
            c2.markdown(f"**Region:** {row['location']} | **EHR System:** {row['ehr_platform']} | **Beds:** {beds}")

            # Clickable Details Expander
            with c2.expander("🔍 View Account Intelligence & ClickUp Mirror Notes"):
                st.markdown(f"**Overview:**\n\n{row['overview']}")
                st.markdown(f"**Key Strategic Priorities:**\n\n{row['strategic_priorities']}")
                
                # Source Link back to ClickUp Doc/Task
                if pd.notna(row.get("clickup_url")) and row["clickup_url"]:
                    st.markdown(f"🔗 [View Source in ClickUp]({row['clickup_url']})")
            
            # Key Stakeholders & Contact Info
            c3.info(f"**Primary Lead:**\n\n{row['account_lead']}\n\n**Status:** {row['stage']}")
            st.divider()