# FashionFolio: Your Digital Wardrobe

A web application that helps you manage your clothing collection, create outfits, and get suggestions based on various factors like weather and personal style.

## Features

- **Wardrobe Management**: Keep track of all your clothing items with details
- **Outfit Creation**: Combine items into complete outfits
- **Suggestions**: Get outfit recommendations based on weather and occasion
- **Wear Tracking**: Track when and where you've worn specific items or outfits
- **Dress Collection**: Special section for managing your dress collection

## Technology Stack

- **Backend**: Python, SQLite
- **Frontend**: Streamlit
- **Dependencies**: See requirements.txt

## Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/TheJaiSrivastava/FashionFolio
   cd FashionFolio
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   streamlit run streamlit_app.py
   ```

6. Access the application in your web browser at `http://localhost:8501`

## Usage

1. **Register/Login**: Create an account or log in to your existing account
   - Default login credentials: 
     - Username: `demo`
     - Password: `password123`
2. **Add Clothing Items**: Add your clothing items with details
3. **Create Outfits**: Combine items to create complete outfits
4. **Get Suggestions**: Get suggestions based on weather and occasion

## Running with Flask (Alternative)

For users who prefer Flask, you can also run the application using Flask:

```
python -m flask run
```

Access the Flask version at `http://127.0.0.1:5000`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Copyright

© 2025 FashionFolio by Jai Srivastava. All rights reserved.

## Acknowledgments

- This project was created as a practical tool for managing wardrobe and creating outfit combinations.
- Thanks to the Streamlit and Flask communities for their excellent documentation and frameworks. 