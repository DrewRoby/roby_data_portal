drop table if exists vendor;

create table vendor (
  vendor_id serial primary key,
  vendor_name varchar(255),
  created_at timestamp,
  updated_at timestamp
);

drop table if exists material_order_header;

create table material_order_header (
  material_order_header_id serial primary key,
  user_id integer,
  vendor_id integer,
  vendor_order_id varchar(100),
  cost_subtotal decimal(10,2),
  cost_tax decimal(10,2),
  cost_shipping decimal(10,2),
  discount_total decimal(10,2),
  cost_total decimal(10,2),
  item_count integer,
  order_date timestamp,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists material_order_line_item;

create table material_order_line_item (
  material_order_line_item_id serial primary key,
  material_order_header_id integer,
  matrial_id integer,
  unit_count integer,
  unit_price decimal(10,2),
  unit_amount decimal(10,2),
  uom varchar(50),
  sku varchar(50),
  upc bigint,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists recipe_header;

create table recipe_header (
  recipe_header_id serial primary key,
  owner_user_id integer not null,
  instruction_set_id integer,
  recipe_name varchar(60),
  recipe_description varchar(255),
  recipe_yield_type_id integer,
  cure_time integer,
  cure_time_unit varchar(20),
  created_at timestamp,
  updated_at timestamp
);

drop table if exists recipe_line_item;

create table recipe_line_item (
  recipe_line_item_id serial primary key,
  recipe_header_id integer,
  material_id integer,
  material_amount decimal(10,2),
  material_amount_uom varchar(20),
  created_at timestamp,
  updated_at timestamp
);

drop table if exists material;

create table material (
  material_id serial primary key,
  material_name varchar(60),
  material_short_name varchar(30),
  material_description varchar(255),
  material_stage_id integer,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists users;

create table users (
  user_id serial primary key,
  user_display_name varchar(60) not null,
  password varchar(255) not null,
  first_name varchar(30) not null,
  last_name varchar(30) not null,
  email_primary varchar(60) not null,
  email_secondary varchar(60),
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists instruction_set;

create table instruction_set (
  instruction_set_id serial primary key,
  instruction_id integer,
  material_id integer,
  ingredient_usage_set integer,
  instruction_number integer,
  owner_user_id integer,
  created_at timestamp,
  updated_at timestamp
);
drop table if exists instruction;

create table instruction (
  instruction_id serial primary key,
  instruction_set_id integer,
  instruction_text varchar(255),
  instruction_ordinal_number integer,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists substitute_set;

create table substitute_set (
  substitute_set_id serial primary key,
  recipe_header_id integer,
  recipe_item_id integer,
  substitute_material_id integer,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists batch;

create table batch (
  batch_id serial primary key,
  recipe_header_id integer,
  user_id integer,
  batch_date timestamp,
  package_date timestamp,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists current_stock;

create table current_stock (
  current_stock_id serial primary key,
  batch_id integer,
  unit_count integer,
  user_id integer,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists event;

create table event (
  event_id serial primary key,
  owner_user_id integer,
  event_name varchar(255),
  event_location varchar(255),
  event_date timestamp,
  created_at timestamp,
  updated_at timestamp
);

drop table if exists event_scheduled_goods;

create table event_scheduled_goods (
  event_scheduled_goods_id serial primary key,
  event_id integer,
  current_stock_id integer,
  recipe_header_id integer,
  units_planned integer,
  created_at timestamp,
  updated_at timestamp
);