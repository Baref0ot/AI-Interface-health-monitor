from langsmith import expect
import psycopg2
import json

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="interface_monitor",
        user="user",
        password="password"
    )

def get_all_events():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT interface_id, vendor, rows_synced, null_rate,
               execution_time_ms, anomaly
        FROM interface_events
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "interface_id": r[0],
            "vendor": r[1],
            "rows_synced": r[2],
            "null_rate": r[3],
            "execution_time_ms": r[4],
            "anomaly": r[5]
           #, "embedding": r[6]
        }
        for r in rows
    ]


def get_anomalies():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT interface_id, vendor, rows_synced, null_rate,
               execution_time_ms, anomaly
        FROM interface_events
        WHERE anomaly IS NOT NULL
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "interface_id": r[0],
            "vendor": r[1],
            "rows_synced": r[2],
            "null_rate": r[3],
            "execution_time_ms": r[4],
            "anomaly": r[5]
        }
        for r in rows
    ]


def get_latest_event(interface_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT interface_id, vendor, rows_synced, null_rate,
               execution_time_ms, anomaly
        FROM interface_events
        WHERE interface_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (interface_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "interface_id": row[0],
        "vendor": row[1],
        "rows_synced": row[2],
        "null_rate": row[3],
        "execution_time_ms": row[4],
        "anomaly": row[5]
    }


def get_all_events_with_embeddings():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT interface_id, vendor, rows_synced, null_rate,
               execution_time_ms, anomaly, embedding
        FROM interface_events
        WHERE embedding IS NOT NULL
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "interface_id": r[0],
            "vendor": r[1],
            "rows_synced": r[2],
            "null_rate": r[3],
            "execution_time_ms": r[4],
            "anomaly": r[5],
            "embedding": r[6]  
        }
        for r in rows
    ]


def save_analysis(
    interface_id: str,
    anomaly: str,
    similarity_score: float,
    similar_interface_id: str,
    root_cause: str
    ):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analyses (
            interface_id,
            anomaly,
            similarity_score,
            similar_interface_id,
            root_cause
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        interface_id,
        anomaly,
        similarity_score,
        similar_interface_id,
        root_cause
    ))
    conn.commit()
    conn.close()


def get_latest_analysis():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, interface_id, anomaly, similarity_score,
               similar_interface_id, root_cause, created_at
        FROM analyses
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    
    try:
        root_cause = json.loads(row[5])
    except json.JSONDecodeError:
        root_cause_payload = {
            "raw_text": row[5]
        }
    
    return {
        "id": row[0],
        "interface_id": row[1],
        "anomaly": row[2],
        "similarity_score": round(row[3], 3) if row[3] is not None else None,
        "similar_interface_id": row[4],
        "root_cause": root_cause,
        "created_at": row[6]
    }



def get_recent_events_for_agency(interface_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT interface_id, anomaly, timestamp
        FROM interface_events
        WHERE interface_id = %s
        ORDER BY timestamp DESC
        LIMIT 10
    """, (interface_id,))

    same_agency_events_rows = cur.fetchall()
    conn.close()

    same_agency_events = [
        {
            "interface_id": row[0],
            "anomaly": row[1],
            "timestamp": row[2]
        }
        for row in same_agency_events_rows
    ]
    return same_agency_events



def get_past_events_globally():
 #fetch past events with embeddings to compare against for cross-agency similarity in case we've seen this type of failure before in another agency.
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT interface_id, vendor, rows_synced, null_rate, execution_time_ms, anomaly, embedding
            FROM interface_events
            WHERE embedding IS NOT NULL and anomaly IS NOT NULL
            LIMIT 50
        """)     
        global_agency_events_rows = cur.fetchall()
        conn.close()

        global_agency_events = [
            {
                "interface_id": row[0],
                "vendor": row[1],
                "rows_synced": row[2],
                "null_rate": row[3],
                "execution_time_ms": row[4],
                "anomaly": row[5],
                "embedding": row[6],
            }
            for row in global_agency_events_rows
        ]
        return global_agency_events


    

        