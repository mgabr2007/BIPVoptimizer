"""
FastAPI endpoints for PV specification module.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from .models import (
    PanelSpecification, ElementPVSpecification, ProjectPVSummary,
    BuildingElement, RadiationRecord
)
from .services.spec_calculator import spec_calculator
from .services.panel_catalog import panel_catalog_manager
from .db.queries import specification_queries, project_data_queries
from .config import security_config, API_ENDPOINTS


router = APIRouter(prefix=API_ENDPOINTS["base_path"])


@router.get("/panel-catalog", response_model=List[PanelSpecification])
async def get_panel_catalog(
    panel_type: Optional[str] = Query(None, description="Filter by panel type"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer")
):
    """Get BIPV panel catalog with optional filtering."""
    try:
        if panel_type:
            panels = await panel_catalog_manager.get_panels_by_type_async(panel_type)
        else:
            panels = await panel_catalog_manager.get_all_panels_async()
        
        if manufacturer:
            panels = [p for p in panels if manufacturer.lower() in p.manufacturer.lower()]
        
        return panels
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve catalog: {e}")


@router.get("/pv-specs/{project_id}", response_model=List[ElementPVSpecification])
async def get_project_specifications(project_id: int):
    """Get PV specifications for a project."""
    try:
        specifications = await specification_queries.get_project_specifications_async(project_id)
        return specifications
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve specifications: {e}")


@router.get("/pv-summary/{project_id}", response_model=Dict[str, Any])
async def get_project_summary(project_id: int):
    """Get project PV summary statistics."""
    try:
        summary = await specification_queries.get_specification_summary_async(project_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Project summary not found")
        
        # Get orientation breakdown
        orientation_data = await project_data_queries.get_orientation_breakdown_async(project_id)
        summary.update(orientation_data)
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {e}")


@router.post("/calculate-specifications", response_model=Dict[str, Any])
async def calculate_specifications(
    project_id: int,
    panel_id: int,
    coverage_factor: Optional[float] = 0.85,
    performance_ratio: Optional[float] = 0.85
):
    """Calculate PV specifications for a project."""
    try:
        # Get panel specification
        panel = await panel_catalog_manager.get_panel_by_id_async(panel_id)
        if not panel:
            raise HTTPException(status_code=404, detail="Panel not found")
        
        # Get building elements and radiation data
        elements_data = await specification_queries.get_building_elements_with_radiation_async(project_id)
        
        if not elements_data:
            raise HTTPException(status_code=404, detail="No building elements found")
        
        # Convert to model objects
        elements = []
        radiation_records = []
        
        for data in elements_data:
            if data.get('pv_suitable', True) and data.get('annual_radiation'):
                element = BuildingElement(
                    element_id=data['element_id'],
                    project_id=project_id,
                    orientation=data['orientation'],
                    azimuth=data.get('azimuth', 0),
                    glass_area=data['glass_area'],
                    pv_suitable=data.get('pv_suitable', True)
                )
                elements.append(element)
                
                radiation = RadiationRecord(
                    element_id=data['element_id'],
                    project_id=project_id,
                    annual_radiation=data['annual_radiation'],
                    shading_factor=data.get('shading_factor', 1.0)
                )
                radiation_records.append(radiation)
        
        # Run calculation
        specifications, metrics = spec_calculator.calculate_specifications(
            elements=elements,
            radiation_data=radiation_records,
            panel_spec=panel,
            coverage_factor=coverage_factor,
            performance_ratio=performance_ratio
        )
        
        # Save to database
        if specifications:
            await specification_queries.bulk_upsert_specifications_async(specifications)
        
        # Return results
        return {
            "success": True,
            "specifications_count": len(specifications),
            "calculation_metrics": metrics.dict(),
            "summary": {
                "total_power_kw": sum(s.system_power for s in specifications),
                "total_energy_kwh": sum(s.annual_energy for s in specifications),
                "total_cost_eur": sum(s.total_cost for s in specifications)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {e}")


@router.delete("/pv-specs/{project_id}")
async def clear_project_specifications(project_id: int):
    """Clear all specifications for a project."""
    try:
        count = await specification_queries.clear_project_specifications_async(project_id)
        return {"success": True, "deleted_count": count}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear specifications: {e}")


@router.get("/export/{project_id}/{format}")
async def export_project_data(project_id: int, format: str):
    """Export project data in various formats."""
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    try:
        specifications = await specification_queries.get_project_specifications_async(project_id)
        
        if not specifications:
            raise HTTPException(status_code=404, detail="No specifications found")
        
        if format == "json":
            export_data = {
                "project_id": project_id,
                "specifications": [spec.dict() for spec in specifications],
                "exported_at": datetime.now().isoformat(),
                "total_elements": len(specifications)
            }
            return JSONResponse(content=export_data)
        
        elif format == "csv":
            # Convert to CSV format
            import pandas as pd
            import io
            
            df = pd.DataFrame([spec.dict() for spec in specifications])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            from fastapi.responses import Response
            return Response(
                content=csv_buffer.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=pv_specs_{project_id}.csv"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


# Include router in main FastAPI app:
# from step6_pv_spec.api import router as pv_spec_router
# app.include_router(pv_spec_router)