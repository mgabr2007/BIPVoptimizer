import streamlit as st

st.title("Message Display Test")

# Test all message types
st.success("✅ This is a SUCCESS message - should be green")
st.error("❌ This is an ERROR message - should be red") 
st.warning("⚠️ This is a WARNING message - should be yellow")
st.info("ℹ️ This is an INFO message - should be blue")

st.markdown("---")

# Test with containers
with st.container():
    st.success("Success message inside container")
    st.error("Error message inside container")

# Test with columns
col1, col2 = st.columns(2)
with col1:
    st.success("Success in column 1")
with col2:
    st.error("Error in column 2")

# Test with expander
with st.expander("Click to see messages"):
    st.success("Success inside expander")
    st.error("Error inside expander")