-- Enable logical replication
ALTER SYSTEM SET wal_level = 'logical';

-- Create a publication for the tables you want to monitor
CREATE PUBLICATION ecommerce_publication FOR TABLE users, customers, warehouses, inventory, orders, payments;

-- Create a replication slot (optional, Debezium can create this automatically)
SELECT pg_create_logical_replication_slot('ecommerce_slot', 'pgoutput');