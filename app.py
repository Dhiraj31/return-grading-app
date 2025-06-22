import streamlit as st
from openai import OpenAI
import os
import base64
from PIL import Image
import io
import json
import ast
from collections import Counter
import re

# Set your OpenAI API Key (or use environment variable)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
st.set_page_config(page_title="Return Grading AI Demo", layout="wide")
st.title("🎯 Smart Return Grading System")

st.markdown("""
Welcome to the **AI-powered product return grading demo**. Upload images of returned products and let the AI:
- Assess product condition
- Provide a reasoning summary
- Recommend next action (e.g., sell, refurb, or charge fee)
""")

uploaded_files = st.file_uploader(
    "📤 Upload product images (JPG, JPEG, PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

results = []

def image_to_data_url(image_bytes):
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"

def clean_json_response(response_text):
    try:
        response_text = re.sub(r"```json|```", "", response_text).strip()
        return ast.literal_eval(response_text)
    except:
        return None

if uploaded_files:
    st.markdown("---")
    st.header("🔍 AI Inspection in Progress")
    cols = st.columns(len(uploaded_files))

    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx]:
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

        with st.spinner(f"Analyzing {uploaded_file.name}..."):
            image_bytes = uploaded_file.read()
            data_url = image_to_data_url(image_bytes)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI that assesses returned products for condition."},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Analyze the product image and determine its return condition:\n"
                                    "- Is the product new, like new, used, or damaged?\n"
                                    "- Are tags or packaging present?\n"
                                    "- Are there visible signs of wear or damage?\n\n"
                                    "Return a JSON object with:\n"
                                    "{\n"
                                    "  'condition': 'new' | 'like new' | 'used' | 'damaged',\n"
                                    "  'reason': '<short reason>',\n"
                                    "  'action': 'Sell as New | Sell as Used | Charge Fee | Route to Refurb | Route to Donation',\n"
                                    "  'next_step': 'Send to FC (new) | Send to Refurb (used) | Send to Liquidation (damaged)'\n"
                                    "}"
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            }
                        ]
                    }
                ]
            )

            result_text = response.choices[0].message.content.strip()
            result_json = clean_json_response(result_text)

            if result_json:
                results.append({"file": uploaded_file.name, **result_json})

    st.markdown("---")
    st.header("📊 AI Grading Results")
    condition_summary = []
    action_summary = []
    next_step_summary = []
    reasons = []

    for res in results:
        st.markdown(f"#### 🖼 {res['file']}")
        st.markdown(f"**Condition:** `{res['condition']}`")
        st.markdown(f"**Why it seems {res['condition']}:** {res['reason']}")
        st.markdown(f"**Recommended Action:** 🚚 {res['action']}")
        st.markdown(f"**Next Step:** 🏷️ {res['next_step']}")
        st.markdown("---")
        condition_summary.append(res['condition'])
        action_summary.append(res['action'])
        next_step_summary.append(res['next_step'])
        reasons.append(res['reason'])

    if condition_summary:
        most_common_condition = Counter(condition_summary).most_common(1)[0][0]
        most_common_action = Counter(action_summary).most_common(1)[0][0]
        most_common_next_step = Counter(next_step_summary).most_common(1)[0][0]
        sample_reason = Counter(reasons).most_common(1)[0][0]

        st.markdown("## 🧠 Final Recommendation Across All Images")
        st.success(f"**Final Condition:** {most_common_condition}")
        st.info(f"**Why it seems {most_common_condition}:** {sample_reason}")
        st.warning(f"**Recommended Action:** {most_common_action}")
        st.markdown(f"**Next Step:** 🏷️ {most_common_next_step}")

st.caption("This is a prototype demo for AI-powered return grading. Built with ❤️ by Dhiraj.")
