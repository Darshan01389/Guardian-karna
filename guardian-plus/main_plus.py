import streamlit as st

# Page Configuration
st.set_page_config(page_title='Guardian Karna Plus', layout='wide')

# Sidebar Navigation
st.sidebar.title('Navigation')
page = st.sidebar.selectbox('Select a page:', ['Dashboard', 'Security', 'Analytics', 'Games', 'Settings'])

# Page Content
if page == 'Dashboard':
    st.title('Dashboard')
    st.write('Welcome to the Guardian Karna Plus Dashboard!')

elif page == 'Security':
    st.title('Security')
    st.write('Security settings and configurations can be managed here.')

elif page == 'Analytics':
    st.title('Analytics')
    st.write('View and analyze user data and interactions.')

elif page == 'Games':
    st.title('Games')
    st.write('Engage with interactive games for users.')

elif page == 'Settings':
    st.title('Settings')
    st.write('Configure your preferences and account settings.')
