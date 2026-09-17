"""The pinned environment must import legacy adapters without fabricated output."""
import asyncio
import unittest
import pandas as pd
import pandera as pa

class AdapterTests(unittest.TestCase):
    def test_facade_schema_rejects_negative_area(self):
        from step4_facade_extraction.validators import DataFrameValidator
        schema=DataFrameValidator().window_schema
        row={'ElementId':'A','Family':'Window','Glass Area (m²)':10.,'Azimuth (°)':180.,
             'Level':'1','HostWallId':'W','Window Width (m)':2.,'Window Height (m)':5.}
        schema.validate(pd.DataFrame([row]))
        with self.assertRaises(pa.errors.SchemaError):schema.validate(pd.DataFrame([dict(row,**{'Glass Area (m²)':-1.})]))

    def test_placeholder_radiation_cannot_be_saved_as_research(self):
        from step5_radiation.services.analysis_runner import RadiationAnalysisOrchestrator
        from step5_radiation.db.queries import RadiationDataQueries
        orchestrator=RadiationAnalysisOrchestrator()
        with self.assertRaises(NotImplementedError):asyncio.run(orchestrator.run_analysis(1,None))
        with self.assertRaises(NotImplementedError):orchestrator._calculate_placeholder_radiation({'orientation':'south'})
