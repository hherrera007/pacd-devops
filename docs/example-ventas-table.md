# Example Ventas Table

This table is not part of the AWS infrastructure. It is an example PostgreSQL table used to show how the demo database can store sales records.

## Table: ventas

```sql
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario > 0),
    cliente VARCHAR(150) NOT NULL,
    total NUMERIC(12,2) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Columns

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `SERIAL` | Yes | Auto-increment primary key. |
| `fecha` | `DATE` | Yes | Sale date. |
| `producto` | `VARCHAR(100)` | Yes | Product name. |
| `categoria` | `VARCHAR(100)` | Yes | Product category. |
| `cantidad` | `INTEGER` | Yes | Quantity sold. Must be greater than `0`. |
| `precio_unitario` | `NUMERIC(10,2)` | Yes | Unit price. Must be greater than `0`. |
| `cliente` | `VARCHAR(150)` | Yes | Customer name. |
| `total` | `NUMERIC(12,2)` | Yes | Total sale amount. |
| `fecha_registro` | `TIMESTAMP` | No | Insert timestamp. Defaults to `CURRENT_TIMESTAMP`. |

## Notes

- `cantidad` and `precio_unitario` include positive-value checks.
- `total` is stored directly in the table.
- `fecha_registro` is automatically set when the row is inserted if no value is provided.
