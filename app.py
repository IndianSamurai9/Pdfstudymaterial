import streamlit as st
import openai
import json
from dotenv import load_dotenv
import os

from prompts import SYSTEM_PROMPT
from renderer import generate_pdf
from utils import extract_json_from_llm_response, validate_and_fix_data

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="OS Handwritten Notes Generator", layout="wide")
st.title("📝 OS Notes → Handwritten PDF Generator")
st.markdown("Paste your OS textbook/content below, and AI will extract scheduling, paging, and inode data to create a beautiful handwritten PDF.")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", value=openai.api_key or "")
    if api_key:
        openai.api_key = api_key
    
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. Paste your OS notes (any length).
    2. Click **Generate Notes**.
    3. GPT-4 extracts structured data.
    4. Renders Gantt Chart, Page Table, Inode + handwriting.
    5. Download your PDF!
    """)
    st.markdown("---")
    st.caption("Uses GPT-4. Costs ~$0.02 per generation.")

# ---------- MAIN AREA ----------
col1, col2 = st.columns([1, 1])

with col1:
    user_input = st.text_area(
        "📄 Paste your Operating Systems notes here:",
        height=400,
        placeholder="Example: In FCFS scheduling, P1 arrives at 0 with burst 8, P2 at 1 with burst 4...\n\nPage tables map virtual to physical. A valid bit indicates the page is in memory...\n\nInodes contain direct, single indirect, and double indirect pointers...",
    )
    
    # Sample data button
    if st.button("📥 Load Sample OS Text"):
        sample_text = """
        FCFS scheduling is simple but suffers from the convoy effect. 
        Process P1 arrives at time 0 with CPU burst 8ms. 
        Process P2 arrives at time 1 with burst 4ms. 
        Process P3 arrives at time 2 with burst 5ms.
        
        For memory management, paging divides memory into fixed-size frames.
        A page table has valid/invalid bits. Frame 0 holds Page 0 (valid) and Page 2 (valid), 
        but Page 1 and Page 3 are invalid (not in memory). Frame 1 holds Page 1 and Page 3 as valid.
        
        In Unix file systems, inodes store metadata. 
        Direct pointers point to data blocks 12, 45, and 78.
        Single indirect points to block 101. Double indirect points to block 202.
        """
        user_input = sample_text

with col2:
    if st.button("🚀 Generate Handwritten PDF", type="primary", use_container_width=True):
        if not user_input:
            st.error("Please paste some OS notes first!")
        elif not openai.api_key:
            st.error("Please enter your OpenAI API key in the sidebar!")
        else:
            with st.spinner("🧠 AI is analyzing your OS notes..."):
                try:
                    # 1. Call LLM
                    client = openai.OpenAI(api_key=openai.api_key)
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",  # or "gpt-3.5-turbo" for cheaper
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Convert these OS notes to JSON:\n\n{user_input}"}
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"}  # Forces valid JSON
                    )
                    
                    raw_output = response.choices[0].message.content
                    st.info("✅ LLM Raw Response (check JSON):")
                    st.code(raw_output, language="json")
                    
                    # 2. Parse & Validate
                    json_str = extract_json_from_llm_response(raw_output)
                    data = json.loads(json_str)
                    data = validate_and_fix_data(data)
                    
                    st.success("✅ Successfully parsed OS structure!")
                    
                    # 3. Generate PDF
                    with st.spinner("🖍️ Rendering diagrams and handwriting..."):
                        pdf_bytes = generate_pdf(data)
                        
                        # 4. Download button
                        st.download_button(
                            label="📥 Download OS_Handwritten_Notes.pdf",
                            data=pdf_bytes,
                            file_name="OS_Handwritten_Notes.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Show preview (first page as image)
                        st.image(pdf_bytes[:100000], caption="Preview (Page 1)", use_column_width=True)
                        
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse LLM JSON. Please check the raw output above. Error: {e}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.exception(e)

# ---------- FOOTER ----------
st.markdown("---")
st.caption("Made for deep OS study. Fork me on GitHub! (Requires OpenAI API key)")
