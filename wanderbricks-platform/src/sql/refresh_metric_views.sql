-- Databricks notebook source
-- Refresh all WanderBricks metric views
-- Run after pipeline refresh to update metric views with latest data

CREATE WIDGET TEXT catalog_name DEFAULT "hls_fde_dev";
CREATE WIDGET TEXT schema_name DEFAULT "dev_matthew_giglia_wanderbricks_ai";

-- COMMAND ----------

REFRESH MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_revenue_metrics');

-- COMMAND ----------

REFRESH MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_occupancy_metrics');

-- COMMAND ----------

REFRESH MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_guest_satisfaction');

-- COMMAND ----------

REFRESH MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_host_performance');
