import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px ## Plotly helps us create interactive charts



# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Cart2Insights",
    page_icon="🛒",
    layout="wide"
)

# Main title
st.title("🛒 Cart2Insights")

# Subtitle
st.subheader("Decoding E-Commerce Performance")

# Divider line
st.divider='rainbow'


# --------------------------------------------------
# MYSQL PASSWORD
# --------------------------------------------------

mysql_password = st.sidebar.text_input(
    "Enter MySQL Password",
    type="password"
)

if not mysql_password:
    st.info("Please enter your MySQL password in the sidebar.")
    st.stop()


# --------------------------------------------------
# MYSQL CONNECTION
# --------------------------------------------------

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="Cart2insight_db"
)

st.sidebar.success("MySQL Connected")


# --------------------------------------------------
# DASHBOARD MENU
# --------------------------------------------------

menu = st.sidebar.radio(
    "Dashboard Menu",
    [
        "Business Overview",
        "Sales Analysis",
        "Customer Analysis",
        "Seller & Product Analysis",
        "Delivery Analysis",
        "Customer Experience"
    ]
)

# ==================================================
# 1. BUSINESS OVERVIEW
# ==================================================

if menu == "Business Overview":

    st.header("🏠 Business Overview")

    cursor = conn.cursor()

    query = """
    SELECT
        (SELECT ROUND(SUM(payment_value), 2)
         FROM payments) AS total_revenue,

        (SELECT COUNT(*)
         FROM orders) AS total_orders,

        (SELECT COUNT(DISTINCT customer_unique_id)
         FROM customers) AS total_customers,

        (SELECT COUNT(*)
         FROM sellers) AS total_sellers,

        (SELECT ROUND(
            SUM(payment_value) /
            COUNT(DISTINCT order_id), 2
         )
         FROM payments) AS average_order_value,

        (SELECT ROUND(AVG(review_score), 2)
         FROM reviews) AS average_review_score;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        f"{result[0]:,.2f}"
    )

    col2.metric(
        "Total Orders",
        f"{result[1]:,}"
    )

    col3.metric(
        "Total Customers",
        f"{result[2]:,}"
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Total Sellers",
        f"{result[3]:,}"
    )

    col5.metric(
        "Average Order Value",
        f"{result[4]:,.2f}"
    )

    col6.metric(
        "Average Review Score",
        result[5]
    )

# ==================================================
# 2. SALES ANALYSIS
# ==================================================
elif menu == "Sales Analysis":

    st.header("📈 Sales Analysis")

    cursor = conn.cursor()


    # ----------------------------------------------
    # 1. MONTHLY REVENUE TREND
    # ----------------------------------------------

    st.subheader("1. Monthly Revenue Trend")

    monthly_query = """
    SELECT
        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%Y-%m'
        ) AS month,

        SUM(p.payment_value) AS revenue

    FROM orders o

    JOIN payments p
        ON o.order_id = p.order_id

    GROUP BY month

    ORDER BY month;
    """

    cursor.execute(monthly_query)

    monthly_data = cursor.fetchall()

    monthly_df = pd.DataFrame(
        monthly_data,
        columns=["Month", "Revenue"]
    )

    monthly_df["Revenue"] = (
        monthly_df["Revenue"].astype(float)
    )

    st.line_chart(
        monthly_df,
        x="Month",
        y="Revenue"
    )

    # ----------------------------------------------
    # 2. REVENUE BY CATEGORY
    # ----------------------------------------------
    st.subheader("2. Revenue by Category")

    category_query = """
    SELECT
        COALESCE(
            c.product_category_name_english,
            p.product_category_name,
            'unknown'
        ) AS category,

        ROUND(
            SUM(oi.price),
            2
        ) AS revenue

    FROM order_items oi

    JOIN products p
        ON oi.product_id = p.product_id

    LEFT JOIN category_translation c
        ON p.product_category_name =
           c.product_category_name

    GROUP BY category

    ORDER BY revenue DESC

    LIMIT 10;
    """

    cursor.execute(category_query)

    category_data = cursor.fetchall()

    category_df = pd.DataFrame(
        category_data,
        columns=[
            "Category",
            "Revenue"
        ]
    )

    category_df["Revenue"] = (
        category_df["Revenue"].astype(float)
    )

    st.bar_chart(
        category_df,
        x="Category",
        y="Revenue"
    )

    # ----------------------------------------------
    # Create an interactive bar chart
    # ----------------------------------------------
    category_chart = px.bar(
       category_df,
       x="Category",
       y="Revenue",
       title="Top 10 Categories by Revenue"
    )

   # Show the chart inside Streamlit
    st.plotly_chart(
       category_chart,
       use_container_width=True
    )

    # ----------------------------------------------
    # 3. TOP-SELLING PRODUCTS
    # ----------------------------------------------
    st.subheader("3. Top-Selling Products")

    top_products_query = """
    SELECT
        product_id,
        COUNT(*) AS units_sold

    FROM order_items

    GROUP BY product_id

    ORDER BY units_sold DESC

    LIMIT 10;
    """

    cursor.execute(top_products_query)

    top_products_data = cursor.fetchall()

    top_products_df = pd.DataFrame(
        top_products_data,
        columns=[
            "Product ID",
            "Units Sold"
        ]
    )

    st.bar_chart(
        top_products_df,
        x="Product ID",
        y="Units Sold"
    )

    # --------------------------------------------------
    # 4. SALES BY LOCATION
    # --------------------------------------------------
    st.subheader("4. Sales by Location")


    # 1. SQL query
    location_query = """
    SELECT
      c.customer_state AS state,
      ROUND(SUM(p.payment_value), 2) AS revenue

    FROM customers c

    JOIN orders o
        ON c.customer_id = o.customer_id

    JOIN payments p
        ON o.order_id = p.order_id

    GROUP BY c.customer_state

    ORDER BY revenue DESC

    LIMIT 10;
    """

    # 2. Run the SQL query
    cursor.execute(location_query)

    # 3. Get the SQL result
    location_data = cursor.fetchall()

    # 4. Convert the result into a Pandas DataFrame
    location_df = pd.DataFrame(
        location_data,
        columns=["State", "Revenue"]
    )

    # 5. Convert Revenue into numbers
    location_df["Revenue"] = location_df["Revenue"].astype(float)

    # 6. Check the data
    st.write(location_df)

    # 7. Show the chart
    st.bar_chart(
       location_df,
       x="State",
       y="Revenue"
    )

# ==================================================
# 3. CUSTOMER ANALYSIS
# ==================================================
if menu == "Customer Analysis":

    st.header("👥 Customer Analysis")

    # Create cursor to communicate with MySQL
    cursor = conn.cursor()

    # --------------------------------------------------
    # 1. CUSTOMER DISTRIBUTION
    # --------------------------------------------------
    st.subheader("1. Customer Distribution by State")

    # Count unique customers in each state
    customer_distribution_query = """
    SELECT
        customer_state AS state,
        COUNT(DISTINCT customer_unique_id) AS total_customers
    FROM customers
    GROUP BY customer_state
    ORDER BY total_customers DESC;
    """

    # Run SQL query
    cursor.execute(customer_distribution_query)

    # Bring SQL result into Python
    customer_distribution_data = cursor.fetchall()

    # Create Pandas DataFrame
    customer_distribution_df = pd.DataFrame(
        customer_distribution_data,
        columns=["State", "Total Customers"]
    )

    # Make sure customer count is numeric
    customer_distribution_df["Total Customers"] = pd.to_numeric(
        customer_distribution_df["Total Customers"]
    )

    # Create interactive chart
    customer_distribution_chart = px.bar(
        customer_distribution_df,
        x="State",
        y="Total Customers",
        title="Customer Distribution by State"
    )

    # Show chart
    st.plotly_chart(
        customer_distribution_chart,
        use_container_width=True
    )

    # --------------------------------------------------
    # 2. CUSTOMER SPENDING
    # --------------------------------------------------
    st.subheader("2.Customer Spending by State")

    # Calculate total customer spending for each state
    customer_spending_query = """
    SELECT
        c.customer_state AS state,
        ROUND(SUM(p.payment_value), 2) AS total_spending
    FROM customers c

    JOIN orders o
        ON c.customer_id = o.customer_id

    JOIN payments p
        ON o.order_id = p.order_id

    GROUP BY c.customer_state

    ORDER BY total_spending DESC;
    """

    # Run SQL query
    cursor.execute(customer_spending_query)

    # Get result
    customer_spending_data = cursor.fetchall()

    # Create DataFrame
    customer_spending_df = pd.DataFrame(
        customer_spending_data,
        columns=["State", "Total Spending"]
    )

    # Convert spending into numbers
    customer_spending_df["Total Spending"] = pd.to_numeric(
        customer_spending_df["Total Spending"]
    )

    # Create interactive chart
    customer_spending_chart = px.bar(
        customer_spending_df,
        x="State",
        y="Total Spending",
        title="Customer Spending by State"
    )

    # Show chart
    st.plotly_chart(
        customer_spending_chart,
        use_container_width=True
    )

    # --------------------------------------------------
    # 3. REPEAT VS NEW CUSTOMERS
    # --------------------------------------------------
    st.subheader("3. Repeat vs New Customers")

    # First count how many orders each unique customer placed.
    # Then classify them:
    # More than 1 order = Repeat Customer
    # Only 1 order = New Customer

    repeat_customer_query = """
    WITH customer_orders AS (
        SELECT
            c.customer_unique_id,
            COUNT(DISTINCT o.order_id) AS order_count
        FROM customers c

        JOIN orders o
            ON c.customer_id = o.customer_id

        GROUP BY c.customer_unique_id
    )

    SELECT
        CASE
            WHEN order_count > 1 THEN 'Repeat Customer'
            ELSE 'New Customer'
        END AS customer_type,

        COUNT(*) AS total_customers

    FROM customer_orders

    GROUP BY customer_type;
    """

    # Run SQL query
    cursor.execute(repeat_customer_query)

    # Get result
    repeat_customer_data = cursor.fetchall()

    # Create DataFrame
    repeat_customer_df = pd.DataFrame(
        repeat_customer_data,
        columns=["Customer Type", "Total Customers"]
    )

    # Create interactive pie chart
    repeat_customer_chart = px.pie(
        repeat_customer_df,
        names="Customer Type",
        values="Total Customers",
        title="Repeat vs New Customers"
    )

    # Show chart
    st.plotly_chart(
        repeat_customer_chart,
        use_container_width=True
    )

    # --------------------------------------------------
    # 4. TOP CUSTOMERS
    # --------------------------------------------------
    st.subheader("4. Top customerss")

    # Find customers who spent the most money
    top_customers_query = """
    SELECT
        c.customer_unique_id,
        ROUND(SUM(p.payment_value), 2) AS total_spending

    FROM customers c

    JOIN orders o
        ON c.customer_id = o.customer_id

    JOIN payments p
        ON o.order_id = p.order_id

    GROUP BY c.customer_unique_id

    ORDER BY total_spending DESC

    LIMIT 10;
    """

    # Run SQL query
    cursor.execute(top_customers_query)

    # Get result
    top_customers_data = cursor.fetchall()

    # Create DataFrame
    top_customers_df = pd.DataFrame(
        top_customers_data,
        columns=["Customer ID", "Total Spending"]
    )

    # Convert spending into numeric values
    top_customers_df["Total Spending"] = pd.to_numeric(
        top_customers_df["Total Spending"]
    )

    # Create interactive horizontal bar chart
    top_customers_chart = px.bar(
        top_customers_df,
        x="Total Spending",
        y="Customer ID",
        orientation="h",
        title="Top 10 Customers by Spending"
    )

    # Show chart
    st.plotly_chart(
        top_customers_chart,
        use_container_width=True
    )

# ==================================================
# 4. SELLER & PRODUCT ANALYSIS
# ==================================================
if menu == "Seller & Product Analysis":

    st.header("🏪 Seller & Product Analysis")

    # --------------------------------------------------
    # 1. TOP SELLERS
    # --------------------------------------------------

    st.subheader("1.Top Sellers")

    st.write(
        "Business Question: Which sellers handled the highest number of orders?"
    )

    # Ask MySQL to count unique orders for each seller
    top_sellers_query = """
    SELECT
        seller_id,
        COUNT(DISTINCT order_id) AS total_orders

    FROM order_items

    GROUP BY seller_id

    ORDER BY total_orders DESC

    LIMIT 10;
    """

    # Ru n SQL query
    cursor = conn.cursor()
    cursor.execute(top_sellers_query)

    #  Bring SQL result into Python
    top_sellers_data = cursor.fetchall()

    #  Convert result into Pandas DataFrame
    top_sellers_df = pd.DataFrame(
        top_sellers_data,
        columns=["Seller ID", "Total Orders"]
    )

    # Create an interactive chart
    top_sellers_chart = px.bar(
        top_sellers_df,
        x ="Total Orders",
        y="Seller ID",
        orientation="h",
        title="Top 10 Sellers by Number of Orders"
    )

    # Show chart
    st.plotly_chart(
        top_sellers_chart,
        use_container_width=True
    )

    # --------------------------------------------------
    # 2. SELLER REVENUE
    # --------------------------------------------------
    st.subheader("2.Seller Revenue")

     #st.write(
     # "Business Question: Which sellers generated the highest sales revenue?"
    #)

    # Calculate total product sales for each seller
    seller_revenue_query = """
    SELECT
         seller_id,
         ROUND(SUM(price), 2) AS seller_revenue
    FROM order_items
    GROUP BY seller_id
    ORDER BY seller_revenue DESC
    LIMIT 10;
    """

    # Run the SQL query
    cursor.execute(seller_revenue_query)

    # Bring the SQL result into Python
    seller_revenue_data = cursor.fetchall()

    # Convert result into a Pandas DataFrame
    seller_revenue_df = pd.DataFrame(
        seller_revenue_data,
        columns=["Seller ID", "Seller Revenue"]
    )

    # Convert revenue into numbers
    seller_revenue_df["Seller Revenue"] = pd.to_numeric(
        seller_revenue_df["Seller Revenue"]
    )

    # Create an interactive horizontal bar chart
    seller_revenue_chart = px.bar(
        seller_revenue_df,
        x="Seller Revenue",
        y="Seller ID",
        orientation="h",
        title="Top 10 Sellers by Revenue"
    )

    # Show chart in Streamlit
    st.plotly_chart(
        seller_revenue_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 3. PRODUCT / CATEGORY PERFORMANCE
    # --------------------------------------------------

    st.subheader("3.Product / Category Performance")

    st.write(
        "Business Question: Which product categories generated the highest revenue?"
    )

    # Join order items with products and category translation
    category_performance_query = """
    SELECT
        COALESCE(
            c.product_category_name_english,
            p.product_category_name,
            'unknown'
        ) AS category,

        ROUND(SUM(oi.price), 2) AS revenue

    FROM order_items oi

    JOIN products p
        ON oi.product_id = p.product_id

    LEFT JOIN category_translation c
        ON p.product_category_name = c.product_category_name

    GROUP BY category 

    ORDER BY revenue DESC

    LIMIT 10;
    """

    # Run SQL query
    cursor.execute(category_performance_query)

    # Get SQL result
    category_performance_data = cursor.fetchall()

    # Convert result into Pandas DataFrame
    category_performance_df = pd.DataFrame(
        category_performance_data,
        columns=["Category", "Revenue"]
    )

    # Make sure Revenue is numeric
    category_performance_df["Revenue"] = pd.to_numeric(
        category_performance_df["Revenue"]
    )

    # Create interactive bar chart
    category_performance_chart = px.bar(
        category_performance_df,
        x="Revenue",
        y="Category",
        orientation="h",
        title="Top 10 Product Categories by Revenue"
    )

    # Show chart
    st.plotly_chart(
        category_performance_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 4. SELLER RATINGS
    # --------------------------------------------------

    st.subheader("4.Seller Ratings")

    st.write(
        "Business Question: Which sellers have the highest average customer rating?"
    )

# First, connect each seller with the orders they handled.
# Then calculate the average review score for each seller.
# We keep sellers with at least 10 reviewed orders.
    seller_rating_query = """
    WITH seller_orders AS (
        SELECT DISTINCT
            seller_id,
            order_id
        FROM order_items
    ),

    seller_ratings AS (
        SELECT
            so.seller_id,
            ROUND(AVG(r.review_score), 2) AS average_rating,
            COUNT(DISTINCT so.order_id) AS reviewed_orders
        FROM seller_orders so

        JOIN reviews r
            ON so.order_id = r.order_id

        GROUP BY so.seller_id

        HAVING COUNT(DISTINCT so.order_id) >= 10
    ),

    ranked_sellers AS (
        SELECT
            seller_id,
            average_rating,
            reviewed_orders,
            RANK() OVER (
                ORDER BY average_rating DESC
            ) AS seller_rank
        FROM seller_ratings
    )
    SELECT
        seller_id,
        average_rating,
        reviewed_orders,
        seller_rank
    FROM ranked_sellers
    ORDER BY seller_rank
    LIMIT 10;
    """

    # Run SQL query
    cursor.execute(seller_rating_query)

    # Get the result
    seller_rating_data = cursor.fetchall()

    # Convert SQL result into Pandas DataFrame
    seller_rating_df = pd.DataFrame(
        seller_rating_data,
        columns=[
           "Seller ID",
           "Average Rating",
           "Reviewed Orders",
           "Seller Rank"
        ]
    )

    # Convert Average Rating into numeric values
    seller_rating_df["Average Rating"] = pd.to_numeric(
        seller_rating_df["Average Rating"]
    )

    # Create interactive chart
    seller_rating_chart = px.bar(
        seller_rating_df,
        x="Average Rating",
        y="Seller ID",
        orientation="h",
        title="Top 10 Sellers by Average Rating"
    )

    # Show chart
    st.plotly_chart(
        seller_rating_chart,
        use_container_width=True
    )
# ==================================================
# 5. DELIVERY ANALYSIS
# ==================================================
if menu == "Delivery Analysis":

    st.header("🚚 Delivery Analysis")

    # --------------------------------------------------
    # 1. AVERAGE DELIVERY TIME
    # --------------------------------------------------

    st.subheader("1. Average Delivery Time")

    st.write(
        "Business Question: On average, how many days does an order take to reach the customer?"
    )

    average_delivery_query = """
    SELECT
        ROUND(
            AVG(
                DATEDIFF(
                    order_delivered_customer_date,
                    order_purchase_timestamp
                )
            ),
            2
        ) AS average_delivery_days
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date >= order_purchase_timestamp;
    """

    cursor = conn.cursor()
    cursor.execute(average_delivery_query)

    average_delivery_data = cursor.fetchone()
    average_delivery_days = average_delivery_data[0]

    st.metric(
        label="Average Delivery Time",
        value=f"{average_delivery_days} Days"
    )

    # --------------------------------------------------
    # 2. ON-TIME VS DELAYED ORDERS
    # --------------------------------------------------

    st.subheader("2. On-time vs Delayed Orders")

    st.write(
        "Business Question: How many delivered orders arrived on time and how many were delayed?"
    )

    on_time_query = """
    SELECT
        CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
            THEN 'On Time'
            ELSE 'Delayed'
        END AS delivery_status,

        COUNT(*) AS total_orders

    FROM orders

    WHERE order_delivered_customer_date IS NOT NULL

    GROUP BY delivery_status;
    """

    cursor.execute(on_time_query)

    on_time_data = cursor.fetchall()

    on_time_df = pd.DataFrame(
        on_time_data,
        columns=["Delivery Status", "Total Orders"]
    )

    on_time_chart = px.pie(
        on_time_df,
        names="Delivery Status",
        values="Total Orders",
        title="On-time vs Delayed Orders"
    )

    st.plotly_chart(
        on_time_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 3. DELIVERY PERFORMANCE BY LOCATION
    # --------------------------------------------------

    st.subheader("3. Delivery Performance by Location")

    #st.write(
     #   "Business Question: Which customer states have the highest average delivery time?"
    #)

    # Create cursor
    cursor = conn.cursor()

    # Calculate average delivery time for each customer state
    delivery_location_query = """
    SELECT
        c.customer_state AS state,

        ROUND(
            AVG(
                TIMESTAMPDIFF(
                    DAY,
                    o.order_purchase_timestamp,
                    o.order_delivered_customer_date
                )
            ),
            2
        ) AS average_delivery_days

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_delivered_customer_date IS NOT NULL

    GROUP BY c.customer_state

    ORDER BY average_delivery_days DESC;
    """

    # Run SQL query
    cursor.execute(delivery_location_query)

    # Get SQL result
    delivery_location_data = cursor.fetchall()

    # Convert result into Pandas DataFrame
    delivery_location_df = pd.DataFrame(
        delivery_location_data,
        columns=["State", "Average Delivery Days"]
    )

    # Convert delivery days into numbers
    delivery_location_df["Average Delivery Days"] = pd.to_numeric(
        delivery_location_df["Average Delivery Days"]
    )

    # Create interactive chart
    delivery_location_chart = px.bar(
        delivery_location_df,
        x="State",
        y="Average Delivery Days",
        title="Average Delivery Time by State"
    )

    # Show chart
    st.plotly_chart(
        delivery_location_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 4. DELIVERY DELAY VS REVIEW SCORE
    # --------------------------------------------------

    st.subheader("4. Delivery Delay vs Review Score")

    #st.write(
     #   "Business Question: How does delivery delay affect customer review scores?"
    #)

    # Calculate delivery delay and average review score
    delivery_review_query = """
    SELECT
        TIMESTAMPDIFF(
            DAY,
            o.order_estimated_delivery_date,
            o.order_delivered_customer_date
        ) AS delivery_delay_days,

        ROUND(AVG(r.review_score), 2) AS average_review_score

    FROM orders o

    JOIN reviews r
        ON o.order_id = r.order_id

    WHERE o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL

    GROUP BY delivery_delay_days

    ORDER BY delivery_delay_days;
    """

    # Run SQL query
    cursor.execute(delivery_review_query)

    # Get result
    delivery_review_data = cursor.fetchall()

    # Convert SQL result into Pandas DataFrame
    delivery_review_df = pd.DataFrame(
        delivery_review_data,
        columns=[
            "Delivery Delay Days",
            "Average Review Score"
        ]
    )

    # Convert columns into numbers
    delivery_review_df["Delivery Delay Days"] = pd.to_numeric(
        delivery_review_df["Delivery Delay Days"]
    )

    delivery_review_df["Average Review Score"] = pd.to_numeric(
        delivery_review_df["Average Review Score"]
    )

    # Create interactive scatter chart
    delivery_review_chart = px.scatter(
        delivery_review_df,
        x="Delivery Delay Days",
        y="Average Review Score",
        title="Delivery Delay vs Review Score"
    )

    # Show chart
    st.plotly_chart(
        delivery_review_chart,
        use_container_width=True
    )
# ==================================================
# 6. CUSTOMER EXPERIENCE
# ==================================================

if menu == "Customer Experience":

    st.header("⭐ Customer Experience")

    st.write(
       "Customer experience analysis will be added here."
    )

    # --------------------------------------------------
    # 1. REVIEW SCORE DISTRIBUTION
    # --------------------------------------------------

    st.subheader("1. Review Score Distribution")

    #st.write(
     #   "Business Question: How are customer review scores distributed?"
    #)
    # Count how many reviews belong to each score
    review_score_query = """
    SELECT
        review_score,
        COUNT(*) AS total_reviews

    FROM reviews

    GROUP BY review_score

    ORDER BY review_score;
    """

    # Run SQL query
    cursor = conn.cursor()
    cursor.execute(review_score_query)

    # Get SQL result
    review_score_data = cursor.fetchall()

    # Convert result into Pandas DataFrame
    review_score_df = pd.DataFrame(
        review_score_data,
        columns=["Review Score", "Total Reviews"]
    )

    # Convert columns into numbers
    review_score_df["Review Score"] = pd.to_numeric(
        review_score_df["Review Score"]
    )

    review_score_df["Total Reviews"] = pd.to_numeric(
        review_score_df["Total Reviews"]
    )

    # Create interactive chart
    review_score_chart = px.bar(
        review_score_df,
        x="Review Score",
        y="Total Reviews",
        title="Customer Review Score Distribution"
    )

    # Show chart
    st.plotly_chart(
        review_score_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 2. REVIEWS BY CATEGORY
    # --------------------------------------------------

    st.subheader("2. Reviews by Category")

    #st.write(
     #   "Business Question: Which product categories receive the most customer reviews?"
    #)

    # First find the product category for each order.
    # DISTINCT prevents the same category from being counted many times
    # when one order contains multiple products from that category.
    reviews_category_query = """
    WITH order_categories AS (
        SELECT DISTINCT
            oi.order_id,

            COALESCE(
                ct.product_category_name_english,
                p.product_category_name,
                'unknown'
            ) AS category

        FROM order_items oi

        JOIN products p
            ON oi.product_id = p.product_id

        LEFT JOIN category_translation ct
            ON p.product_category_name = ct.product_category_name
    )

    SELECT
        oc.category,
        COUNT(*) AS total_reviews

    FROM order_categories oc

    JOIN reviews r
        ON oc.order_id = r.order_id

    GROUP BY oc.category

    ORDER BY total_reviews DESC

    LIMIT 10;
    """

    # Run SQL query
    cursor.execute(reviews_category_query)

    # Get SQL result
    reviews_category_data = cursor.fetchall()

    # Convert result into Pandas DataFrame
    reviews_category_df = pd.DataFrame(
        reviews_category_data,
        columns=["Category", "Total Reviews"]
    )

    # Convert Total Reviews into numbers
    reviews_category_df["Total Reviews"] = pd.to_numeric(
        reviews_category_df["Total Reviews"]
    )

    # Create interactive horizontal bar chart
    reviews_category_chart = px.bar(
        reviews_category_df,
        x="Total Reviews",
        y="Category",
        orientation="h",
        title="Top 10 Categories by Number of Reviews"
    )

    # Show chart
    st.plotly_chart(
        reviews_category_chart,
        use_container_width=True
    )
    # --------------------------------------------------
    # 3. RATING VS DELIVERY PERFORMANCE
    # --------------------------------------------------

    st.subheader("4. Rating vs Delivery Performance")

    #st.write(
     #   "Business Question: Do delayed deliveries receive lower customer ratings?"
    #)

    # Compare review scores for on-time and delayed orders
    rating_delivery_query = """
    SELECT
        CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 'On Time'
            ELSE 'Delayed'
        END AS delivery_status,

        ROUND(AVG(r.review_score), 2) AS average_review_score,

        COUNT(*) AS total_reviews

    FROM orders o

    JOIN reviews r
        ON o.order_id = r.order_id

    WHERE o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL

    GROUP BY delivery_status;
    """

    # Run SQL query
    cursor.execute(rating_delivery_query)

    # Get the result
    rating_delivery_data = cursor.fetchall()

    # Convert SQL result into Pandas DataFrame
    rating_delivery_df = pd.DataFrame(
        rating_delivery_data,
        columns=[
            "Delivery Status",
            "Average Review Score",
            "Total Reviews"
        ]
    )

    # Convert values into numbers
    rating_delivery_df["Average Review Score"] = pd.to_numeric(
        rating_delivery_df["Average Review Score"]
    )

    # Create interactive chart
    rating_delivery_chart = px.bar(
        rating_delivery_df,
        x="Delivery Status",
        y="Average Review Score",
        title="Average Rating: On-Time vs Delayed Deliveries"
    )

    # Show chart
    st.plotly_chart(
        rating_delivery_chart,
        use_container_width=True
    )
