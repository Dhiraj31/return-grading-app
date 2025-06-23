import streamlit as st
import openai
import os
import base64
from PIL import Image
import io
import json
import ast
import re

# Set your OpenAI API Key (or use environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Return Grading AI Demo", layout="wide")
st.title("🎯 Smart Return Grading System")

st.markdown("""
Welcome to the **AI-powered product return grading demo**. Upload multiple images of a returned product and let the AI:
- Assess the product condition
- Provide a reasoning summary
- Recommend the next action (e.g., sell, refurb, or charge fee)
""")

if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
    st.session_state.result_json = None

uploaded_files = st.file_uploader(
    "📤 Upload multiple images of a single product (JPG, JPEG, PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="file_uploader"
)

def image_to_data_url(image_bytes):
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"

def clean_json_response(response_text):
    try:
        response_text = re.sub(r"```json|```", "", response_text).strip()
        return ast.literal_eval(response_text)
    except:
        return None

if uploaded_files and uploaded_files != st.session_state.last_uploaded:
    st.session_state.last_uploaded = uploaded_files
    st.session_state.result_json = None
    st.markdown("---")
    st.header("🔍 AI Inspection in Progress")
    image_blocks = []

    for uploaded_file in uploaded_files:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        image_bytes = uploaded_file.read()
        data_url = image_to_data_url(image_bytes)
        image_blocks.append({"type": "image_url", "image_url": {"url": data_url}})

    with st.spinner("Analyzing all images together..."):
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI that assesses returned products for condition."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze these images of a single returned product and determine its return condition:\n"
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
                        *image_blocks
                    ]
                }
            ]
        )

        result_text = response.choices[0].message.content.strip()
        st.session_state.result_json = clean_json_response(result_text)

if st.session_state.result_json:
    st.markdown("---")
    st.header("📊 AI Grading Result")
    res = st.session_state.result_json
    st.markdown(f"**Condition:** `{res['condition']}`")
    st.markdown(f"**Why it seems {res['condition']}:** {res['reason']}")
    st.markdown(f"**Recommended Action:** 🚚 {res['action']}")
    st.markdown(f"**Next Step:** 🏷️ {res['next_step']}")

st.caption("This is a prototype demo for AI-powered return grading. Built with ❤️ by Dhiraj.")
