import unittest
from services.energy_price_api import (
    fetch_current_german_rates, fetch_eu_energy_prices, get_live_rates_for_country,
)


class TariffProvenanceTests(unittest.TestCase):
    def test_unimplemented_adapter_never_claims_fetched_tariffs(self):
        results = [fetch_current_german_rates(), fetch_eu_energy_prices()]
        results += [get_live_rates_for_country(c) for c in ('DE', 'FR', 'UK', 'US')]
        for result in results:
            self.assertFalse(result['success'])
            self.assertEqual(result['data_quality'], 'unavailable')
            for fabricated_field in ('source', 'import_rate', 'export_rate', 'timestamp'):
                self.assertNotIn(fabricated_field, result)
            self.assertIn('contract', result['error'])
