-- Migration 002: Create PV specification tables and indexes
-- Purpose: Establish database schema for production-grade PV specification analysis

-- Create panel_catalog table for BIPV glass specifications
CREATE TABLE IF NOT EXISTS panel_catalog (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    panel_type VARCHAR(20) NOT NULL CHECK (panel_type IN ('opaque', 'semi_transparent')),
    efficiency DECIMAL(5,4) NOT NULL,
    transparency DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    power_density DECIMAL(6,2) NOT NULL,
    cost_per_m2 DECIMAL(8,2) NOT NULL,
    glass_thickness DECIMAL(5,2) NOT NULL DEFAULT 6.0,
    u_value DECIMAL(5,2) NOT NULL DEFAULT 2.0,
    glass_weight DECIMAL(6,2) NOT NULL DEFAULT 25.0,
    performance_ratio DECIMAL(4,3) NOT NULL DEFAULT 0.85,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT panel_catalog_name_unique UNIQUE (name, manufacturer),
    CONSTRAINT panel_catalog_efficiency_range CHECK (efficiency >= 0.02 AND efficiency <= 0.25),
    CONSTRAINT panel_catalog_transparency_range CHECK (transparency >= 0.0 AND transparency <= 0.65),
    CONSTRAINT panel_catalog_power_density_range CHECK (power_density >= 10 AND power_density <= 250),
    CONSTRAINT panel_catalog_cost_range CHECK (cost_per_m2 >= 50 AND cost_per_m2 <= 1000),
    CONSTRAINT panel_catalog_performance_ratio_range CHECK (performance_ratio >= 0.60 AND performance_ratio <= 0.95)
);

-- Create element_pv_specifications table for calculated specifications
CREATE TABLE IF NOT EXISTS element_pv_specifications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    panel_spec_id INTEGER NOT NULL,
    glass_area DECIMAL(10,3) NOT NULL,
    panel_coverage DECIMAL(5,3) NOT NULL,
    effective_area DECIMAL(10,3) NOT NULL,
    system_power DECIMAL(10,4) NOT NULL,
    annual_radiation DECIMAL(10,2) NOT NULL,
    annual_energy DECIMAL(12,2) NOT NULL,
    specific_yield DECIMAL(8,1) NOT NULL,
    total_cost DECIMAL(12,2) NOT NULL,
    cost_per_wp DECIMAL(8,3) NOT NULL,
    orientation VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT element_pv_specs_unique UNIQUE (project_id, element_id),
    CONSTRAINT element_pv_specs_glass_area_positive CHECK (glass_area > 0),
    CONSTRAINT element_pv_specs_coverage_range CHECK (panel_coverage >= 0 AND panel_coverage <= 1),
    CONSTRAINT element_pv_specs_system_power_positive CHECK (system_power >= 0),
    CONSTRAINT element_pv_specs_annual_energy_positive CHECK (annual_energy >= 0),
    CONSTRAINT element_pv_specs_cost_positive CHECK (total_cost >= 0),
    
    -- Foreign keys
    CONSTRAINT fk_element_pv_specs_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_element_pv_specs_panel FOREIGN KEY (panel_spec_id) REFERENCES panel_catalog(id) ON DELETE RESTRICT,
    CONSTRAINT fk_element_pv_specs_element FOREIGN KEY (project_id, element_id) REFERENCES building_elements(project_id, element_id) ON DELETE CASCADE
);

-- Create project_pv_summaries table for aggregated project results
CREATE TABLE IF NOT EXISTS project_pv_summaries (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL UNIQUE,
    total_elements INTEGER NOT NULL DEFAULT 0,
    suitable_elements INTEGER NOT NULL DEFAULT 0,
    specified_elements INTEGER NOT NULL DEFAULT 0,
    total_glass_area DECIMAL(12,3) NOT NULL DEFAULT 0,
    total_effective_area DECIMAL(12,3) NOT NULL DEFAULT 0,
    total_system_power DECIMAL(12,4) NOT NULL DEFAULT 0,
    total_annual_energy DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_system_cost DECIMAL(15,2) NOT NULL DEFAULT 0,
    avg_specific_yield DECIMAL(8,1) NOT NULL DEFAULT 0,
    avg_cost_per_wp DECIMAL(8,3) NOT NULL DEFAULT 0,
    orientation_breakdown JSONB,
    power_breakdown JSONB,
    cost_breakdown JSONB,
    panel_type_distribution JSONB,
    analysis_settings JSONB,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    CONSTRAINT fk_project_pv_summary_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_panel_catalog_type_active ON panel_catalog(panel_type, is_active);
CREATE INDEX IF NOT EXISTS idx_panel_catalog_manufacturer ON panel_catalog(manufacturer);
CREATE INDEX IF NOT EXISTS idx_panel_catalog_efficiency ON panel_catalog(efficiency DESC);
CREATE INDEX IF NOT EXISTS idx_panel_catalog_cost ON panel_catalog(cost_per_m2);

-- Indexes for element_pv_specifications
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_id ON element_pv_specifications(project_id);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_element_id ON element_pv_specifications(element_id);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_panel_id ON element_pv_specifications(panel_spec_id);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_orientation ON element_pv_specifications(orientation);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_system_power ON element_pv_specifications(system_power DESC);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_annual_energy ON element_pv_specifications(annual_energy DESC);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_cost ON element_pv_specifications(total_cost);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_element ON element_pv_specifications(project_id, element_id);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_orientation ON element_pv_specifications(project_id, orientation);
CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_panel ON element_pv_specifications(project_id, panel_spec_id);

-- Index for project summaries
CREATE INDEX IF NOT EXISTS idx_project_pv_summaries_project_id ON project_pv_summaries(project_id);
CREATE INDEX IF NOT EXISTS idx_project_pv_summaries_completed ON project_pv_summaries(completed_at);

-- Create or replace views for common aggregations
CREATE OR REPLACE VIEW pv_specification_overview AS
SELECT 
    eps.project_id,
    COUNT(eps.element_id) as total_specified_elements,
    SUM(eps.glass_area) as total_glass_area,
    SUM(eps.effective_area) as total_effective_area,
    SUM(eps.system_power) as total_system_power,
    SUM(eps.annual_energy) as total_annual_energy,
    SUM(eps.total_cost) as total_system_cost,
    AVG(eps.specific_yield) as avg_specific_yield,
    AVG(eps.cost_per_wp) as avg_cost_per_wp,
    MIN(eps.created_at) as analysis_start,
    MAX(eps.created_at) as analysis_completion
FROM element_pv_specifications eps
GROUP BY eps.project_id;

CREATE OR REPLACE VIEW pv_orientation_performance AS
SELECT 
    eps.project_id,
    eps.orientation,
    COUNT(*) as element_count,
    SUM(eps.system_power) as total_power_kw,
    SUM(eps.annual_energy) as total_energy_kwh,
    SUM(eps.total_cost) as total_cost_eur,
    AVG(eps.specific_yield) as avg_specific_yield,
    AVG(eps.cost_per_wp) as avg_cost_per_wp,
    SUM(eps.effective_area) as total_effective_area
FROM element_pv_specifications eps
GROUP BY eps.project_id, eps.orientation
ORDER BY total_power_kw DESC;

CREATE OR REPLACE VIEW panel_usage_statistics AS
SELECT 
    pc.id as panel_id,
    pc.name as panel_name,
    pc.manufacturer,
    pc.panel_type,
    COUNT(eps.element_id) as usage_count,
    SUM(eps.system_power) as total_installed_power,
    SUM(eps.effective_area) as total_installed_area,
    AVG(eps.specific_yield) as avg_achieved_yield,
    COUNT(DISTINCT eps.project_id) as projects_used
FROM panel_catalog pc
LEFT JOIN element_pv_specifications eps ON pc.id = eps.panel_spec_id
WHERE pc.is_active = true
GROUP BY pc.id, pc.name, pc.manufacturer, pc.panel_type
ORDER BY usage_count DESC;

CREATE OR REPLACE VIEW cost_efficiency_analysis AS
SELECT 
    eps.project_id,
    eps.orientation,
    eps.element_id,
    eps.system_power,
    eps.annual_energy,
    eps.total_cost,
    eps.cost_per_wp,
    eps.specific_yield,
    -- Cost efficiency metrics
    (eps.annual_energy / eps.total_cost) as energy_per_euro,
    (eps.system_power / eps.total_cost * 1000) as watts_per_euro,
    -- Performance rankings
    RANK() OVER (PARTITION BY eps.project_id ORDER BY eps.specific_yield DESC) as yield_rank,
    RANK() OVER (PARTITION BY eps.project_id ORDER BY eps.cost_per_wp ASC) as cost_rank,
    RANK() OVER (PARTITION BY eps.project_id ORDER BY (eps.annual_energy / eps.total_cost) DESC) as efficiency_rank
FROM element_pv_specifications eps;

-- Create stored procedures for common operations
CREATE OR REPLACE FUNCTION calculate_project_pv_summary(
    p_project_id INTEGER
) RETURNS TABLE (
    total_elements BIGINT,
    total_power NUMERIC,
    total_energy NUMERIC,
    total_cost NUMERIC,
    avg_yield NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_elements,
        SUM(eps.system_power) as total_power,
        SUM(eps.annual_energy) as total_energy,
        SUM(eps.total_cost) as total_cost,
        AVG(eps.specific_yield) as avg_yield
    FROM element_pv_specifications eps
    WHERE eps.project_id = p_project_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_top_performing_elements(
    p_project_id INTEGER,
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    element_id VARCHAR(50),
    orientation VARCHAR(20),
    system_power NUMERIC,
    annual_energy NUMERIC,
    specific_yield NUMERIC,
    cost_per_wp NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        eps.element_id,
        eps.orientation,
        eps.system_power,
        eps.annual_energy,
        eps.specific_yield,
        eps.cost_per_wp
    FROM element_pv_specifications eps
    WHERE eps.project_id = p_project_id
    ORDER BY eps.specific_yield DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create function for bulk specification cleanup
CREATE OR REPLACE FUNCTION cleanup_old_specifications(
    retention_days INTEGER DEFAULT 90
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM element_pv_specifications 
    WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also cleanup old summaries
    DELETE FROM project_pv_summaries 
    WHERE updated_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update project summary when specifications change
CREATE OR REPLACE FUNCTION update_project_pv_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO project_pv_summaries (
        project_id,
        total_elements,
        suitable_elements,
        specified_elements,
        total_glass_area,
        total_effective_area,
        total_system_power,
        total_annual_energy,
        total_system_cost,
        avg_specific_yield,
        avg_cost_per_wp,
        orientation_breakdown,
        power_breakdown,
        cost_breakdown,
        updated_at
    )
    SELECT 
        NEW.project_id,
        (SELECT COUNT(*) FROM building_elements WHERE project_id = NEW.project_id),
        (SELECT COUNT(*) FROM building_elements WHERE project_id = NEW.project_id AND pv_suitable = true),
        COUNT(*),
        SUM(glass_area),
        SUM(effective_area),
        SUM(system_power),
        SUM(annual_energy),
        SUM(total_cost),
        AVG(specific_yield),
        AVG(cost_per_wp),
        json_object_agg(orientation, COUNT(*)) FILTER (WHERE orientation IS NOT NULL),
        json_object_agg(orientation, SUM(system_power)) FILTER (WHERE orientation IS NOT NULL),
        json_object_agg(orientation, SUM(total_cost)) FILTER (WHERE orientation IS NOT NULL),
        CURRENT_TIMESTAMP
    FROM element_pv_specifications
    WHERE project_id = NEW.project_id
    GROUP BY project_id
    ON CONFLICT (project_id) 
    DO UPDATE SET
        specified_elements = EXCLUDED.specified_elements,
        total_glass_area = EXCLUDED.total_glass_area,
        total_effective_area = EXCLUDED.total_effective_area,
        total_system_power = EXCLUDED.total_system_power,
        total_annual_energy = EXCLUDED.total_annual_energy,
        total_system_cost = EXCLUDED.total_system_cost,
        avg_specific_yield = EXCLUDED.avg_specific_yield,
        avg_cost_per_wp = EXCLUDED.avg_cost_per_wp,
        orientation_breakdown = EXCLUDED.orientation_breakdown,
        power_breakdown = EXCLUDED.power_breakdown,
        cost_breakdown = EXCLUDED.cost_breakdown,
        updated_at = EXCLUDED.updated_at;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_project_pv_summary ON element_pv_specifications;
CREATE TRIGGER trigger_update_project_pv_summary
    AFTER INSERT OR UPDATE OR DELETE ON element_pv_specifications
    FOR EACH ROW
    EXECUTE FUNCTION update_project_pv_summary();

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_pv_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_panel_catalog_timestamp ON panel_catalog;
CREATE TRIGGER trigger_update_panel_catalog_timestamp
    BEFORE UPDATE ON panel_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_pv_timestamp();

DROP TRIGGER IF EXISTS trigger_update_project_summary_timestamp ON project_pv_summaries;
CREATE TRIGGER trigger_update_project_summary_timestamp
    BEFORE UPDATE ON project_pv_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_pv_timestamp();

-- Insert default BIPV panel specifications
INSERT INTO panel_catalog (
    name, manufacturer, panel_type, efficiency, transparency, power_density,
    cost_per_m2, glass_thickness, u_value, glass_weight, performance_ratio
) VALUES 
    ('Heliatek HeliaSol 436-2000', 'Heliatek', 'opaque', 0.089, 0.0, 89.0, 183.0, 1.5, 1.1, 15.0, 0.85),
    ('SUNOVATION eFORM Clear', 'SUNOVATION', 'semi_transparent', 0.11, 0.35, 110.0, 400.0, 6.0, 2.8, 25.0, 0.85),
    ('Solarnova SOL_GT Translucent', 'Solarnova', 'semi_transparent', 0.132, 0.22, 132.0, 185.0, 10.0, 1.8, 30.0, 0.85),
    ('Solarwatt Vision AM 4.5', 'Solarwatt', 'semi_transparent', 0.219, 0.20, 219.0, 87.0, 8.0, 1.5, 28.0, 0.85),
    ('AVANCIS SKALA 105-110W', 'AVANCIS', 'opaque', 0.102, 0.0, 102.0, 244.0, 6.0, 1.2, 22.0, 0.85)
ON CONFLICT (name, manufacturer) DO NOTHING;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON panel_catalog TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON element_pv_specifications TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON project_pv_summaries TO postgres;
GRANT USAGE, SELECT ON SEQUENCE panel_catalog_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE element_pv_specifications_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE project_pv_summaries_id_seq TO postgres;

-- Add comments for documentation
COMMENT ON TABLE panel_catalog IS 'BIPV panel catalog with specifications and pricing';
COMMENT ON COLUMN panel_catalog.efficiency IS 'Panel efficiency as decimal (0.089 = 8.9%)';
COMMENT ON COLUMN panel_catalog.transparency IS 'Glass transparency as decimal (0.35 = 35%)';
COMMENT ON COLUMN panel_catalog.power_density IS 'Power density in W/m² under standard conditions';

COMMENT ON TABLE element_pv_specifications IS 'Calculated PV specifications for individual building elements';
COMMENT ON COLUMN element_pv_specifications.panel_coverage IS 'Panel coverage factor (0-1)';
COMMENT ON COLUMN element_pv_specifications.specific_yield IS 'Specific energy yield in kWh/kW/year';

COMMENT ON TABLE project_pv_summaries IS 'Aggregated PV analysis summaries for projects';
COMMENT ON COLUMN project_pv_summaries.orientation_breakdown IS 'Element count by orientation (JSON)';

COMMENT ON VIEW pv_specification_overview IS 'Project-level PV specification overview with key metrics';
COMMENT ON VIEW pv_orientation_performance IS 'Performance breakdown by orientation';
COMMENT ON VIEW panel_usage_statistics IS 'Panel usage statistics across projects';
COMMENT ON VIEW cost_efficiency_analysis IS 'Cost efficiency analysis with rankings';

-- Migration completion log
INSERT INTO schema_migrations (version, description, executed_at) 
VALUES ('002', 'Create PV specification tables and indexes', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;