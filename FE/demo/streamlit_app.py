import streamlit as st
import requests
import os
import json

st.set_page_config(page_title="AfyaMate / repo_mapper Demo", layout="wide")

st.title("repo_mapper Demo UI")
st.markdown("A small UI to call the Jac `repo_mapper` walker and view JSON reports.")

# server and token config
JAC_SERVER = st.text_input("Jac server base URL", value="http://localhost:8000")
JAC_TOKEN = st.text_input("Jac token (or export JAC_TOKEN as env var)", value=os.environ.get("JAC_TOKEN", ""), type="password")
url = st.text_input("Repository URL to clone", value="https://github.com/jaseci-labs/jaseci")

st.caption("Notes: start your Jac API server in another terminal with `jac serve BE/repo_mapper.jac`.")

col1, col2 = st.columns(2)

with col1:
    if st.button("List walkers"):
        try:
            r = requests.get(f"{JAC_SERVER}/walkers", headers={"Authorization": f"Bearer {JAC_TOKEN}"} if JAC_TOKEN else {})
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Error: {e}")
with col2:
    st.write("Call repo_mapper walker")

if st.button("Run repo_mapper"):
    payload = {"fields": {"url": url}}  # server expects fields wrapper for walker
    headers = {"Content-Type": "application/json"}
    if JAC_TOKEN:
        headers["Authorization"] = f"Bearer {JAC_TOKEN}"
    try:
        with st.spinner("Calling walker... this may take a minute for clones"):
            r = requests.post(f"{JAC_SERVER}/walker/repo_mapper", headers=headers, json=payload, timeout=300)
        try:
            rj = r.json()
        except Exception:
            st.error(f"Non-JSON response: {r.text}")
            rj = None
        if r.status_code != 200:
            st.error(f"HTTP {r.status_code} - {rj or r.text}")
        else:
            st.success("Call succeeded (HTTP 200)")
            st.subheader("Result object")
            st.json(rj.get("result"))
            st.subheader("Reports")
            st.json(rj.get("reports"))
    except Exception as e:
        st.error(f"Request failed: {e}")

st.markdown("### Curl example (copy/paste to terminal B)")
st.code("""curl -s -X POST "http://localhost:8000/walker/repo_mapper" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $JAC_TOKEN" \\
  -d '{"fields": {"url":"https://github.com/jaseci-labs/jaseci"}}' | jq .""", language="bash")
