import sqlite3
import streamlit as st
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

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

def add_dress(user_id, name, color_id, season, description=None, brand=None, occasion=None, length=None):
    """Add a new dress to the wardrobe"""
    conn = get_db_connection()
    try:
        # Get the category ID for dresses (should be 3 based on init_db.py)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM categories WHERE name = ?', ('Dresses',))
        category_result = cursor.fetchone()
        
        if not category_result:
            st.error("Dress category not found in database. Please check your database setup.")
            return False
            
        category_id = category_result['id']
        
        # Insert the dress
        cursor.execute('''
            INSERT INTO clothing_items 
            (name, category_id, color_id, season, description, brand, user_id, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category_id, color_id, season, description, brand, user_id, datetime.utcnow()))
        
        # Get the ID of the newly inserted dress
        dress_id = cursor.lastrowid
        
        # Add additional dress properties if needed
        # You could create a separate dresses table with additional fields for length, style, etc.
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding dress: {e}")
        return False
    finally:
        conn.close()

def get_dresses(user_id, color=None, season=None):
    """Get dresses filtered by color and/or season"""
    conn = get_db_connection()
    try:
        # Get the category ID for dresses
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM categories WHERE name = ?', ('Dresses',))
        category_result = cursor.fetchone()
        
        if not category_result:
            return []
            
        category_id = category_result['id']
        
        # Build the query
        query = '''
            SELECT ci.*, c.name as color_name 
            FROM clothing_items ci
            JOIN colors c ON ci.color_id = c.id
            WHERE ci.user_id = ? AND ci.category_id = ?
        '''
        params = [user_id, category_id]
        
        if color:
            query += " AND c.name = ?"
            params.append(color)
            
        if season:
            query += " AND ci.season = ?"
            params.append(season)
            
        # Execute query and get results
        cursor.execute(query, params)
        dresses = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(dress) for dress in dresses]
    except Exception as e:
        st.error(f"Error retrieving dresses: {e}")
        return []
    finally:
        conn.close()

def delete_dress(dress_id, user_id):
    """Delete a dress by ID (checks user ownership)"""
    conn = get_db_connection()
    try:
        # Check if the dress belongs to the user first
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM clothing_items WHERE id = ? AND user_id = ?', 
            (dress_id, user_id)
        )
        dress = cursor.fetchone()
        
        if not dress:
            return False, "Dress not found or you don't have permission to delete it"
        
        # Delete the dress
        cursor.execute('DELETE FROM clothing_items WHERE id = ?', (dress_id,))
        conn.commit()
        return True, "Dress deleted successfully"
    except Exception as e:
        return False, f"Error deleting dress: {e}"
    finally:
        conn.close()

def update_dress(dress_id, user_id, name, color_id, season, description=None, brand=None):
    """Update an existing dress"""
    conn = get_db_connection()
    try:
        # Get the category ID for dresses
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM categories WHERE name = ?', ('Dresses',))
        category_result = cursor.fetchone()
        
        if not category_result:
            return False, "Dress category not found in database"
            
        category_id = category_result['id']
        
        # Check if the dress belongs to the user
        cursor.execute(
            'SELECT id FROM clothing_items WHERE id = ? AND user_id = ?', 
            (dress_id, user_id)
        )
        dress = cursor.fetchone()
        
        if not dress:
            return False, "Dress not found or you don't have permission to edit it"
        
        # Update the dress
        cursor.execute('''
            UPDATE clothing_items 
            SET name = ?, category_id = ?, color_id = ?, season = ?, description = ?, brand = ? 
            WHERE id = ? AND user_id = ?
        ''', (name, category_id, color_id, season, description, brand, dress_id, user_id))
        
        conn.commit()
        return True, "Dress updated successfully"
    except Exception as e:
        return False, f"Error updating dress: {e}"
    finally:
        conn.close()

def dress_management_page():
    """Streamlit page for managing dresses"""
    st.title("FashionFolio Dress Collection")
    
    # Check if user is logged in
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to manage your dresses")
        return
    
    # Initialize edit_dress_id if it doesn't exist
    if 'edit_dress_id' not in st.session_state:
        st.session_state.edit_dress_id = None
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["My Dresses", "Add New Dress", "Edit Dress"])
    
    with tab1:
        # Filters for dresses
        conn = get_db_connection()
        colors = conn.execute('SELECT * FROM colors ORDER BY name').fetchall()
        conn.close()
        
        col1, col2 = st.columns(2)
        with col1:
            color_options = ["All"] + [color["name"] for color in colors]
            selected_color = st.selectbox("Filter by Color", color_options)
            
        with col2:
            season_options = ["All", "Spring", "Summer", "Fall", "Winter", "All Season"]
            selected_season = st.selectbox("Filter by Season", season_options)
        
        # Get dresses based on filters
        color_param = None if selected_color == "All" else selected_color
        season_param = None if selected_season == "All" else selected_season
        dresses = get_dresses(st.session_state.user_id, color_param, season_param)
        
        if dresses:
            st.write(f"Found {len(dresses)} dresses")
            
            # Display dresses in a grid
            cols = st.columns(2)
            for i, dress in enumerate(dresses):
                with cols[i % 2]:
                    st.subheader(dress['name'])
                    st.write(f"**Color:** {dress['color_name']}")
                    st.write(f"**Season:** {dress['season'] or 'Not specified'}")
                    
                    if dress['description']:
                        st.write(f"**Description:** {dress['description']}")
                    if dress['brand']:
                        st.write(f"**Brand:** {dress['brand']}")
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit {dress['name']}", key=f"edit_{dress['id']}"):
                            st.session_state.edit_dress_id = dress['id']
                            st.rerun()
                    with col2:
                        if st.button(f"Delete {dress['name']}", key=f"del_{dress['id']}"):
                            success, message = delete_dress(dress['id'], st.session_state.user_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        else:
            st.info("No dresses found with the selected filters.")
    
    with tab2:
        st.subheader("Add a New Dress")
        
        with st.form("add_dress_form"):
            name = st.text_input("Dress Name")
            
            # Get colors for selection
            conn = get_db_connection()
            colors = conn.execute('SELECT * FROM colors ORDER BY name').fetchall()
            conn.close()
            
            color_id = st.selectbox(
                "Color", 
                options=[c["id"] for c in colors],
                format_func=lambda x: next((c["name"] for c in colors if c["id"] == x), "")
            )
            
            season = st.selectbox(
                "Season", 
                options=["Spring", "Summer", "Fall", "Winter", "All Season"]
            )
            
            description = st.text_area("Description (optional)")
            brand = st.text_input("Brand (optional)")
            occasion = st.selectbox(
                "Occasion", 
                options=["Casual", "Formal", "Business", "Party", "Beach", "Other", "Not specified"]
            )
            
            length = st.selectbox(
                "Length", 
                options=["Mini", "Knee-length", "Midi", "Maxi", "Not specified"]
            )
            
            submit = st.form_submit_button("Add Dress")
            
            if submit:
                if not name or not color_id:
                    st.error("Name and color are required")
                else:
                    # Add optional fields
                    occasion = None if occasion == "Not specified" else occasion
                    length = None if length == "Not specified" else length
                    
                    if add_dress(
                        st.session_state.user_id, 
                        name, 
                        color_id, 
                        season, 
                        description, 
                        brand, 
                        occasion, 
                        length
                    ):
                        st.success(f"Added {name} to your wardrobe!")
                        st.rerun()

    # Tab 3 for editing a dress
    with tab3:
        if st.session_state.edit_dress_id is None:
            st.info("Select a dress to edit from the 'My Dresses' tab")
        else:
            conn = get_db_connection()
            try:
                # Get the dress to edit
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT ci.*, c.name as color_name 
                    FROM clothing_items ci
                    JOIN colors c ON ci.color_id = c.id
                    WHERE ci.id = ? AND ci.user_id = ?
                ''', (st.session_state.edit_dress_id, st.session_state.user_id))
                dress = cursor.fetchone()
                
                if not dress:
                    st.error("Dress not found or you don't have permission to edit it")
                    st.session_state.edit_dress_id = None
                    st.rerun()
                
                # Convert to dict for easier access
                dress = dict(dress)
                
                # Get colors for the form
                colors = conn.execute('SELECT * FROM colors ORDER BY name').fetchall()
                
                st.subheader(f"Edit Dress: {dress['name']}")
                
                with st.form("edit_dress_form"):
                    name = st.text_input("Dress Name", value=dress['name'])
                    
                    # Find the index of the current color
                    color_options = [color["id"] for color in colors]
                    try:
                        color_index = color_options.index(dress['color_id'])
                    except ValueError:
                        color_index = 0
                    
                    color_id = st.selectbox(
                        "Color", 
                        options=color_options,
                        index=color_index,
                        format_func=lambda x: next((color["name"] for color in colors if color["id"] == x), "")
                    )
                    
                    # Find index of current season
                    season_options = ["Spring", "Summer", "Fall", "Winter", "All Season"]
                    try:
                        season_index = season_options.index(dress['season'])
                    except (ValueError, TypeError):
                        season_index = 0
                    
                    season = st.selectbox(
                        "Season", 
                        options=season_options,
                        index=season_index
                    )
                    
                    description = st.text_area("Description (optional)", value=dress['description'] or "")
                    brand = st.text_input("Brand (optional)", value=dress['brand'] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Dress")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    
                    if submit:
                        if not name or not color_id:
                            st.error("Name and color are required")
                        else:
                            success, message = update_dress(
                                st.session_state.edit_dress_id,
                                st.session_state.user_id,
                                name,
                                color_id,
                                season,
                                description,
                                brand
                            )
                            
                            if success:
                                st.success(message)
                                st.session_state.edit_dress_id = None
                                st.rerun()
                            else:
                                st.error(message)
                    
                    if cancel:
                        st.session_state.edit_dress_id = None
                        st.rerun()
            finally:
                conn.close()

# Add footer with copyright when running as standalone
def add_footer():
    st.markdown("---")
    footer_html = """
    <div style="text-align: center; color: #666; padding: 10px;">
        © 2025 FashionFolio by Jai Srivastava. All rights reserved.
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    # Setup page config
    st.set_page_config(
        page_title="FashionFolio Dress Collection",
        page_icon="👗",
        layout="wide"
    )
    
    # Check if user is logged in via session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if not st.session_state.user_id:
        st.warning("Please login from the main application first")
    else:
        dress_management_page()
        
    # Add footer
    add_footer() 