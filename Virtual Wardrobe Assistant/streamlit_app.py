import streamlit as st
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

# Import dresses management module
try:
    import dresses
except ImportError:
    dresses = None

# Set page config
st.set_page_config(
    page_title="FashionFolio: Your Digital Wardrobe",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_db_connection():
    try:
        db_path = os.path.join('instance', 'wardrobe.db')
        if not os.path.exists(db_path):
            st.error("Database not found. Please run `python init_db.py` first to initialize the database.")
            st.stop()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database error: {e}")
        st.stop()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Authentication functions
def authenticate(username, password):
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            # Use werkzeug's check_password_hash to verify the password
            if check_password_hash(user['password_hash'], password):
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.session_state.authenticated = True
                return True
        return False
    finally:
        conn.close()

def register_user(username, email, password):
    conn = get_db_connection()
    try:
        # Check if username exists
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                                   (username, email)).fetchone()
        if existing_user:
            return False, "Username or email already exists"
        
        # Hash the password before storing
        password_hash = generate_password_hash(password)
        
        # Insert new user
        conn.execute('INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                   (username, email, password_hash, datetime.utcnow()))
        conn.commit()
        return True, "Registration successful! Please login."
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

# Sidebar navigation
def sidebar_nav():
    with st.sidebar:
        st.title("FashionFolio")
        st.caption("Your Personal Style Companion")
        
        if not st.session_state.authenticated:
            if st.button("Login"):
                st.session_state.page = "login"
            if st.button("Register"):
                st.session_state.page = "register"
            if st.button("About"):
                st.session_state.page = "about"
        else:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Dashboard"):
                st.session_state.page = "dashboard"
            if st.button("My Wardrobe"):
                st.session_state.page = "wardrobe"
            if st.button("Outfits"):
                st.session_state.page = "outfits"
            if st.button("Dresses"):
                st.session_state.page = "dresses"
            if st.button("Suggestions"):
                st.session_state.page = "suggestions"
            if st.button("About"):
                st.session_state.page = "about"
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.page = "login"
                st.rerun()

# Pages
def login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if authenticate(username, password):
                st.success("Login successful!")
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password")

def register_page():
    st.title("Register")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        
        if submit:
            if not username or not email or not password:
                st.error("All fields are required")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = register_user(username, email, password)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)

def dashboard_page():
    st.title("Dashboard")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view this page")
        st.session_state.page = "login"
        st.rerun()
        
    conn = get_db_connection()
    try:
        # Get counts
        clothing_count = conn.execute('SELECT COUNT(*) FROM clothing_items WHERE user_id = ?', 
                                    (st.session_state.user_id,)).fetchone()[0]
        outfit_count = conn.execute('SELECT COUNT(*) FROM outfits WHERE user_id = ?', 
                                  (st.session_state.user_id,)).fetchone()[0]
        
        # Create dashboard
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clothing Items", clothing_count)
        with col2:
            st.metric("Outfits", outfit_count)
        with col3:
            st.metric("Current Date", datetime.now().strftime("%Y-%m-%d"))
            
        # Recent items
        st.subheader("Recent Clothing Items")
        recent_items = conn.execute(
            'SELECT * FROM clothing_items WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', 
            (st.session_state.user_id,)
        ).fetchall()
        
        if recent_items:
            # Convert to list of dicts to ensure we can access columns by name
            items_list = [dict(item) for item in recent_items]
            items_df = pd.DataFrame(items_list)
            
            # Get only columns that exist
            display_columns = []
            for col in ['name', 'description', 'brand', 'season', 'created_at']:
                if col in items_df.columns:
                    display_columns.append(col)
            
            if display_columns:
                st.dataframe(items_df[display_columns], use_container_width=True)
            else:
                st.dataframe(items_df, use_container_width=True)
        else:
            st.info("No clothing items found. Add some to your wardrobe!")
            
        # Recent outfits
        st.subheader("Recent Outfits")
        recent_outfits = conn.execute(
            'SELECT * FROM outfits WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', 
            (st.session_state.user_id,)
        ).fetchall()
        
        if recent_outfits:
            # Convert to list of dicts to ensure we can access columns by name
            outfits_list = [dict(outfit) for outfit in recent_outfits]
            outfits_df = pd.DataFrame(outfits_list)
            
            # Get only columns that exist
            display_columns = []
            for col in ['name', 'description', 'occasion', 'season', 'created_at']:
                if col in outfits_df.columns:
                    display_columns.append(col)
            
            if display_columns:
                st.dataframe(outfits_df[display_columns], use_container_width=True)
            else:
                st.dataframe(outfits_df, use_container_width=True)
        else:
            st.info("No outfits found. Create some outfit combinations!")
    finally:
        conn.close()

def about_page():
    st.title("About FashionFolio")
    
    st.write("""
    ## Welcome to FashionFolio: Your Digital Wardrobe!
    
    FashionFolio helps you manage your clothing collection, create outfits, and get recommendations
    based on weather conditions and your personal style preferences.
    
    ### Features:
    
    - **Wardrobe Management**: Keep track of all your clothing items with details
    - **Outfit Creation**: Combine items into complete outfits
    - **Suggestions**: Get outfit recommendations based on various factors
    - **Wear Tracking**: Track when and where you've worn specific items or outfits
    - **Dress Collection**: Special section for managing your dress collection
    
    ### Technology Stack:
    
    - **Streamlit**: For the web interface
    - **SQLite**: For data storage
    - **Python**: For application logic
    
    ### Get Started:
    
    Register an account to begin organizing your wardrobe and creating stylish outfit combinations!
    
    ### Demo Account:
    
    You can try out the application using the demo account:
    - **Username**: demo
    - **Password**: password123
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/examples/data/logo.png", width=100)
        st.caption("Streamlit")
    with col2:
        st.image("https://www.python.org/static/community_logos/python-logo.png", width=100)
        st.caption("Python")
    with col3:
        st.image("https://www.sqlite.org/images/sqlite370_banner.gif", width=100)
        st.caption("SQLite")
        
    # Add copyright notice
    st.markdown("---")
    st.markdown("© 2025 FashionFolio by Jai Srivastava. All rights reserved.")

def wardrobe_page():
    st.title("My Wardrobe")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view this page")
        st.session_state.page = "login"
        st.rerun()
    
    # Initialize session state for edit_item if it doesn't exist
    if 'edit_item_id' not in st.session_state:
        st.session_state.edit_item_id = None
    
    # Tabs for viewing and adding items
    tab1, tab2, tab3 = st.tabs(["View Items", "Add New Item", "Edit Item"])
    
    with tab1:
        conn = get_db_connection()
        try:
            # Get categories and colors for filtering
            categories = conn.execute('SELECT * FROM categories').fetchall()
            colors = conn.execute('SELECT * FROM colors').fetchall()
            
            # Create filters
            col1, col2, col3 = st.columns(3)
            with col1:
                category_options = ["All"] + [cat["name"] for cat in categories]
                selected_category = st.selectbox("Filter by Category", category_options)
            
            with col2:
                color_options = ["All"] + [color["name"] for color in colors]
                selected_color = st.selectbox("Filter by Color", color_options)
                
            with col3:
                season_options = ["All", "Spring", "Summer", "Fall", "Winter", "All Season"]
                selected_season = st.selectbox("Filter by Season", season_options)
            
            # Build query
            query = '''
                SELECT ci.*, c.name as category_name, col.name as color_name 
                FROM clothing_items ci
                JOIN categories c ON ci.category_id = c.id
                JOIN colors col ON ci.color_id = col.id
                WHERE ci.user_id = ?
            '''
            params = [st.session_state.user_id]
            
            if selected_category != "All":
                query += " AND c.name = ?"
                params.append(selected_category)
                
            if selected_color != "All":
                query += " AND col.name = ?"
                params.append(selected_color)
                
            if selected_season != "All":
                query += " AND ci.season = ?"
                params.append(selected_season)
                
            items = conn.execute(query, params).fetchall()
            
            # Display items
            if items:
                # Convert to a list of dicts for easier display
                items_list = [dict(item) for item in items]
                items_df = pd.DataFrame(items_list)
                
                st.write(f"Found {len(items)} items")
                
                # Display items in a grid
                cols = st.columns(3)
                for i, item in enumerate(items_list):
                    with cols[i % 3]:
                        st.subheader(item['name'])
                        st.write(f"**Category:** {item['category_name']}")
                        st.write(f"**Color:** {item['color_name']}")
                        st.write(f"**Season:** {item['season'] or 'Not specified'}")
                        if item['description']:
                            st.write(f"**Description:** {item['description']}")
                        if item['brand']:
                            st.write(f"**Brand:** {item['brand']}")
                        
                        # Actions
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Edit {item['name']}", key=f"edit_{item['id']}"):
                                st.session_state.edit_item_id = item['id']
                                # Switch to edit tab
                                st.rerun()
                        with col2:
                            if st.button(f"Delete {item['name']}", key=f"delete_{item['id']}"):
                                conn.execute('DELETE FROM clothing_items WHERE id = ?', (item['id'],))
                                conn.commit()
                                st.success(f"Deleted {item['name']}")
                                st.rerun()
            else:
                st.info("No items found with the selected filters. Try different filters or add new items.")
        finally:
            conn.close()
                
    with tab2:
        conn = get_db_connection()
        try:
            # Get categories and colors for the form
            categories = conn.execute('SELECT * FROM categories').fetchall()
            colors = conn.execute('SELECT * FROM colors').fetchall()
            
            with st.form("add_item_form"):
                st.subheader("Add New Clothing Item")
                
                name = st.text_input("Item Name")
                
                col1, col2 = st.columns(2)
                with col1:
                    category_id = st.selectbox(
                        "Category", 
                        options=[cat["id"] for cat in categories],
                        format_func=lambda x: next((cat["name"] for cat in categories if cat["id"] == x), "")
                    )
                
                with col2:
                    color_id = st.selectbox(
                        "Color", 
                        options=[color["id"] for color in colors],
                        format_func=lambda x: next((color["name"] for color in colors if color["id"] == x), "")
                    )
                
                season = st.selectbox(
                    "Season", 
                    options=["Spring", "Summer", "Fall", "Winter", "All Season"]
                )
                
                description = st.text_area("Description (optional)")
                brand = st.text_input("Brand (optional)")
                
                submit = st.form_submit_button("Add Item")
                
                if submit:
                    if not name or not category_id or not color_id:
                        st.error("Name, category and color are required")
                    else:
                        try:
                            conn.execute(
                                '''INSERT INTO clothing_items 
                                (name, category_id, color_id, season, description, brand, user_id, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (name, category_id, color_id, season, description, brand, 
                                 st.session_state.user_id, datetime.utcnow())
                            )
                            conn.commit()
                            st.success(f"Added {name} to your wardrobe!")
                            # Clear form fields
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding item: {e}")
        finally:
            conn.close()
            
    # New tab3 (Edit Item) code
    with tab3:
        if st.session_state.edit_item_id is None:
            st.info("Select an item to edit from the 'View Items' tab")
        else:
            conn = get_db_connection()
            try:
                # Get categories and colors for the form
                categories = conn.execute('SELECT * FROM categories').fetchall()
                colors = conn.execute('SELECT * FROM colors').fetchall()
                
                # Get the item to edit
                item = conn.execute(
                    'SELECT * FROM clothing_items WHERE id = ? AND user_id = ?', 
                    (st.session_state.edit_item_id, st.session_state.user_id)
                ).fetchone()
                
                if not item:
                    st.error("Item not found or you don't have permission to edit it")
                    st.session_state.edit_item_id = None
                    st.rerun()
                
                # Convert to dict for easier access
                item = dict(item)
                
                st.subheader(f"Edit Item: {item['name']}")
                
                with st.form("edit_item_form"):
                    name = st.text_input("Item Name", value=item['name'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        category_id = st.selectbox(
                            "Category", 
                            options=[cat["id"] for cat in categories],
                            index=[i for i, cat in enumerate(categories) if cat["id"] == item['category_id']][0],
                            format_func=lambda x: next((cat["name"] for cat in categories if cat["id"] == x), "")
                        )
                    
                    with col2:
                        color_id = st.selectbox(
                            "Color", 
                            options=[color["id"] for color in colors],
                            index=[i for i, color in enumerate(colors) if color["id"] == item['color_id']][0],
                            format_func=lambda x: next((color["name"] for color in colors if color["id"] == x), "")
                        )
                    
                    # Find index of current season
                    season_options = ["Spring", "Summer", "Fall", "Winter", "All Season"]
                    try:
                        season_index = season_options.index(item['season'])
                    except (ValueError, TypeError):
                        season_index = 0
                    
                    season = st.selectbox(
                        "Season", 
                        options=season_options,
                        index=season_index
                    )
                    
                    description = st.text_area("Description (optional)", value=item['description'] or "")
                    brand = st.text_input("Brand (optional)", value=item['brand'] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Item")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    
                    if submit:
                        if not name or not category_id or not color_id:
                            st.error("Name, category and color are required")
                        else:
                            try:
                                conn.execute(
                                    '''UPDATE clothing_items 
                                    SET name = ?, category_id = ?, color_id = ?, 
                                        season = ?, description = ?, brand = ? 
                                    WHERE id = ? AND user_id = ?''',
                                    (name, category_id, color_id, season, description, brand, 
                                     st.session_state.edit_item_id, st.session_state.user_id)
                                )
                                conn.commit()
                                st.success(f"Updated {name}")
                                st.session_state.edit_item_id = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating item: {e}")
                    
                    if cancel:
                        st.session_state.edit_item_id = None
                        st.rerun()
            finally:
                conn.close()

def outfits_page():
    st.title("My Outfits")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view this page")
        st.session_state.page = "login"
        st.rerun()
    
    # Tabs for viewing and creating outfits
    tab1, tab2 = st.tabs(["View Outfits", "Create Outfit"])
    
    with tab1:
        conn = get_db_connection()
        try:
            # Get outfits
            outfits = conn.execute(
                'SELECT * FROM outfits WHERE user_id = ? ORDER BY created_at DESC', 
                (st.session_state.user_id,)
            ).fetchall()
            
            if outfits:
                outfits_list = [dict(outfit) for outfit in outfits]
                
                # Display outfits in a grid
                cols = st.columns(2)
                for i, outfit in enumerate(outfits_list):
                    with cols[i % 2]:
                        st.subheader(outfit['name'])
                        if outfit['description']:
                            st.write(outfit['description'])
                        st.write(f"**Occasion:** {outfit['occasion'] or 'Not specified'}")
                        st.write(f"**Season:** {outfit['season'] or 'Not specified'}")
                        
                        # Get outfit items
                        outfit_items = conn.execute(
                            '''
                            SELECT oi.*, ci.name as item_name, c.name as category_name 
                            FROM outfit_items oi
                            JOIN clothing_items ci ON oi.clothing_item_id = ci.id
                            JOIN categories c ON ci.category_id = c.id
                            WHERE oi.outfit_id = ?
                            ''',
                            (outfit['id'],)
                        ).fetchall()
                        
                        if outfit_items:
                            st.write("**Items:**")
                            for item in outfit_items:
                                st.write(f"- {item['item_name']} ({item['category_name']})")
                        
                        # Actions
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Edit {outfit['name']}", key=f"edit_outfit_{outfit['id']}"):
                                st.session_state.edit_outfit_id = outfit['id']
                                st.rerun()
                        with col2:
                            if st.button(f"Delete {outfit['name']}", key=f"delete_outfit_{outfit['id']}"):
                                # Delete outfit items first (foreign key constraint)
                                conn.execute('DELETE FROM outfit_items WHERE outfit_id = ?', (outfit['id'],))
                                conn.execute('DELETE FROM outfits WHERE id = ?', (outfit['id'],))
                                conn.commit()
                                st.success(f"Deleted {outfit['name']}")
                                st.rerun()
            else:
                st.info("No outfits found. Create your first outfit!")
        finally:
            conn.close()
    
    with tab2:
        conn = get_db_connection()
        try:
            # Get clothing items for creating outfit
            clothing_items = conn.execute(
                '''
                SELECT ci.*, c.name as category_name, col.name as color_name 
                FROM clothing_items ci
                JOIN categories c ON ci.category_id = c.id
                JOIN colors col ON ci.color_id = col.id
                WHERE ci.user_id = ?
                ORDER BY c.name, ci.name
                ''',
                (st.session_state.user_id,)
            ).fetchall()
            
            if not clothing_items:
                st.warning("You need to add clothing items before creating outfits")
                st.stop()
            
            with st.form("create_outfit_form"):
                st.subheader("Create New Outfit")
                
                name = st.text_input("Outfit Name")
                description = st.text_area("Description (optional)")
                
                col1, col2 = st.columns(2)
                with col1:
                    occasion = st.selectbox(
                        "Occasion", 
                        options=["Casual", "Formal", "Business", "Sport", "Party", "Other"]
                    )
                
                with col2:
                    season = st.selectbox(
                        "Season", 
                        options=["Spring", "Summer", "Fall", "Winter", "All Season"]
                    )
                
                # Group items by category for selection
                st.write("**Select Items:**")
                
                # Get all categories that have items
                categories = list(set(item['category_name'] for item in clothing_items))
                categories.sort()
                
                selected_items = {}
                for category in categories:
                    category_items = [item for item in clothing_items if item['category_name'] == category]
                    if category_items:
                        st.write(f"**{category}**")
                        items_in_category = {item['name']: item['id'] for item in category_items}
                        selected_items[category] = st.multiselect(
                            f"Select {category}", 
                            options=list(items_in_category.keys()),
                            key=f"cat_{category}"
                        )
                        selected_items[category] = [items_in_category[item] for item in selected_items[category]]
                
                submit = st.form_submit_button("Create Outfit")
                
                if submit:
                    if not name:
                        st.error("Outfit name is required")
                    elif not any(selected_items.values()):
                        st.error("Select at least one item for the outfit")
                    else:
                        try:
                            # Insert outfit
                            cursor = conn.cursor()
                            cursor.execute(
                                '''INSERT INTO outfits 
                                (name, description, occasion, season, user_id, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?)''',
                                (name, description, occasion, season, st.session_state.user_id, datetime.utcnow())
                            )
                            outfit_id = cursor.lastrowid
                            
                            # Insert outfit items
                            for category, item_ids in selected_items.items():
                                for item_id in item_ids:
                                    conn.execute(
                                        '''INSERT INTO outfit_items 
                                        (outfit_id, clothing_item_id) 
                                        VALUES (?, ?)''',
                                        (outfit_id, item_id)
                                    )
                            
                            conn.commit()
                            st.success(f"Created outfit: {name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating outfit: {e}")
        finally:
            conn.close()

def suggestions_page():
    st.title("Outfit Suggestions")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view this page")
        st.session_state.page = "login"
        st.rerun()
    
    conn = get_db_connection()
    try:
        # Get user preferences
        user = conn.execute(
            'SELECT * FROM users WHERE id = ?', 
            (st.session_state.user_id,)
        ).fetchone()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Parameters")
            
            occasion = st.selectbox(
                "Occasion", 
                options=["Casual", "Formal", "Business", "Sport", "Party", "Other"],
                index=0
            )
            
            season = st.selectbox(
                "Season", 
                options=["Spring", "Summer", "Fall", "Winter"],
                index=datetime.now().month % 12 // 3  # Default to current season
            )
            
            if user and user['location']:
                st.write(f"Your location: {user['location']}")
                
                # Here we would normally fetch weather data
                # For simplicity, we'll use mock data
                st.write("Current weather: Sunny, 22°C")
                
        with col2:
            st.subheader("Style Preferences")
            style_pref = st.radio(
                "Style preference",
                options=["Casual", "Formal", "Business", "Trendy", "Classic", "Sporty"],
                index=0 if not user or not user['style_preference'] else 0
            )
            
            color_scheme = st.radio(
                "Color scheme",
                options=["Monochromatic", "Complementary", "Analogous", "Any"],
                index=3
            )
        
        if st.button("Generate Suggestions"):
            st.write("---")
            st.subheader("Suggested Outfits")
            
            # In a real app, we would run an algorithm to suggest outfits based on the parameters
            # For now, we'll just show some existing outfits
            outfits = conn.execute(
                '''
                SELECT * FROM outfits 
                WHERE user_id = ? AND (occasion = ? OR occasion IS NULL) AND (season = ? OR season = 'All Season')
                LIMIT 3
                ''',
                (st.session_state.user_id, occasion, season)
            ).fetchall()
            
            if outfits:
                for outfit in outfits:
                    st.write(f"### {outfit['name']}")
                    if outfit['description']:
                        st.write(outfit['description'])
                    
                    # Get outfit items
                    outfit_items = conn.execute(
                        '''
                        SELECT oi.*, ci.name as item_name, c.name as category_name 
                        FROM outfit_items oi
                        JOIN clothing_items ci ON oi.clothing_item_id = ci.id
                        JOIN categories c ON ci.category_id = c.id
                        WHERE oi.outfit_id = ?
                        ''',
                        (outfit['id'],)
                    ).fetchall()
                    
                    if outfit_items:
                        st.write("**Items:**")
                        for item in outfit_items:
                            st.write(f"- {item['item_name']} ({item['category_name']})")
            else:
                # If no matching outfits, suggest items to combine
                st.info("No matching outfits found. Here are some items you could combine:")
                
                # Get items matching season and style
                items = conn.execute(
                    '''
                    SELECT ci.*, c.name as category_name, col.name as color_name 
                    FROM clothing_items ci
                    JOIN categories c ON ci.category_id = c.id
                    JOIN colors col ON ci.color_id = col.id
                    WHERE ci.user_id = ? AND (ci.season = ? OR ci.season = 'All Season')
                    ORDER BY RANDOM()
                    LIMIT 5
                    ''',
                    (st.session_state.user_id, season)
                ).fetchall()
                
                if items:
                    for item in items:
                        st.write(f"- {item['name']} ({item['category_name']}, {item['color_name']})")
                else:
                    st.warning("No suitable items found. Try adding more items to your wardrobe.")
    finally:
        conn.close()

# Add global footer with copyright
def add_footer():
    st.markdown("---")
    footer_html = """
    <div style="text-align: center; color: #666; padding: 10px;">
        © 2025 FashionFolio by Jai Srivastava. All rights reserved.
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

def main():
    # Initialize page state if not set
    if 'page' not in st.session_state:
        st.session_state.page = "login" if not st.session_state.authenticated else "dashboard"
    
    # Display navigation sidebar
    sidebar_nav()
    
    # Render the appropriate page based on state
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "wardrobe":
        wardrobe_page()
    elif st.session_state.page == "outfits":
        outfits_page()
    elif st.session_state.page == "dresses":
        if dresses:
            dresses.dress_management_page()
        else:
            st.error("Dresses module not found. Please make sure dresses.py exists in the application directory.")
    elif st.session_state.page == "suggestions":
        suggestions_page()
    elif st.session_state.page == "about":
        about_page()
    else:
        st.error("Page not found")
    
    # Add copyright footer to all pages
    add_footer()

if __name__ == "__main__":
    main() 