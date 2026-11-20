terraform {
  required_version = "= 1.17.2"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "= 1.144.0"
    }
  }
  # Supply the reviewed encrypted, access-controlled backend at init time.
  backend "s3" {}
}

provider "databricks" {
  host = var.workspace_host
}

variable "workspace_host" {
  type = string
}
variable "catalog" {
  type = string
}
variable "schema_name" {
  type = string
}
variable "warehouse_id" {
  type = string
}
variable "table_name" {
  type    = string
  default = "county_indicators"
}
variable "manage_schema" {
  type    = bool
  default = false
}
variable "mcp_principal" {
  description = "App service principal application ID; set only after App adoption and grant review"
  type        = string
  default     = ""
}
variable "manage_reader_grants" {
  description = "Authoritative for this principal's grants; review existing grants first"
  type        = bool
  default     = false
}
variable "snapshot_loaded" {
  description = "True only after destination load and independent count/hash verification"
  type        = bool
  default     = false
}

data "databricks_catalog" "existing" {
  name = var.catalog
}
data "databricks_sql_warehouse" "existing" {
  id = var.warehouse_id
}
resource "databricks_schema" "research" {
  count        = var.manage_schema ? 1 : 0
  catalog_name = data.databricks_catalog.existing.name
  name         = var.schema_name
  comment      = "Reviewed public government data snapshots"
  lifecycle {
    prevent_destroy = true
  }
}
locals {
  schema = var.manage_schema ? databricks_schema.research[0].name : var.schema_name
  reader = var.manage_reader_grants ? { mcp = var.mcp_principal } : {}
}
resource "databricks_grant" "catalog_reader" {
  for_each   = local.reader
  catalog    = data.databricks_catalog.existing.name
  principal  = each.value
  privileges = ["USE_CATALOG"]
  lifecycle {
    precondition {
      condition     = var.mcp_principal != ""
      error_message = "Review and supply the destination MCP App principal first."
    }
  }
}
resource "databricks_grant" "schema_reader" {
  for_each   = local.reader
  schema     = "${var.catalog}.${local.schema}"
  principal  = each.value
  privileges = ["USE_SCHEMA"]
}
resource "databricks_grant" "table_reader" {
  for_each   = var.snapshot_loaded ? local.reader : {}
  table      = "${var.catalog}.${local.schema}.${var.table_name}"
  principal  = each.value
  privileges = ["SELECT"]
}
output "warehouse_id" {
  value = data.databricks_sql_warehouse.existing.id
}
output "schema_name" {
  value = local.schema
}
