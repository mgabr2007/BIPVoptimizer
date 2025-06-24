-- BIPV Optimizer Database Schema
-- Comprehensive schema for storing all workflow analysis data

-- Projects table - stores basic project information
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    timezone VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'EUR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather data table - stores TMY and current weather data
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    description TEXT,
    annual_ghi DECIMAL(10, 2),
    annual_dni DECIMAL(10, 2),
    annual_dhi DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Building elements table - stores BIM extracted window/facade data
CREATE TABLE IF NOT EXISTS building_elements (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    element_id VARCHAR(100),
    wall_element_id VARCHAR(100),
    element_type VARCHAR(50),
    orientation VARCHAR(50),
    azimuth DECIMAL(5, 1),
    glass_area DECIMAL(10, 2),
    window_width DECIMAL(8, 2),
    window_height DECIMAL(8, 2),
    building_level VARCHAR(100),
    family VARCHAR(100),
    pv_suitable BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Radiation analysis table - stores solar radiation calculations
CREATE TABLE IF NOT EXISTS radiation_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    avg_irradiance DECIMAL(10, 2),
    peak_irradiance DECIMAL(10, 2),
    shading_factor DECIMAL(5, 4),
    grid_points INTEGER,
    analysis_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Element radiation table - stores radiation data per building element
CREATE TABLE IF NOT EXISTS element_radiation (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    element_id VARCHAR(100),
    annual_radiation DECIMAL(12, 2),
    irradiance DECIMAL(10, 2),
    orientation_multiplier DECIMAL(5, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PV specifications table - stores PV technology parameters
CREATE TABLE IF NOT EXISTS pv_specifications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    panel_type VARCHAR(100),
    efficiency DECIMAL(5, 2),
    transparency DECIMAL(5, 2),
    cost_per_m2 DECIMAL(10, 2),
    power_density DECIMAL(8, 2),
    installation_factor DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Energy analysis table - stores yield vs demand calculations
CREATE TABLE IF NOT EXISTS energy_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    annual_generation DECIMAL(12, 2),
    annual_demand DECIMAL(12, 2),
    net_energy_balance DECIMAL(12, 2),
    self_consumption_rate DECIMAL(5, 2),
    energy_yield_per_m2 DECIMAL(8, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial analysis table - stores economic calculations
CREATE TABLE IF NOT EXISTS financial_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    initial_investment DECIMAL(12, 2),
    annual_savings DECIMAL(12, 2),
    annual_generation DECIMAL(12, 2),
    annual_export_revenue DECIMAL(12, 2),
    annual_om_cost DECIMAL(12, 2),
    net_annual_benefit DECIMAL(12, 2),
    npv DECIMAL(12, 2),
    irr DECIMAL(5, 2),
    payback_period DECIMAL(5, 2),
    lcoe DECIMAL(8, 4),
    analysis_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Environmental impact table - stores CO2 and environmental metrics
CREATE TABLE IF NOT EXISTS environmental_impact (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    co2_savings_annual DECIMAL(10, 2),
    co2_savings_lifetime DECIMAL(12, 2),
    carbon_value DECIMAL(12, 2),
    trees_equivalent INTEGER,
    cars_equivalent INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimization results table - stores genetic algorithm solutions
CREATE TABLE IF NOT EXISTS optimization_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    solution_id VARCHAR(50),
    capacity DECIMAL(10, 2),
    roi DECIMAL(5, 2),
    net_import DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    rank_position INTEGER,
    pareto_optimal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(project_name);
CREATE INDEX IF NOT EXISTS idx_building_elements_project ON building_elements(project_id);
CREATE INDEX IF NOT EXISTS idx_building_elements_element ON building_elements(element_id);
CREATE INDEX IF NOT EXISTS idx_element_radiation_project ON element_radiation(project_id);
CREATE INDEX IF NOT EXISTS idx_financial_analysis_project ON financial_analysis(project_id);
CREATE INDEX IF NOT EXISTS idx_optimization_results_project ON optimization_results(project_id);

-- Create a view for comprehensive project reports
CREATE OR REPLACE VIEW project_report_view AS
SELECT 
    p.id as project_id,
    p.project_name,
    p.location,
    p.latitude,
    p.longitude,
    p.timezone,
    p.currency,
    w.temperature,
    w.annual_ghi,
    ra.avg_irradiance,
    ra.peak_irradiance,
    ra.shading_factor,
    pv.panel_type,
    pv.efficiency,
    pv.transparency,
    pv.cost_per_m2,
    ea.annual_generation,
    ea.annual_demand,
    ea.net_energy_balance,
    fa.initial_investment,
    fa.annual_savings,
    fa.npv,
    fa.irr,
    fa.payback_period,
    ei.co2_savings_annual,
    ei.co2_savings_lifetime,
    COUNT(be.id) as total_elements,
    SUM(CASE WHEN be.pv_suitable THEN 1 ELSE 0 END) as suitable_elements,
    SUM(be.glass_area) as total_glass_area
FROM projects p
LEFT JOIN weather_data w ON p.id = w.project_id
LEFT JOIN radiation_analysis ra ON p.id = ra.project_id
LEFT JOIN pv_specifications pv ON p.id = pv.project_id
LEFT JOIN energy_analysis ea ON p.id = ea.project_id
LEFT JOIN financial_analysis fa ON p.id = fa.project_id
LEFT JOIN environmental_impact ei ON p.id = ei.project_id
LEFT JOIN building_elements be ON p.id = be.project_id
GROUP BY p.id, p.project_name, p.location, p.latitude, p.longitude, p.timezone, p.currency,
         w.temperature, w.annual_ghi, ra.avg_irradiance, ra.peak_irradiance, ra.shading_factor,
         pv.panel_type, pv.efficiency, pv.transparency, pv.cost_per_m2,
         ea.annual_generation, ea.annual_demand, ea.net_energy_balance,
         fa.initial_investment, fa.annual_savings, fa.npv, fa.irr, fa.payback_period,
         ei.co2_savings_annual, ei.co2_savings_lifetime;