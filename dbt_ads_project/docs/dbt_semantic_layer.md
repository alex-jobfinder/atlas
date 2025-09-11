# Intro to the dbt Semantic Layer

Flying cars, hoverboards, and true self-service analytics: this is the future we were promised. The first two might still be a few years out, but real self-service analytics is here today. With dbt's Semantic Layer, you can resolve the tension between accuracy and flexibility that has hampered analytics tools for years, empowering everybody in your organization to explore a shared reality of metrics. Best of all for analytics engineers, building with these new tools will significantly DRY up and simplify your codebase. As you'll see, the deep interaction between your dbt models and the Semantic Layer make your dbt project the ideal place to craft your metrics.
Learning goals

    ❓ Understand the purpose and capabilities of the Semantic Layer, particularly MetricFlow as the engine that powers it.
    🧱 Familiarity with the core components of MetricFlow — semantic models and metrics — and how they work together.
    🔁 Know how to refactor dbt models for the Semantic Layer.
    🏅 Aware of best practices to take maximum advantage of the Semantic Layer.

Guide structure overview

    Getting setup in your dbt project.
    Building a semantic model and its fundamental parts: entities, dimensions, and measures.
    Building a metric.
    Defining advanced metrics: ratio and derived types.
    File and folder structure: establishing a system for naming things.
    Refactoring marts and roll-ups for the Semantic Layer.
    Review best practices.

If you're ready to ship your users more power and flexibility with less code, let's dive in!

# Set up the dbt Semantic Layer
Getting started

There are two options for developing a dbt project, including the Semantic Layer:

    Cloud CLI — MetricFlow commands are embedded in the Cloud CLI under the dbt sl subcommand. This is the easiest, most full-featured way to develop Semantic Layer code for the time being. You can use the editor of your choice and run commands from the terminal.

    Studio IDE — You can create semantic models and metrics in the Studio IDE.

Basic commands

    🔍 A less common command that will come in handy with the Semantic Layer is dbt parse. This will parse your project and generate a semantic manifest, a representation of meaningful connections described by your project. This is uploaded to dbt, and used for running dbt sl commands in development. This file gives MetricFlow a state of the world from which to generate queries.
    🧰 dbt sl query is your other best friend, it will execute a query against your semantic layer and return a sample of the results. This is great for testing your semantic models and metrics as you build them. For example, if you're building a revenue model you can run dbt sl query --metrics revenue --group-by metric_time__month to validate that monthly revenue is calculating correctly.
    📝 Lastly, dbt sl list dimensions --metrics [metric name] will list all the dimensions available for a given metric. This is useful for checking that you're increasing dimensionality as you progress. You can dbt sl list other aspects of your Semantic Layer as well, run dbt sl list --help for the full list of options.

For more information on the available commands, refer to the MetricFlow commands reference, or use dbt sl --help and dbt sl [subcommand] --help on the command line. If you need to set up a dbt project first, check out the quickstart guides.
Onward!
Throughout the rest of the guide, we'll show example code based on the Jaffle Shop project, a fictional chain of restaurants. You can check out the code yourself and try things out in the Jaffle Shop repository. So if you see us calculating metrics like food_revenue later in this guide, this is why!

# Building semantic models
How to build a semantic model

A semantic model is the Semantic Layer equivalent to a logical layer model (what historically has just been called a 'model' in dbt land). Just as configurations for models are defined on the models: YAML key, configurations for semantic models are housed under semantic models:. A key difference is that while a logical model consists of configuration and SQL or Python code, a semantic model is defined purely via YAML. Rather than encoding a specific dataset, a semantic model describes relationships and expressions that let your end users select and refine their own datasets dynamically and reliably.

    ⚙️ Semantic models are comprised of three components:
        🫂 entities: these describe the relationships between various semantic models (think ids)
        🔪 dimensions: these are the columns you want to slice, dice, group, and filter by (think timestamps, categories, booleans).
        📏 measures: these are the quantitative values you want to aggregate
    🪣 We define columns as being an entity, dimension, or measure. Columns will typically fit into one of these 3 buckets, or if they're a complex aggregation expression, they might constitute a metric.

Defining orders

Let's zoom in on how we might define an orders semantic model.

    📗 We define it as a YAML dictionary in the semantic_models list.
    📑 It will have a name, entities list, dimensions list, and measures list.
    ⏬ We recommend defining them in this order consistently as a style best practice.

models/marts/orders.yml

semantic_models:
  - name: orders
    entities: ... # we'll define these later
    dimensions: ... # we'll define these later
    measures: ... # we'll define these later

    Next we'll point to the corresponding logical model by supplying a ref in the model: property, and a description for documentation.

models/marts/orders.yml

semantic_models:
  - name: orders
    description: |
      Model containing order data. The grain of the table is the order id.
    model: ref('stg_orders')
    entities: ...
    dimensions: ...
    measures: ...

Establishing our entities

    🫂 Entities are the objects and concepts in our data that have dimensions and measures. You can think of them as the nouns of our project, the spines of our queries that we may want to aggregate by, or simply the join keys.
    🔀 Entities help MetricFlow understand how various semantic models relate to one another.
    ⛓️ Unlike many other semantic layers, in MetricFlow we do not need to describe joins explicitly, instead the relationships are implicitly described by entities.
    1️⃣ Each semantic model should have one primary entity defined for itself, and any number of foreign entities for other semantic models it may join to.
    🫂 Entities require a name and type
        🔑 Types available are primary, foreign, unique or natural — we'll be focused on the first two for now, but you can read more about unique and natural keys.

Entities in action

If we look at an example staging model for orders, we see that it has 3 id columns, so we'll need three entities.
models/staging/stg_orders.sql

renamed as (

    select

        ----------  ids
        id as order_id,
        store_id as location_id,
        customer as customer_id,

        ---------- properties
        (order_total / 100.0) as order_total,
        (tax_paid / 100.0) as tax_paid,

        ---------- timestamps
        ordered_at

    from source

    👉 We add them with a name, type, and optional expr (expression). The expression can be any valid SQL expression on your platform.
    📛 If you don't add an expression, MetricFlow will assume the name is equal to the column name in the underlying logical model.
    👍 Our best practices pattern is to, whenever possible, provide a name that is the singular form of the subject or grain of the table, and use expr to specify the precise column name (with _id etc). This will let us write more readable metrics on top of these semantic models. For example, we'll use location instead of location_id.

models/marts/orders.yml

semantic_models:
  - name: orders
    ...
    entities:
      # we use the column for the name here because order is a reserved word in SQL
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id

    dimensions:
      ...
    measures:
      ...

Defining our dimensions

    🧮 Dimensions are the columns that we want to filter and group by, the adjectives of our project. They come in three types:
        categorical
        time
        slowly changing dimensions — these are covered in the documentation, and a little more complex. To focus on building your mental models of MetricFlow's fundamentals, we won't be using SCDs in this guide.
    ➕ We're not limited to existing columns, we can use the expr property to add simple computations in our dimensions.
    📛 Categorical dimensions are the simplest, they simply require a name and type (type being categorical). If the name property matches the name of the dimension column, that's it, you're done. If you want or need to use a name other than the column name, or do some filtering or computation, you can supply an optional expr property to evaluate for the dimension.

Dimensions in action

    👀 Let's look at our staging model again and see what fields we have available.

models/staging/stg_orders.sql

select

    ----------  ids -> entities
    id as order_id,
    store_id as location_id,
    customer as customer_id,

    ---------- numerics -> measures
    (order_total / 100.0) as order_total,
    (tax_paid / 100.0) as tax_paid,

    ---------- timestamps -> dimensions
    ordered_at

from source

    ⏰ For now the only dimension to add is a time dimension: ordered_at.
    🕰️ At least one primary time dimension is required for any semantic models that have measures.
    1️⃣ We denote this with the is_primary property, or if there is only a one-time dimension supplied it is primary by default. Below we only have ordered_at as a timestamp so we don't need to specify anything except the minimum granularity we're bucketing to (in this case, day). By this we mean that we're not going to be looking at orders at a finer granularity than a day.

models/marts/orders.yml

dimensions:
  - name: ordered_at
    expr: date_trunc('day', ordered_at)
    type: time
    type_params:
      time_granularity: day

tip

Dimensional models. You may have some models that do not contain measures, just dimensional data that enriches other facts. That's totally fine, a semantic model does not require dimensions or measures, it just needs a primary entity, and if you do have measures, a primary time dimension.

We'll discuss an alternate situation, dimensional tables that have static numeric values like supply costs or tax rates but no time dimensions, later in the Guide.

    🔢 We can also make a dimension out of a numeric column that would typically be a measure.
    🪣 Using expr we can create buckets of values that we label for our dimension. We'll add one of these in for labeling 'large orders' as any order totals over $50.

models/marts/orders.yml

dimensions:
  - name: ordered_at
    expr: date_trunc('day', ordered_at)
    type: time
    type_params:
      time_granularity: day
  - name: is_large_order
    type: categorical
    expr: case when order_total > 50 then true else false end

Making our measures

    📏 Measures are the final component of a semantic model. They describe the numeric values that we want to aggregate.
    🧱 Measures form the building blocks of metrics, with entities and dimensions helping us combine, group, and filter those metrics correctly.
    🏃 You can think of them as something like the verbs of a semantic model.

Measures in action

    👀 Let's look at our staging model one last time and see what fields we want to measure.

models/staging/stg_orders.sql

select

    ----------  ids -> entities
    id as order_id,
    store_id as location_id,
    customer as customer_id,

    ---------- numerics -> measures
    (order_total / 100.0) as order_total,
    (tax_paid / 100.0) as tax_paid,

    ---------- timestamps -> dimensions
    ordered_at

from source

    ➕ Here order_total and tax paid are the columns we want as measures.
    📝 We can describe them via the code below, specifying a name, description, aggregation, and expression.
    👍 As before MetricFlow will default to the name being the name of a column when no expression is supplied.
    🧮 Many different aggregations are available to us. Here we just want sums.

models/marts/orders.yml

measures:
  - name: order_total
    description: The total amount for each order including taxes.
    agg: sum
  - name: tax_paid
    description: The total tax paid on each order.
    agg: sum

    🆕 We can also create new measures using expressions, for instance adding a count of individual orders as below.

models/marts/orders.yml

- name: order_count
  description: The count of individual orders.
  expr: 1
  agg: sum

Reviewing our work

Our completed code will look like this, our first semantic model! Here are two examples showing different organizational approaches:
 Co-located approach
models/marts/orders.yml

semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: ordered_at
    description: |
      Order fact table. This table is at the order grain with one row per order.

    model: ref('stg_orders')

    entities:
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id

    dimensions:
      - name: ordered_at
        expr: date_trunc('day', ordered_at)
        # use date_trunc(ordered_at, DAY) if using BigQuery
        type: time
        type_params:
          time_granularity: day
      - name: is_large_order
        type: categorical
        expr: case when order_total > 50 then true else false end

    measures:
      - name: order_total
        description: The total revenue for each order.
        agg: sum
      - name: order_count
        description: The count of individual orders.
        expr: 1
        agg: sum
      - name: tax_paid
        description: The total tax paid on each order.
        agg: sum

models/marts/orders.yml

semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: ordered_at
    description: |
      Order fact table. This table is at the order grain with one row per order.

    model: ref('stg_orders')

    entities:
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id

    dimensions:
      - name: ordered_at
        expr: date_trunc('day', ordered_at)
        # use date_trunc(ordered_at, DAY) if using BigQuery
        type: time
        type_params:
          time_granularity: day
      - name: is_large_order
        type: categorical
        expr: case when order_total > 50 then true else false end

    measures:
      - name: order_total
        description: The total revenue for each order.
        agg: sum
      - name: order_count
        description: The count of individual orders.
        expr: 1
        agg: sum
      - name: tax_paid
        description: The total tax paid on each order.
        agg: sum

 Parallel sub-folder approach
models/semantic_models/sem_orders.yml

semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: ordered_at
    description: |
      Order fact table. This table is at the order grain with one row per order.

    model: ref('stg_orders')

    entities:
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id

    dimensions:
      - name: ordered_at
        expr: date_trunc('day', ordered_at)
        # use date_trunc(ordered_at, DAY) if using BigQuery
        type: time
        type_params:
          time_granularity: day
      - name: is_large_order
        type: categorical
        expr: case when order_total > 50 then true else false end

    measures:
      - name: order_total
        description: The total revenue for each order.
        agg: sum
      - name: order_count
        description: The count of individual orders.
        expr: 1
        agg: sum
      - name: tax_paid
        description: The total tax paid on each order.
        agg: sum

models/semantic_models/sem_orders.yml

semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: ordered_at
    description: |
      Order fact table. This table is at the order grain with one row per order.

    model: ref('stg_orders')

    entities:
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id

    dimensions:
      - name: ordered_at
        expr: date_trunc('day', ordered_at)
        # use date_trunc(ordered_at, DAY) if using BigQuery
        type: time
        type_params:
          time_granularity: day
      - name: is_large_order
        type: categorical
        expr: case when order_total > 50 then true else false end

    measures:
      - name: order_total
        description: The total revenue for each order.
        agg: sum
      - name: order_count
        description: The count of individual orders.
        expr: 1
        agg: sum
      - name: tax_paid
        description: The total tax paid on each order.
        agg: sum

As you can see, the content of the semantic model is identical in both approaches. The key differences are:

    File location
        Co-located approach: models/marts/orders.yml
        Parallel sub-folder approach: models/semantic_models/sem_orders.yml

    File naming
        Co-located approach: Uses the same name as the corresponding mart (orders.yml)
        Parallel sub-folder approach: Prefixes the file with sem_ (sem_orders.yml)

Choose the approach that best fits your project structure and team preferences. The co-located approach is often simpler for new projects, while the parallel sub-folder approach can be clearer for migrating large existing projects to the Semantic Layer.
Next steps

Let's review the basics of semantic models:

    🧱 Consist of entities, dimensions, and measures.
    🫂 Describe the semantics and relationships of objects in the warehouse.
    1️⃣ Correspond to a single logical model in your dbt project.

Next up, let's use our new semantic model to build a metric!



# Building metrics
How to build metrics

    💹 We'll start with one of the most important metrics for any business: revenue.
    📖 For now, our metric for revenue will be defined as the sum of order totals excluding tax.

Defining revenue

    🔢 Metrics have four basic properties:
        name: We'll use 'revenue' to reference this metric.
        description: For documentation.
        label: The display name for the metric in downstream tools.
        type: one of simple, ratio, or derived.
    🎛️ Each type has different type_params.
    🛠️ We'll build a simple metric first to get the hang of it, and move on to ratio and derived metrics later.
    📏 Simple metrics are built on a single measure defined as a type parameter.
    🔜 Defining measures as their own distinct component on semantic models is critical to allowing the flexibility of more advanced metrics, though simple metrics act mainly as pass-through that provide filtering and labeling options.

models/marts/orders.yml

metrics:
  - name: revenue
    description: Sum of the order total.
    label: Revenue
    type: simple
    type_params:
      measure: order_total

Query your metric

You can use the Cloud CLI for metric validation or queries during development, via the dbt sl set of subcommands. Here are some useful examples:

dbt sl query revenue --group-by metric_time__month
dbt sl list dimensions --metrics revenue # list all dimensions available for the revenue metric

    It's best practice any time we're updating our Semantic Layer code to run dbt parse to update our development semantic manifest.
    dbt sl query is not how you would typically use the tool in production, that's handled by the dbt Semantic Layer's features. It's available for testing results of various metric queries in development, exactly as we're using it now.
    Note the structure of the above query. We select the metric(s) we want and the dimensions to group them by — we use dunders (double underscores e.g.metric_time__[time bucket]) to designate time dimensions or other non-unique dimensions that need a specified entity path to resolve (e.g. if you have an orders location dimension and an employee location dimension both named 'location' you would need dunders to specify orders__location or employee__location).



# More advanced metrics
More advanced metric types

We're not limited to just passing measures through to our metrics, we can also combine measures to model more advanced metrics.

    🍊 Ratio metrics are, as the name implies, about comparing two metrics as a numerator and a denominator to form a new metric, for instance the percentage of order items that are food items instead of drinks.
    🧱 Derived metrics are when we want to write an expression that calculates a metric using multiple metrics. A classic example here is our gross profit calculated by subtracting costs from revenue.
    ➕ Cumulative metrics calculate all of a measure over a given window, such as the past week, or if no window is supplied, the all-time total of that measure.

Ratio metrics

    🔢 We need to establish one measure that will be our numerator, and one that will be our denominator.
    🥪 Let's calculate the percentage of our Jaffle Shop revenue that comes from food items.
    💰 We already have our denominator, revenue, but we'll want to make a new metric for our numerator called food_revenue.

models/marts/orders.yml

- name: food_revenue
  description: The revenue from food in each order.
  label: Food Revenue
  type: simple
  type_params:
    measure: food_revenue

    📝 Now we can set up our ratio metric.

models/marts/orders.yml

- name: food_revenue_pct
  description: The % of order revenue from food.
  label: Food Revenue %
  type: ratio
  type_params:
    numerator: food_revenue
    denominator: revenue

Derived metrics

    🆙 Now let's really have some fun. One of the most important metrics for any business is not just revenue, but revenue growth. Let's use a derived metric to build month-over-month revenue.
    ⚙️ A derived metric has a couple key components:
        📚 A list of metrics to build on. These can be manipulated and filtered in various way, here we'll use the offset_window property to lag by a month.
        🧮 An expression that performs a calculation with these metrics.
    With these parts we can assemble complex logic that would otherwise need to be 'frozen' in logical models.

models/marts/orders.yml

- name: revenue_growth_mom
  description: "Percentage growth of revenue compared to 1 month ago. Excluded tax"
  type: derived
  label: Revenue Growth % M/M
  type_params:
    expr: (current_revenue - revenue_prev_month) * 100 / revenue_prev_month
    metrics:
      - name: revenue
        alias: current_revenue
      - name: revenue
        offset_window: 1 month
        alias: revenue_prev_month

Cumulative metrics

    ➕ Lastly, lets build a cumulative metric. In keeping with our theme of business priorities, let's continue with revenue and build an all-time revenue metric for any given time window.
    🪟 All we need to do is indicate the type is cumulative and not supply a window in the type_params, which indicates we want cumulative for the entire time period our end users select.

models/marts/orders.yml

- name: cumulative_revenue
  description: The cumulative revenue for all orders.
  label: Cumulative Revenue (All Time)
  type: cumulative
  type_params:
    measure: revenue

# Tactical terminology

The rest of this guide will focus on the process of migrating your existing dbt code to the Semantic Layer. To do this, we'll need to introduce some new terminology and concepts that are specific to the Semantic Layer.

We want to define them up front, as we have specific meanings in mind applicable to the process of migrating code to the Semantic Layer. These terms can mean different things in different settings, but here we mean:

    🔲 Normalized — can be defined with varying degrees of technical rigor, but used here we mean something that contains unique data stored only once in one place, so it can be efficiently joined and aggregated into various shapes. You can think of it referring to tables that function as conceptual building blocks in your business, not in the sense of say, strict Codd 3NF.
    🛒 Mart — also has a variety of definitions, but here we mean a table that is relatively normalized and functions as the source of truth for a core concept in your business.
    🕸️ Denormalized — when we store the same data in multiple places for easier access without joins. The most denormalized data modeling system is OBT (One Big Table), where we try to get every possible interesting column related to a concept (for instance, customers) into one big table so all an analyst needs to do is select.
    🗞️ Rollup — used here as a catchall term meaning both denormalized tables built on top of normalized marts and those that perform aggregations to a certain grain. For example active_accounts_per_week might aggregate customers and orders data to a weekly time. Another example would be customer_metrics which might denormalize a lot of the data from customers as well as aggregated data from orders. For the sake of brevity in this guide, we’ll call all these types of products built on top of your normalized concepts as rollups.

We'll also use a couple new terms for the sake of brevity. These aren't standard or official dbt-isms, but useful for communicating meaning in the context of refactoring code for the Semantic Layer:

    🧊 Frozen — shorthand to indicate code that is statically built in dbt’s logical transformation layer. Does not refer to the materialization type: views, incremental models, and regular tables are all considered frozen as they statically generate data or code that is stored in the warehouse as opposed to dynamically querying, as with the Semantic Layer. This is not a bad thing! We want some portion of our transformation logic to be frozen and stable as the transformation logic is not rapidly shifting and we benefit in testing, performance, and stability.
    🫠 Melting — the process of breaking up frozen structures into flexible Semantic Layer code. This allows them to create as many combinations and aggregations as possible dynamically in response to stakeholder needs and queries.

tip

🏎️ The Semantic Layer is a denormalization engine. dbt transforms your data into clean, normalized marts. The Semantic Layer is a denormalization engine that dynamically connects and molds these building blocks into the maximum amount of shapes available dynamically.

# Semantic structure
Files and Folders

The first thing you need to establish is how you’re going to consistently structure your code. There are two recommend best practices to choose from:

    🏡 Co-locate your semantic layer code in a one-YAML-file-per-marts-model system.
        Puts documentation, data tests, unit tests, semantic models, and metrics into a unified file that corresponds to a dbt-modeled mart.
        Trades larger file size for less clicking between files.
        Simpler for greenfield projects that are building the Semantic Layer alongside dbt models.
    🏘️Create a sub-folder called models/semantic_models/.
        Create a parallel file and folder structure within that specifically for semantic layer code.
        Gives you more targeted files, but may involves switching between files more often.
        Better for migrating large existing projects, as you can quickly see what marts have been codified into the Semantic Layer.

It’s not terribly difficult to shift between these (it can be done with some relatively straightforward shell scripting), and this is purely a decision based on your developers’ preference (i.e. it has no impact on execution or performance), so don’t feel locked in to either path. Just pick the one that feels right and you can always shift down the road if you change your mind.
tip

Make sure to save all semantic models and metrics under the directory defined in the model-paths (or a subdirectory of it, like models/semantic_models/). If you save them outside of this path, it will result in an empty semantic_manifest.json file, and your semantic models or metrics won't be recognized.
Naming

Next, establish your system for consistent file naming:

    1️⃣ If you’re doing one-YAML-file-per-mart then you’d have an orders.sql and an orders.yml.
    📛 If you’re using a parallel subfolder approach, for the sake of unique file names it’s recommended to use the prefix sem_ e.g. sem_orders.yml for the dedicated semantic model and metrics that build on orders.sql and orders.yml.

Can't decide?
Start with a dedicated subfolder for your semantic models and metrics, and then if you find that you’re spending a lot of time clicking between files, you can always shift to a one-YAML-file-per-mart system. Our internal data team has found that the dedicated subfolder approach is more manageable for migrating existing projects, and this is the approach our documentation uses, so if you can't pick go with that.


# Refactor an existing rollup
A new approach

Now that we've set the stage, it's time to dig in to the fun and messy part: how do we refactor an existing rollup in dbt into semantic models and metrics?

Let's look at the differences we can observe in how we might approach this with MetricFlow supercharging dbt versus how we work without a Semantic Layer. These differences can then inform our structure.

    🍊 In dbt, we tend to create highly denormalized datasets that bring everything you want around a certain entity or process into a single table.
    💜 The problem is, this limits the dimensionality available to MetricFlow. The more we pre-compute and 'freeze' into place, the less flexible our data is.
    🚰 In MetricFlow, we ideally want highly normalized, star schema-like data that then allows MetricFlow to shine as a denormalization engine.
    ∞ Another way to think about this is that instead of moving down a list of requested priorities trying to pre-make as many combinations of our marts as possible — increasing lines of code and complexity — we can let MetricFlow present every combination possible without specifically coding it.
    🏗️ To resolve these approaches optimally, we'll need to shift some fundamental aspects of our modeling strategy.

Refactor steps outlined

We recommend an incremental implementation process that looks something like this:

    👉 Identify an important output (a revenue chart on a dashboard for example, and the mart model(s) that supplies this output.
    🔍 Examine all the entities that are components of this rollup (for instance, an active_customers_per_week rollup may include customers, shipping, and product data).
    🛠️ Build semantic models for all the underlying component marts.
    📏 Build metrics for the required aggregations in the rollup.
    👯 Create a clone of the output on top of the Semantic Layer.
    💻 Audit to ensure you get accurate outputs.
    👉 Identify any other outputs that point to the rollup and move them to the Semantic Layer.
    ✌️ Put a deprecation plan in place for the now extraneous frozen rollup.

You would then continue this process on other outputs and marts moving down a list of priorities. Each model as you go along will be faster and easier as you'll reuse many of the same components that will already have been semantically modeled.
Let's make a revenue metric

So far we've been working in new pointing at a staging model to simplify things as we build new mental models for MetricFlow. In reality, unless you're implementing MetricFlow in a green-field dbt project, you probably are going to have some refactoring to do. So let's get into that in detail.

    📚 Per the above steps, let's say we've identified our target as a revenue rollup that is built on top of orders and order_items. Now we need to identify all the underlying components, these will be all the 'import' CTEs at the top of these marts. So in the Jaffle Shop project we'd need: orders, order_items, products, locations, and supplies.
    🗺️ We'll next make semantic models for all of these. Let's walk through a straightforward conversion first with locations.
    ⛓️ We'll want to first decide if we need to do any joining to get this into the shape we want for our semantic model. The biggest determinants of this are two factors:
        📏 Does this semantic model contain measures?
        🕥 Does this semantic model have a primary timestamp?
        🫂 If a semantic model has measures but no timestamp (for example, supplies in the example project, which has static costs of supplies), you'll likely want to sacrifice some normalization and join it on to another model that has a primary timestamp to allow for metric aggregation.
    🔄 If we don't need any joins, we'll just go straight to the staging model for our semantic model's ref. Locations does have a tax_rate measure, but it also has an ordered_at timestamp, so we can go straight to the staging model here.
    🥇 We specify our primary entity (based on location_id), dimensions (one categorical, location_name, and one primary time dimension opened_at), and lastly our measures, in this case just average_tax_rate.

models/marts/locations.yml

semantic_models:
  - name: locations
    description: |
      Location dimension table. The grain of the table is one row per location.
    model: ref('stg_locations')
    entities:
      - name: location
        type: primary
        expr: location_id
    dimensions:
      - name: location_name
        type: categorical
      - name: date_trunc('day', opened_at)
        type: time
        type_params:
          time_granularity: day
    measures:
      - name: average_tax_rate
        description: Average tax rate.
        expr: tax_rate
        agg: avg

Semantic and logical interaction

Now, let's tackle a thornier situation. Products and supplies both have dimensions and measures but no time dimension. Products has a one-to-one relationship with order_items, enriching that table, which is itself just a mapping table of products to orders. Additionally, products have a one-to-many relationship with supplies. The high-level ERD looks like the diagram below.

So to calculate, for instance, the cost of ingredients and supplies for a given order, we'll need to do some joining and aggregating, but again we lack a time dimension for products and supplies. This is the signal to us that we'll need to build a logical mart and point our semantic model at that.
tip

dbt 🧡 MetricFlow. This is where integrating your semantic definitions into your dbt project really starts to pay dividends. The interaction between the logical and semantic layers is so dynamic, you either need to house them in one codebase or facilitate a lot of cross-project communication and dependency.

    🎯 Let's aim at, to start, building a table at the order_items grain. We can aggregate supply costs up, map over the fields we want from products, such as price, and bring the ordered_at timestamp we need over from the orders table. You can see example code, copied below, in models/marts/order_items.sql.

models/marts/order_items.sql

{{
   config(
      materialized = 'table',
   )
}}

with

order_items as (

   select * from {{ ref('stg_order_items') }}

),

orders as (

   select * from {{ ref('stg_orders')}}

),

products as (

   select * from {{ ref('stg_products') }}

),

supplies as (

   select * from {{ ref('stg_supplies') }}

),

order_supplies_summary as (

   select
      product_id,
      sum(supply_cost) as supply_cost

   from supplies

   group by 1
),

joined as (

   select
      order_items.*,
      products.product_price,
      order_supplies_summary.supply_cost,
      products.is_food_item,
      products.is_drink_item,
      orders.ordered_at

   from order_items

   left join orders on order_items.order_id  = orders.order_id

   left join products on order_items.product_id = products.product_id

   left join order_supplies_summary on order_items.product_id = order_supplies_summary.product_id

)

select * from joined

    🏗️ Now we've got a table that looks more like what we want to feed into the Semantic Layer. Next, we'll build a semantic model on top of this new mart in models/marts/order_items.yml. Again, we'll identify our entities, then dimensions, then measures.

models/marts/order_items.yml

semantic_models:
   #The name of the semantic model.
   - name: order_items
      defaults:
         agg_time_dimension: ordered_at
      description: |
         Items contatined in each order. The grain of the table is one row per order item.
      model: ref('order_items')
      entities:
         - name: order_item
           type: primary
           expr: order_item_id
         - name: order_id
           type: foreign
           expr: order_id
         - name: product
           type: foreign
           expr: product_id
      dimensions:
         - name: ordered_at
           expr: date_trunc('day', ordered_at)
           type: time
           type_params:
             time_granularity: day
         - name: is_food_item
           type: categorical
         - name: is_drink_item
           type: categorical
      measures:
         - name: revenue
           description: The revenue generated for each order item. Revenue is calculated as a sum of revenue associated with each product in an order.
           agg: sum
           expr: product_price
         - name: food_revenue
           description: The revenue generated for each order item. Revenue is calculated as a sum of revenue associated with each product in an order.
           agg: sum
           expr: case when is_food_item = 1 then product_price else 0 end
         - name: drink_revenue
           description: The revenue generated for each order item. Revenue is calculated as a sum of revenue associated with each product in an order.
           agg: sum
           expr: case when is_drink_item = 1 then product_price else 0 end
         - name: median_revenue
           description: The median revenue generated for each order item.
           agg: median
           expr: product_price

    📏 Finally, Let's build a simple revenue metric on top of our semantic model now.

models/marts/order_items.yml

metrics:
  - name: revenue
    description: Sum of the product revenue for each order item. Excludes tax.
    type: simple
    label: Revenue
    type_params:
      measure: revenue

Checking our work

    🔍 We always start our auditing with a dbt parse to ensure our code works before we examine its output.
    👯 If we're working there, we'll move to trying out an dbt sl query that replicates the logic of the output we're trying to refactor.
    💸 For our example we want to audit monthly revenue, to do that we'd run the query below.

Example query

dbt sl query --metrics revenue --group-by metric_time__month

Example query results

✔ Success 🦄 - query completed after 1.02 seconds
| METRIC_TIME__MONTH   |   REVENUE |
|:---------------------|----------:|
| 2016-09-01 00:00:00  |  17032.00 |
| 2016-10-01 00:00:00  |  20684.00 |
| 2016-11-01 00:00:00  |  26338.00 |
| 2016-12-01 00:00:00  |  10685.00 |

    Try introducing some other dimensions from the semantic models into the group-by arguments to get a feel for this command.


# Best practices
Putting it all together

    📊 We've walked through creating semantic models and metrics for basic coverage of a key business area.
    🔁 In doing so we've looked at how to refactor a frozen rollup into a dynamic, flexible new life in the Semantic Layer.

Best practices

    ✅ Prefer normalization when possible to allow MetricFlow to denormalize dynamically for end users.
    ✅ Use marts to denormalize when needed, for instance grouping tables together into richer components, or getting measures on dimensional tables attached to a table with a time spine.
    ✅ When source data is well normalized you can build semantic models on top of staging models.
    ✅ Prefer computing values in measures and metrics when possible as opposed to in frozen rollups.
    ❌ Don't directly refactor the code you have in production, build in parallel so you can audit the Semantic Layer output and deprecate old marts gracefully.

Key commands

    🔑 Use dbt parse to generate a fresh semantic manifest.
    🔑 Use dbt sl list dimensions --metrics [metric name] to check that you're increasing dimensionality as you progress.
    🔑 Use dbt sl query [query options] to preview the output from your metrics as you develop.

Next steps

    🗺️ Use these best practices to map out your team's plan to incrementally adopt the Semantic Layer.
    🤗 Get involved in the community and ask questions, help craft best practices, and share your progress in building a Semantic Layer.
    Validate semantic nodes in CI to ensure code changes made to dbt models don't break these metrics.

The Semantic Layer is the biggest paradigm shift thus far in the young practice of analytics engineering. It's ready to provide value right away, but is most impactful if you move your project towards increasing normalization, and allow MetricFlow to do the denormalization for you with maximum dimensionality.

We will be releasing more resources soon covering implementation of the Semantic Layer in dbt with various integrated BI tools. This is just the beginning, hopefully this guide has given you a path forward for building your data platform in this new era. Refer to Semantic Layer FAQs for more information.