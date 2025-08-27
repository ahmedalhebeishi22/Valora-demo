
# valora_streamlit.py
import streamlit as st
import os
import json
import time
import pandas as pd
import matplotlib.pyplot as plt

try:
    import openai
except Exception:
    openai = None

SYSTEM_PROMPT = """
You are Valora — a concise, data-driven real estate investment advisor.
Respond ONLY in valid JSON (no extra text) following this schema exactly:

{
  "property": {
    "address": "<string>",
    "estimated_current_value": <number>,
    "currency": "USD"
  },
  "prediction": {
    "annual_growth_pct": <number>,
    "projection_years": <int>,
    "projected_values": [
      { "year": 2025, "value": 312000 }
    ],
    "confidence_pct": <number>
  },
  "strategy": {
    "best_strategy": "<flip|buy_hold|rental|wholesale|other>",
    "explanation": "<short plain-sentence reason>",
    "expected_roi_pct": <number>
  },
  "negotiation_tip": {
    "amount_off_suggestion": <number>,
    "reason": "<one-line reason>"
  },
  "comparables": [
    { "address": "<string>", "sale_price": <number>, "days_on_market": <int> }
  ],
  "alternative_opportunities": [
    { "type": "duplex|nearby_house|lot", "address": "<string>", "estimated_roi_pct": <number> }
  ]
}

Use conservative, professional tone. If any input is missing, make a reasonable assumption but set "confidence_pct" lower.
"""

DEMO_RESULTS = {
    "123 Main St, Los Angeles, CA": {
      "property": {"address":"123 Main St, Los Angeles, CA","estimated_current_value":750000,"currency":"USD"},
      "prediction":{"annual_growth_pct":4.5,"projection_years":3,"projected_values":[{"year":2025,"value":783750},{"year":2026,"value":818900},{"year":2027,"value":855120}],"confidence_pct":78},
      "strategy":{"best_strategy":"buy_hold","explanation":"Strong rental demand and steady appreciation in this zip code.","expected_roi_pct":8.1},
      "negotiation_tip":{"amount_off_suggestion":20000,"reason":"Older roof and 45 days on market give negotiating leverage."},
      "comparables":[{"address":"118 Elm St","sale_price":732000,"days_on_market":38},{"address":"234 Oak Ave","sale_price":769000,"days_on_market":22}],
      "alternative_opportunities":[{"type":"duplex","address":"200 Maple St","estimated_roi_pct":9.2}]
    }
}

def call_openai_chat(messages, model="gpt-4", temperature=0.2, max_tokens=700):
    if openai is None:
        raise RuntimeError("openai library not installed or failed to import.")
    api_key = (
        os.getenv("OPENAI_API_KEY") or
        (st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else None)
    )
    if not api_key:
        raise RuntimeError("OpenAI API key not found. Set environment variable OPENAI_API_KEY or use Streamlit secrets.")
    openai.api_key = api_key

    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp["choices"][0]["message"]["content"]

def parse_json_safe(txt):
    try:
        cleaned = txt.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[1:-1])
        return json.loads(cleaned)
    except Exception as e:
        try:
            start = txt.find("{")
            end = txt.rfind("}") + 1
            return json.loads(txt[start:end])
        except Exception:
            raise

def projection_chart(projected_values, currency="USD"):
    years = [p["year"] for p in projected_values]
    vals = [p["value"] for p in projected_values]
    fig, ax = plt.subplots()
    ax.plot(years, vals, marker="o")
    ax.set_title("Value Projection")
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Estimated Value ({currency})")
    ax.grid(True)
    st.pyplot(fig)

st.set_page_config(page_title="Valora — AI Demo", layout="wide")
st.title("Valora — AI Real Estate Investment Advisor (Streamlit Demo)")

with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("OpenAI API Key (or set as env var)", type="password")
    if api_key_input:
        st.session_state["OPENAI_API_KEY_TEMP"] = api_key_input
    demo_mode = st.checkbox("Demo mode (use canned responses)", value=True)
    model = st.selectbox("Model (change if you want)", options=["gpt-4", "gpt-4o", "gpt-3.5-turbo"], index=0)
    st.markdown("---")
    st.markdown("Tips:\n- Use Demo mode for safe demos.\n- Provide purchase price for better projections.")

with st.form("analyze_form"):
    st.subheader("Property Input")
    address = st.text_input("Address (example: 123 Main St, Los Angeles, CA)", value="123 Main St, Los Angeles, CA")
    estimated_value = st.number_input("Estimated current value (USD) — optional", min_value=0, value=0, step=1000)
    purchase_price = st.number_input("Purchase price (USD) — optional", min_value=0, value=0, step=1000)
    years = st.slider("Projection years", min_value=1, max_value=7, value=3)
    submit = st.form_submit_button("Analyze")

if submit:
    st.info("Running Valora analysis...")
    time.sleep(0.5)

    user_prompt = {
      "role": "user",
      "content": json.dumps({
          "address": address,
          "estimated_current_value": estimated_value if estimated_value>0 else None,
          "purchase_price": purchase_price if purchase_price>0 else None,
          "projection_years": years
      })
    }

    if demo_mode and address in DEMO_RESULTS:
        st.success("Demo mode: using canned result for a smooth presentation.")
        result = DEMO_RESULTS[address]
    elif demo_mode:
        base = estimated_value if estimated_value>0 else (purchase_price if purchase_price>0 else 300000)
        annual = 3.2
        projected = []
        current_year = pd.Timestamp.now().year
        for i in range(1, years+1):
            val = round(base * ((1+annual/100) ** i))
            projected.append({"year": current_year + i, "value": val})
        result = {
            "property":{"address":address,"estimated_current_value":base,"currency":"USD"},
            "prediction":{"annual_growth_pct":annual,"projection_years":years,"projected_values":projected,"confidence_pct":60},
            "strategy":{"best_strategy":"buy_hold","explanation":"Conservative recommendation based on generic market trends.","expected_roi_pct":5.8},
            "negotiation_tip":{"amount_off_suggestion":int(base*0.03),"reason":"Typical minor repairs & market friction."},
            "comparables":[],
            "alternative_opportunities":[]
        }
    else:
        messages = [
            {"role":"system", "content": SYSTEM_PROMPT},
            user_prompt
        ]
        if "OPENAI_API_KEY_TEMP" in st.session_state:
            os.environ["OPENAI_API_KEY"] = st.session_state["OPENAI_API_KEY_TEMP"]
        try:
            raw = call_openai_chat(messages, model=model)
            st.text_area("Raw AI response (JSON)", value=raw, height=200)
            result = parse_json_safe(raw)
        except Exception as e:
            st.error(f"AI call / parse failed: {str(e)}")
            st.stop()

    st.header("Valora Report")
    col1, col2, col3 = st.columns([2,2,1])

    with col1:
        st.subheader("Property")
        st.write(result["property"]["address"])
        st.metric("Estimated value", f'{result["property"]["estimated_current_value"]:,} {result["property"]["currency"]}')

    with col2:
        st.subheader("Prediction")
        pred = result["prediction"]
        st.write(f"Annual growth (est): {pred['annual_growth_pct']}%")
        st.write(f"Confidence: {pred['confidence_pct']}%")
        projection_chart(pred["projected_values"], result["property"]["currency"])

    with col3:
        st.subheader("Strategy")
        st.write(result["strategy"]["best_strategy"].upper())
        st.write(result["strategy"]["explanation"])
        st.metric("Expected ROI (est)", f"{result['strategy']['expected_roi_pct']}%")

    st.subheader("Negotiation Tip")
    nt = result.get("negotiation_tip", {})
    st.write(f"Suggest: ${nt.get('amount_off_suggestion',0):,}")
    st.write(nt.get("reason",""))

    if result.get("comparables"):
        st.subheader("Comparables")
        df = pd.DataFrame(result["comparables"])
        st.dataframe(df)

    if result.get("alternative_opportunities"):
        st.subheader("Alternative Opportunities")
        df2 = pd.DataFrame(result["alternative_opportunities"])
        st.dataframe(df2)

    st.markdown("---")
    st.caption("Valora demo — results are suggestions only. For production, connect Valora to authoritative data sources (MLS/Zillow) and use proper legal/disclosure workflows.")
