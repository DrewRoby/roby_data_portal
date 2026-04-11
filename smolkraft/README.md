# Smolkraft — The Crafter's ERP

Smolkraft helps small-batch producers go from hobby to business. It tracks your materials, purchase orders, recipes (bills of materials), step-by-step production processes (bills of operations), production runs, and inventory — so you can price accurately, plan production, and never run out of a key ingredient mid-batch.

Smolkraft is integrated into Roby Data Portal as a Django app mounted at `/smolkraft/`. Authentication is handled by the portal's session auth — no separate login. The API lives at `/smolkraft/api/`.

---

## Data Model

### `BaseTable` (abstract)
All primary tables inherit from this. Provides:

| Field | Notes |
|---|---|
| `insert_user` | Integer ID of the portal user who created the record |
| `insert_dttm` | Auto-set on creation |
| `update_user` | Integer ID of the user who last modified the record |
| `update_dttm` | Auto-set on update |

User IDs are stored as plain integers (not ForeignKeys) because smolkraft lives on its own database, separate from the portal's `auth_user` table.

---

### `Material`
A raw material, component, or finished good. The central reference object that almost everything else points to.

| Field | Type | Notes |
|---|---|---|
| `description` | CharField(512) | Long-form description |
| `short_name` | CharField(64) | Display name used throughout the UI |
| `bom_header` | FK → BOMHeader (nullable) | Set if this material is manufactured internally rather than purchased |

---

### `Vendor`
A supplier from whom materials are purchased.

| Field | Type | Notes |
|---|---|---|
| `vendor_name` | CharField(256) | |

---

### `OrderHeader`
A purchase order placed with a vendor.

| Field | Type | Notes |
|---|---|---|
| `owner_user_id` | IntegerField | Portal user who owns this order |
| `vendor` | FK → Vendor | |
| `vendor_order_id` | CharField(128) | Vendor's own PO number |
| `order_date` | DateField | |
| `cost_subtotal / tax / shipping / discount / total` | Decimal(10,2) | Cost breakdown |
| `item_count` | IntegerField | Number of line items |

Unique constraint: `(owner_user_id, vendor, cost_total)`.

---

### `OrderLineItem`
An individual line on a purchase order.

| Field | Type | Notes |
|---|---|---|
| `owner_user_id` | IntegerField | |
| `order_header` | FK → OrderHeader | |
| `material` | FK → Material | |
| `item_count` | IntegerField | |
| `sku / upc` | CharField(128) | Optional vendor identifiers |
| `unit_price` | Decimal(10,2) | Price per unit |
| `unit_amount` | Decimal(12,4) | Quantity per unit (e.g. 500 for a 500g bag) |
| `unit_uom` | CharField(4) | Unit of measure — see UOM list below |

---

### `BOMHeader` (Bill of Materials)
Defines a recipe for producing one batch of a product.

| Field | Type | Notes |
|---|---|---|
| `owner_user_id` | IntegerField | |
| `product_name` | CharField(64) | |
| `description` | CharField(256) | |
| `output_quantity` | Decimal(12,4) | How much the recipe produces per batch |
| `output_uom` | CharField(4) | Unit of measure of the output |

---

### `BOMLine`
One ingredient/component within a BOM.

| Field | Type | Notes |
|---|---|---|
| `bom_header` | FK → BOMHeader | |
| `material` | FK → Material | |
| `quantity` | Decimal(14,6) | Amount required per batch |
| `uom` | CharField(4) | Unit of measure |

---

### `BOOHeader` (Bill of Operations)
Defines the sequence of steps needed to produce a BOM. One-to-one with `BOMHeader`.

---

### `Operation`
One step in a bill of operations.

| Field | Type | Notes |
|---|---|---|
| `boo_header` | FK → BOOHeader | |
| `sequence_number` | PositiveSmallIntegerField | Determines display/execution order |
| `description` | CharField(3000) | Full step instructions |
| `estimated_time` | Decimal(10,2) (nullable) | |
| `time_uom` | CharField(10) (nullable) | e.g. "minutes", "hours" |

---

### `ProductionOrder`
A planned or completed production run of a BOM.

| Field | Type | Notes |
|---|---|---|
| `owner_user_id` | IntegerField | |
| `bom_header` | FK → BOMHeader | What is being produced |
| `production_date` | DateField | |
| `quantity` | PositiveSmallIntegerField | Number of batches |
| `status` | CharField | `planned` / `in_progress` / `completed` / `cancelled` |

---

### `Inventory`
A lot of material in stock, optionally linked to the production order that created it.

| Field | Type | Notes |
|---|---|---|
| `owner_user_id` | IntegerField | |
| `material` | FK → Material | |
| `quantity` | Decimal(14,6) | |
| `uom` | CharField(4) | |
| `production_order` | FK → ProductionOrder (nullable) | Set for manufactured lots; null for purchased material |
| `location` | CharField(50) | Storage location, optional |

---

### `UnitConversion`
Conversion factors between units of measure.

| Field | Type | Notes |
|---|---|---|
| `from_unit_name` | CharField(32) | |
| `to_unit_name` | CharField(32) | |
| `multiply_by` | Decimal(16,10) | |

> **Note:** This table exists but is not yet wired into any business logic. Shortfall and production possibility calculations currently assume all quantities for a given material share the same UOM.

---

### Supported Units of Measure

`C`, `CL`, `CM`, `DL`, `FLOZ`, `G`, `IN`, `KG`, `L`, `LB`, `M`, `MG`, `ML`, `MM`, `OZ`, `PC`, `TBSP`, `THOU`, `TSP`, `UNIT`, `YD`

---

## API Reference

Base path: `/smolkraft/api/`

All endpoints require an authenticated portal session. The DRF browsable API is available when `DEBUG=True`.

---

### Materials — `/smolkraft/api/materials/`

Standard CRUD, scoped to the authenticated user (`insert_user`).

| Method | Path | Description |
|---|---|---|
| GET | `/materials/` | List all materials for the current user |
| POST | `/materials/` | Create a material |
| GET | `/materials/{id}/` | Retrieve a single material |
| PUT/PATCH | `/materials/{id}/` | Update a material |
| DELETE | `/materials/{id}/` | Delete a material |

**Response shape:**
```json
{
  "id": 1,
  "short_name": "AP Flour",
  "description": "All-purpose flour, unbleached"
}
```

---

### Bills of Materials — `/smolkraft/api/boms/`

Standard CRUD, scoped to `owner_user_id`. The response always includes the full ingredient list and operations sequence.

| Method | Path | Description |
|---|---|---|
| GET | `/boms/` | List all BOMs for the current user |
| POST | `/boms/` | Create a BOM header |
| GET | `/boms/{id}/` | Full BOM with lines and operations |
| PUT/PATCH | `/boms/{id}/` | Update a BOM header |
| DELETE | `/boms/{id}/` | Delete a BOM |

**Response shape:**
```json
{
  "id": 1,
  "product_name": "Sourdough Loaf",
  "description": "1kg sourdough, 75% hydration",
  "output_quantity": "1.0000",
  "output_uom": "UNIT",
  "materials": [
    {
      "id": 1,
      "material": 3,
      "material_name": "AP Flour",
      "material_description": "All-purpose flour, unbleached",
      "quantity": "500.000000",
      "uom": "G"
    }
  ],
  "operations": [
    {
      "id": 1,
      "sequence_number": 1,
      "description": "Mix flour and water. Autolyse 30 minutes.",
      "estimated_time": "30.00",
      "time_uom": "minutes"
    }
  ]
}
```

---

### Production Orders — `/smolkraft/api/production-orders/`

Standard CRUD. The list endpoint returns a summary; the single-record GET returns full detail including the BOM, what inventory was produced, and what materials would be consumed.

| Method | Path | Description |
|---|---|---|
| GET | `/production-orders/` | List all production orders |
| POST | `/production-orders/` | Create a production order |
| GET | `/production-orders/{id}/` | Full detail with BOM + consumed/produced inventory |
| PUT/PATCH | `/production-orders/{id}/` | Update |
| DELETE | `/production-orders/{id}/` | Delete |

**List response shape:**
```json
{
  "id": 1,
  "bom_header": 1,
  "product_name": "Sourdough Loaf",
  "production_date": "2025-04-01",
  "quantity": 4,
  "status": "completed"
}
```

**Detail response shape** adds:
```json
{
  "bom_details": { "...full BOM object..." },
  "inventory_produced": [
    { "id": 5, "material": "Sourdough Loaf", "quantity": "4.000000", "uom": "UNIT" }
  ],
  "materials_consumed": [
    { "material": "AP Flour", "quantity_needed": "2000.000000", "uom": "G" }
  ]
}
```

> **Note:** `materials_consumed` is calculated from the BOM × order quantity. It shows what *would* be consumed, not what was actually deducted from inventory. Actual inventory deduction is a manual step (create Inventory records linked to the production order).

---

### Inventory — `/smolkraft/api/inventory/`

Standard CRUD, scoped to `owner_user_id`.

| Method | Path | Description |
|---|---|---|
| GET | `/inventory/` | List all inventory lots |
| POST | `/inventory/` | Add a lot |
| GET | `/inventory/{id}/` | Retrieve a single lot |
| PUT/PATCH | `/inventory/{id}/` | Update |
| DELETE | `/inventory/{id}/` | Delete |

**Response shape:**
```json
{
  "id": 5,
  "material": 2,
  "material_name": "Sourdough Loaf",
  "quantity": "4.000000",
  "uom": "UNIT",
  "location": "Shelf A"
}
```

---

### Current Inventory — `GET /smolkraft/api/current-inventory/`

Returns inventory lots enriched with a derived lot number and a calculated expiration date.

- **Lot number:** `LOT-{production_order.id}` — null if the lot has no linked production order
- **Expiration date:** production date + 90 days — null if no production order is linked

**Response shape:**
```json
[
  {
    "id": 5,
    "product_name": "Sourdough Loaf",
    "lot_number": "LOT-1",
    "quantity": "4.000000",
    "uom": "UNIT",
    "expiration_date": "2025-06-30",
    "location": "Shelf A"
  }
]
```

> **Known limitation:** The 90-day expiration window is hardcoded. It should eventually be a per-material shelf-life field.

---

### Inventory Shortfall — `GET /smolkraft/api/inventory-shortfall/`

Compares current inventory against quantities referenced in purchase orders to identify materials that are needed but understocked. For each material, returns available quantity, needed quantity, and the gap.

> **Known limitation:** "Open" orders are defined as `order_date >= 2024-01-01` (hardcoded). This should use an order status field or a configurable lookback window.

**Response shape:**
```json
[
  {
    "product_id": 3,
    "product_name": "AP Flour",
    "available_quantity": "500.000000",
    "needed_quantity": "2000.000000",
    "shortfall": "1500.000000",
    "uom": "G",
    "oldest_order_date": "2025-03-15"
  }
]
```

---

### Production Possibilities — `GET /smolkraft/api/production-possibilities/`

For each BOM the user owns, calculates how many complete batches could be started given current inventory levels. Identifies the limiting component and estimates per-batch cost from the most recent purchase price of each ingredient.

**Response shape:**
```json
[
  {
    "product_id": 1,
    "product_name": "Sourdough Loaf",
    "batches_possible": 3,
    "unit_cost": "1.25",
    "limiting_component": "AP Flour",
    "component_materials": [
      {
        "material_id": 3,
        "material_name": "AP Flour",
        "required_per_batch": "500.000000",
        "available": "1500.000000",
        "max_batches": 3,
        "unit_cost": "0.80",
        "component_cost": "0.40"
      }
    ]
  }
]
```

---

## Frontend Roadmap

The API is complete. What's missing is a user-facing interface — right now `/smolkraft/` redirects to the DRF browsable API.

### Proposed page structure

| Route | Page | Primary data source |
|---|---|---|
| `/smolkraft/` | **Dashboard** | Summary cards from shortfall, production-possibilities, current-inventory |
| `/smolkraft/materials/` | Materials list | `GET /materials/` |
| `/smolkraft/materials/:id/` | Material detail | `GET /materials/{id}/` + inventory on hand |
| `/smolkraft/boms/` | BOM list | `GET /boms/` |
| `/smolkraft/boms/:id/` | BOM detail | `GET /boms/{id}/` + "start production" action |
| `/smolkraft/production-orders/` | Production order list | `GET /production-orders/` — filterable by status |
| `/smolkraft/production-orders/:id/` | Production order detail | `GET /production-orders/{id}/` — status workflow |
| `/smolkraft/inventory/` | Inventory | Tabbed: current lots / shortfall / production possibilities |

### Implementation phases

**Phase 1 — Shell and dashboard**
Establish the frontend integration pattern within Django, then build the dashboard using the three analytic endpoints. This validates the full stack and surfaces the most useful data immediately.

**Phase 2 — Inventory management**
CRUD UI for inventory lots. Most frequently updated data, simplest forms.

**Phase 3 — Materials and BOMs**
Materials list and BOM editor. The BOM editor is the most complex form: a header with dynamic line items and an optional operations list.

**Phase 4 — Production orders**
List, detail, and status workflow. Add a "complete order" action that auto-creates inventory lots from the BOM output.

**Phase 5 — Polish and known limitations**

- Per-material shelf life (replace hardcoded 90-day expiration)
- Order status field on `OrderHeader` (replace hardcoded date cutoff)
- Wire `UnitConversion` into shortfall and production calculations
- Purchase order entry UI (`OrderHeader` / `OrderLineItem` have no frontend yet)
- Auto-populate `update_user` on save (currently nothing sets it)

---

## Known Issues / Tech Debt

| Area | Issue |
|---|---|
| `ExpirationDateField` | 90-day shelf life is hardcoded; should be a per-material attribute |
| `ShortfallSerializer` | Open order date cutoff (`2024-01-01`) is a hardcoded string |
| `OrderHeader` / `OrderLineItem` | No API endpoints or UI for purchase order entry |
| `UnitConversion` | Table exists but is unused in all business logic |
| `update_user` | Field exists on every record but is never populated automatically |
