-- Insert more garages
INSERT INTO garages (id, name, location, capacity) VALUES
(3, 'Garage C', 'Midtown', 40),
(4, 'Garage D', 'Uptown', 35);

-- Insert more services
INSERT INTO services (id, service_name, price, garage_id) VALUES
(5, 'Battery Replacement', 120.0, 1),
(6, 'Car Wash', 25.0, 2),
(7, 'Alignment Check', 60.0, 3),
(8, 'Tire Balancing', 80.0, 3),
(9, 'Transmission Repair', 500.0, 4);

-- Insert more provided services
INSERT INTO provided_services (id, service_id, customer_id, date_provided) VALUES
(5, 5, 5, '2025-01-19'),
(6, 6, 6, '2025-01-20'),
(7, 7, 7, '2025-01-21'),
(8, 8, 8, '2025-01-22'),
(9, 9, 9, '2025-01-23'),
(10, 1, 10, '2025-01-24'),
(11, 2, 11, '2025-01-25'),
(12, 3, 12, '2025-01-26');