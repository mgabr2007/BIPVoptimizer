"""
Explicit availability contract for project tariff integrations.
Unverified constants must never be reported as fetched institutional data.
"""


def _unavailable(country_code):
    """No verified building tariff provider is implemented in this adapter."""
    return {
        'success': False,
        'country_code': country_code,
        'data_quality': 'unavailable',
        'error': (
            'No verified project import/export tariff is available from this adapter. '
            'Enter the building contract tariffs in Project Setup, with their source and date. '
            'Historical constants and wholesale prices are not live building tariffs.'
        ),
    }


def fetch_current_german_rates():
    """Fail explicitly until a verified project tariff integration is configured."""
    return _unavailable('DE')


def fetch_eu_energy_prices():
    """Do not attribute an unfetched hard-coded tariff table to ACER/Eurostat."""
    return _unavailable('EU')


def get_live_rates_for_country(country_code):
    return _unavailable(country_code)


def test_rate_integration():
    """Test the rate integration with German data"""
    
    import streamlit as st

    st.subheader("Testing Live Rate Integration")
    
    with st.spinner("Fetching German electricity rates..."):
        german_rates = fetch_current_german_rates()
    
    if german_rates.get('success'):
        st.success(f"Connected to: {german_rates['source']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Import Rate", f"€{german_rates['import_rate']:.3f}/kWh")
        with col2:
            st.metric("Export Rate", f"€{german_rates['export_rate']:.3f}/kWh")
        with col3:
            if 'wholesale_eur_mwh' in german_rates:
                st.metric("Wholesale Price", f"€{german_rates['wholesale_eur_mwh']:.2f}/MWh")
        
        st.info(f"Data source: {german_rates['source']}")
        st.caption(f"Last updated: {german_rates['timestamp']}")
        
        return german_rates
    else:
        st.error(f"Rate integration failed: {german_rates.get('error', 'Unknown error')}")
        return None