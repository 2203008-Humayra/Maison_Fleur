# Software Requirements Specification (SRS)

## 1. Project Overview

Maison Fleur is a web-based flower bouquet ordering system that allows customers to create personalized bouquets using real flowers and place orders for delivery. Customers can select flowers, specify quantities, choose wrapping paper and ribbons and add personal messages. The system also provides an administrative interface for managing the flower catalog and customer orders.

## 2. Functional Requirements

### FR-01: User Management
- The system shall allow customers to register and log in.
- The system shall allow users to log out securely.
- The system shall distinguish between customer and administrator roles.

### FR-02: Flower Catalog
- The system shall display available flowers with their names, images, descriptions, and prices.
- Customers shall be able to browse the flower catalog.
- Administrators shall be able to add, update, and remove flowers.

### FR-03: Bouquet Customization
- Customers shall be able to select multiple types of flowers.
- Customers shall be able to specify the quantity of each selected flower.
- Customers shall be able to choose wrapping paper and ribbon styles.
- Customers shall be able to add a personal message to their bouquets.
- The system shall calculate the total bouquet price based on the selected items.

### FR-04: Order Management
- Customers shall be able to place bouquet orders.
- Customers shall provide recipient information and a delivery address.
- Customers shall be able to specify a preferred delivery date.
- The system shall store order details in the database.

### FR-05: Order Tracking and Administration
- Customers shall be able to view their order details and current status.
- Administrators shall be able to view and manage customer orders.
- Administrators shall be able to update order statuses.

## 3. Non-Functional Requirements

### NFR-01: Usability
- The website shall provide a simple and user-friendly interface.
- Navigation shall be consistent across all pages.
- The bouquet customization process shall be easy to understand.

### NFR-02: Performance
- The website shall load pages within a reasonable time under normal usage.
- The system shall process customer requests without unnecessary delays.

### NFR-03: Security
- User passwords shall be stored in hashed form.
- Unauthorized users shall not be allowed to access administrative functions.
- Sensitive configuration information shall not be exposed publicly.

### NFR-04: Reliability
- Order information shall be stored persistently in the database.
- The system shall validate user input before processing requests.
- The system shall handle invalid inputs without unexpected failures.

### NFR-05: Maintainability
- The source code shall follow a consistent project structure.
- The system shall support future feature additions.
- Individual functionalities shall be designed to simplify testing and maintenance.

## 4. User Roles

| User Role | Responsibilities |
|---|---|
| Customer | Register, log in, browse flowers, customize bouquets, place orders and track orders. |
| Administrator | Manage flowers, view customer orders and update order statuses. |

## 5. Project Constraints

- The application shall be developed using Python and Flask.
- HTML, CSS, and JavaScript shall be used for frontend development.
- MySQL shall be used for persistent data storage.
- The application shall support customer and administrator roles.
- Online payment gateway integration and live GPS delivery tracking are outside the initial project scope.