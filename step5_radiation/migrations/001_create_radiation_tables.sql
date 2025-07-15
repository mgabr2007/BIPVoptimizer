-- Migration 001: Create radiation analysis tables and indexes
-- Purpose: Establish database schema for production-grade radiation analysis

-- Create element_radiation table for storing analysis results
CREATE TABLE IF NOT EXISTS element_radiation (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    orientation VARCHAR(20) NOT NULL,
    azimuth DECIMAL(5,1) NOT NULL,
    glass_area DECIMAL(10,2) NOT NULL,
    annual_radiation DECIMAL(10,2) NOT NULL,
    peak_radiation DECIMAL(10,2),
    monthly_radiation JSONB,
    shading_factor DECIMAL(5,3) DEFAULT 1.0,
    processing_time DECIMAL(8,3),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT element_radiation_unique UNIQUE (project_id, element_id),
    CONSTRAINT element_radiation_radiation_range CHECK (annual_radiation >= 0 AND annual_radiation <= 3000),
    CONSTRAINT element_radiation_azimuth_range CHECK (azimuth >= 0 AND azimuth <= 360),
    CONSTRAINT element_radiation_area_positive CHECK (glass_area > 0),
    CONSTRAINT element_radiation_shading_range CHECK (shading_factor >= 0 AND shading_factor <= 1),
    
    -- Foreign key to projects table
    CONSTRAINT fk_element_radiation_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create radiation_analysis_sessions table for tracking analysis runs
CREATE TABLE IF NOT EXISTS radiation_analysis_sessions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    session_key VARCHAR(100) NOT NULL,
    precision_level VARCHAR(20) NOT NULL,
    configuration JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'running',
    total_elements INTEGER,
    completed_elements INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_time TIMESTAMP,
    error_message TEXT,
    
    -- Constraints
    CONSTRAINT fk_radiation_session_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT radiation_session_unique UNIQUE (project_id, session_key),
    CONSTRAINT radiation_session_status_valid CHECK (status IN ('running', 'completed', 'failed', 'stopped'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_element_radiation_project_id ON element_radiation(project_id);
CREATE INDEX IF NOT EXISTS idx_element_radiation_element_id ON element_radiation(element_id);
CREATE INDEX IF NOT EXISTS idx_element_radiation_orientation ON element_radiation(orientation);
CREATE INDEX IF NOT EXISTS idx_element_radiation_annual_radiation ON element_radiation(annual_radiation);
CREATE INDEX IF NOT EXISTS idx_element_radiation_calculated_at ON element_radiation(calculated_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_element_radiation_project_orientation ON element_radiation(project_id, orientation);
CREATE INDEX IF NOT EXISTS idx_element_radiation_project_calculated ON element_radiation(project_id, calculated_at);

-- Index for analysis sessions
CREATE INDEX IF NOT EXISTS idx_radiation_sessions_project_status ON radiation_analysis_sessions(project_id, status);
CREATE INDEX IF NOT EXISTS idx_radiation_sessions_start_time ON radiation_analysis_sessions(start_time);

-- Create or replace views for aggregations
CREATE OR REPLACE VIEW radiation_orientation_stats AS
SELECT 
    project_id,
    orientation,
    COUNT(*) as element_count,
    AVG(annual_radiation) as avg_radiation,
    SUM(annual_radiation * glass_area) as total_energy_potential,
    MIN(annual_radiation) as min_radiation,
    MAX(annual_radiation) as max_radiation,
    STDDEV(annual_radiation) as radiation_stddev,
    SUM(glass_area) as total_glass_area
FROM element_radiation
GROUP BY project_id, orientation;

CREATE OR REPLACE VIEW project_radiation_overview AS
SELECT 
    er.project_id,
    COUNT(er.element_id) as total_analyzed_elements,
    AVG(er.annual_radiation) as avg_annual_radiation,
    SUM(er.glass_area) as total_glass_area,
    SUM(er.annual_radiation * er.glass_area) as total_annual_energy,
    MIN(er.calculated_at) as analysis_start,
    MAX(er.calculated_at) as analysis_completion,
    -- Performance metrics
    AVG(er.processing_time) as avg_processing_time,
    SUM(er.processing_time) as total_processing_time
FROM element_radiation er
GROUP BY er.project_id;

CREATE OR REPLACE VIEW radiation_performance_ranking AS
SELECT 
    project_id,
    element_id,
    orientation,
    annual_radiation,
    glass_area,
    (annual_radiation * glass_area) as energy_potential,
    RANK() OVER (PARTITION BY project_id ORDER BY annual_radiation DESC) as radiation_rank,
    RANK() OVER (PARTITION BY project_id ORDER BY (annual_radiation * glass_area) DESC) as energy_rank,
    PERCENT_RANK() OVER (PARTITION BY project_id ORDER BY annual_radiation DESC) as radiation_percentile
FROM element_radiation;

-- Create stored procedure for bulk radiation data cleanup
CREATE OR REPLACE FUNCTION cleanup_old_radiation_data(
    retention_days INTEGER DEFAULT 90
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM element_radiation 
    WHERE calculated_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also cleanup old sessions
    DELETE FROM radiation_analysis_sessions 
    WHERE start_time < (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function for radiation statistics calculation
CREATE OR REPLACE FUNCTION calculate_radiation_statistics(
    p_project_id INTEGER
) RETURNS TABLE (
    orientation VARCHAR(20),
    element_count BIGINT,
    avg_radiation NUMERIC,
    total_energy NUMERIC,
    glass_area NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        er.orientation,
        COUNT(*)::BIGINT as element_count,
        AVG(er.annual_radiation) as avg_radiation,
        SUM(er.annual_radiation * er.glass_area) as total_energy,
        SUM(er.glass_area) as glass_area
    FROM element_radiation er
    WHERE er.project_id = p_project_id
    GROUP BY er.orientation
    ORDER BY avg_radiation DESC;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_radiation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_radiation_timestamp ON element_radiation;
CREATE TRIGGER trigger_update_radiation_timestamp
    BEFORE UPDATE ON element_radiation
    FOR EACH ROW
    EXECUTE FUNCTION update_radiation_timestamp();

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON element_radiation TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON radiation_analysis_sessions TO postgres;
GRANT USAGE, SELECT ON SEQUENCE element_radiation_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE radiation_analysis_sessions_id_seq TO postgres;

-- Add comments for documentation
COMMENT ON TABLE element_radiation IS 'Stores radiation analysis results for individual building elements';
COMMENT ON COLUMN element_radiation.annual_radiation IS 'Annual radiation in kWh/m²/year';
COMMENT ON COLUMN element_radiation.shading_factor IS 'Applied shading factor (0.0 to 1.0)';
COMMENT ON COLUMN element_radiation.monthly_radiation IS 'Monthly radiation breakdown stored as JSON';

COMMENT ON TABLE radiation_analysis_sessions IS 'Tracks radiation analysis execution sessions';
COMMENT ON COLUMN radiation_analysis_sessions.configuration IS 'Analysis configuration stored as JSON';

COMMENT ON VIEW radiation_orientation_stats IS 'Aggregated radiation statistics by orientation';
COMMENT ON VIEW project_radiation_overview IS 'Project-level radiation analysis overview';
COMMENT ON VIEW radiation_performance_ranking IS 'Element performance ranking with percentiles';

-- Migration completion log
INSERT INTO schema_migrations (version, description, executed_at) 
VALUES ('001', 'Create radiation analysis tables and indexes', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;