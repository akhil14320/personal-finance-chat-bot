import streamlit as st
import os
import sys
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import time
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
from streamlit_option_menu import option_menu
import requests # Added for making API calls

# --- 1. CONFIGURATION & SETUP ---

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
# You will need to get an API key from a service like ExchangeRate-API.com
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

if not API_KEY:
    st.error("🚫 Configuration Error: GOOGLE_API_KEY not found.")
    st.info("Please create a file named `.env` in the same directory and add the line: GOOGLE_API_KEY='your_api_key_here'")
    st.stop()
    
if not EXCHANGE_RATE_API_KEY:
    st.error("🚫 Configuration Error: EXCHANGE_RATE_API_KEY not found.")
    st.info("Please create a file named `.env` and add the line: EXCHANGE_RATE_API_KEY='your_api_key_here' from a service like ExchangeRate-API.com.")
    st.stop()


# Configure the Gemini API
try:
    genai.configure(api_key=API_KEY)
    llm = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Failed to configure Gemini API: {e}")
    st.stop()

# Currency Data (as provided, no changes needed)
CURRENCIES = {
    'USD': 'United States Dollar', 'EUR': 'Euro', 'JPY': 'Japanese Yen', 'GBP': 'British Pound Sterling',
    'AUD': 'Australian Dollar', 'CAD': 'Canadian Dollar', 'CHF': 'Swiss Franc', 'CNY': 'Chinese Yuan',
    'SEK': 'Swedish Krona', 'NZD': 'New Zealand Dollar', 'MXN': 'Mexican Peso', 'SGD': 'Singapore Dollar',
    'HKD': 'Hong Kong Dollar', 'NOK': 'Norwegian Krone', 'KRW': 'South Korean Won', 'TRY': 'Turkish Lira',
    'RUB': 'Russian Ruble', 'INR': 'Indian Rupee', 'BRL': 'Brazilian Real', 'ZAR': 'South African Rand',
    'AED': 'United Arab Emirates Dirham', 'AFN': 'Afghan Afghani', 'ALL': 'Albanian Lek', 'AMD': 'Armenian Dram',
    'ANG': 'Netherlands Antillean Guilder', 'AOA': 'Angolan Kwanza', 'ARS': 'Argentine Peso',
    'AWG': 'Aruban Florin', 'AZN': 'Azerbaijani Manat', 'BAM': 'Bosnia-Herzegovina Convertible Mark',
    'BBD': 'Barbadian Dollar', 'BDT': 'Bangladeshi Taka', 'BGN': 'Bulgarian Lev', 'BHD': 'Bahraini Dinar',
    'BIF': 'Burundian Franc', 'BMD': 'Bermudan Dollar', 'BND': 'Brunei Dollar', 'BOB': 'Bolivian Boliviano',
    'BSD': 'Bahamian Dollar', 'BTN': 'Bhutanese Ngultrum', 'BWP': 'Botswanan Pula', 'BYN': 'Belarusian Ruble',
    'BZD': 'Belize Dollar', 'CDF': 'Congolese Franc', 'CLP': 'Chilean Peso', 'COP': 'Colombian Peso',
    'CRC': 'Costa Rican Colón', 'CUP': 'Cuban Peso', 'CVE': 'Cape Verdean Escudo', 'CZK': 'Czech Koruna',
    'DJF': 'Djiboutian Franc', 'DKK': 'Danish Krone', 'DOP': 'Dominican Peso', 'DZD': 'Algerian Dinar',
    'EGP': 'Egyptian Pound', 'ERN': 'Eritrean Nakfa', 'ETB': 'Ethiopian Birr', 'FJD': 'Fijian Dollar',
    'FKP': 'Falkland Islands Pound', 'FOK': 'Faroese Króna', 'GEL': 'Georgian Lari', 'GGP': 'Guernsey Pound',
    'GHS': 'Ghanaian Cedi', 'GIP': 'Gibraltar Pound', 'GMD': 'Gambian Dalasi', 'GNF': 'Guinean Franc',
    'GTQ': 'Guatemalan Quetzal', 'GYD': 'Guyanaese Dollar', 'HNL': 'Honduran Lempira', 'HRK': 'Croatian Kuna',
    'HTG': 'Haitian Gourde', 'HUF': 'Hungarian Forint', 'IDR': 'Indonesian Rupiah', 'ILS': 'Israeli New Shekel',
    'IMP': 'Isle of Man Pound', 'IQD': 'Iraqi Dinar', 'IRR': 'Iranian Rial', 'ISK': 'Icelandic Króna',
    'JEP': 'Jersey Pound', 'JMD': 'Jamaican Dollar', 'JOD': 'Jordanian Dinar', 'KES': 'Kenyan Shilling',
    'KGS': 'Kyrgystani Som', 'KHR': 'Cambodian Riel', 'KID': 'Kiribati Dollar', 'KMF': 'Comorian Franc',
    'KWD': 'Kuwaiti Dinar', 'KYD': 'Cayman Islands Dollar', 'KZT': 'Kazakhstani Tenge', 'LAK': 'Laotian Kip',
    'LBP': 'Lebanese Pound', 'LKR': 'Sri Lankan Rupee', 'LRD': 'Liberian Dollar', 'LSL': 'Lesotho Loti',
    'LYD': 'Libyan Dinar', 'MAD': 'Moroccan Dirham', 'MDL': 'Moldovan Leu', 'MGA': 'Malagasy Ariary',
    'MKD': 'Macedonian Denar', 'MMK': 'Myanma Kyat', 'MNT': 'Mongolian Tugrik', 'MOP': 'Macanese Pataca',
    'MRU': 'Mauritanian Ouguiya', 'MUR': 'Mauritian Rupee', 'MVR': 'Maldivian Rufiyaa', 'MWK': 'Malawian Kwacha',
    'MYR': 'Malaysian Ringgit', 'MZN': 'Mozambican Metical', 'NAD': 'Namibian Dollar', 'NGN': 'Nigerian Naira',
    'NIO': 'Nicaraguan Córdoba', 'NPR': 'Nepalese Rupee', 'OMR': 'Omani Rial', 'PAB': 'Panamanian Balboa',
    'PEN': 'Peruvian Sol', 'PGK': 'Papua New Guinean Kina', 'PHP': 'Philippine Peso', 'PKR': 'Pakistani Rupee',
    'PLN': 'Polish Zloty', 'PYG': 'Paraguayan Guarani', 'QAR': 'Qatari Rial', 'RON': 'Romanian Leu',
    'RSD': 'Serbian Dinar', 'RWF': 'Rwandan Franc', 'SAR': 'Saudi Riyal', 'SBD': 'Solomon Islands Dollar',
    'SCR': 'Seychellois Rupee', 'SDG': 'Sudanese Pound', 'SHP': 'Saint Helena Pound', 'SLE': 'Sierra Leonean Leone',
    'SOS': 'Somali Shilling', 'SRD': 'Surinamese Dollar', 'SSP': 'South Sudanese Pound',
    'STN': 'São Tomé and Príncipe Dobra', 'SYP': 'Syrian Pound', 'SZL': 'Eswatini Lilangeni',
    'THB': 'Thai Baht', 'TJS': 'Tajikistani Somoni', 'TMT': 'Turkmenistani Manat', 'TND': 'Tunisian Dinar',
    'TOP': 'Tongan Paʻanga', 'TTD': 'Trinidad and Tobago Dollar', 'TVD': 'Tuvaluan Dollar',
    'TWD': 'New Taiwan Dollar', 'TZS': 'Tanzanian Shilling', 'UAH': 'Ukrainian Hryvnia',
    'UGX': 'Ugandan Shilling', 'UYU': 'Uruguayan Peso', 'UZS': 'Uzbekistan Som', 'VES': 'Venezuelan Bolívar',
    'VND': 'Vietnamese Dong', 'VUV': 'Vanuatu Vatu', 'WST': 'Samoan Tala', 'XAF': 'Central African CFA Franc',
    'XCD': 'East Caribbean Dollar', 'XDR': 'Special Drawing Rights', 'XOF': 'West African CFA Franc',
    'XPF': 'CFP Franc', 'YER': 'Yemeni Rial', 'ZMW': 'Zambian Kwacha', 'ZWL': 'Zimbabwean Dollar'
}

# --- 2. HELPER FUNCTIONS ---

def get_real_time_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """Fetches a real-time exchange rate from an external API."""
    base_url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{from_currency}/{to_currency}"
    try:
        response = requests.get(base_url)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()
        if data["result"] == "success":
            return data["conversion_rate"]
        else:
            st.error(f"API Error: {data.get('error-type', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to the exchange rate API. Please check your internet connection. {e}")
        return None
    except KeyError:
        st.error("API Response Error: The API response format was unexpected.")
        return None

def safe_generate_content(model, prompt):
    """
    Wraps the generate_content call with exponential backoff for quota errors.
    """
    retries = 0
    max_retries = 5
    while retries < max_retries:
        try:
            return model.generate_content(prompt)
        except genai.types.BlockedPromptException as e:
            st.error(f"Error: Prompt blocked by safety policy.")
            raise e
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                retry_delay = 2 ** retries
                st.warning(f"We're experiencing high traffic. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retries += 1
            else:
                raise e
    st.error("We're having trouble reaching the service right now. Please wait a moment and try again.")
    return None

def build_advanced_currency_prompt(from_currency: str, to_currency: str, amount: float, real_time_rate: float, lookup_date: date = None) -> str:
    """Builds an advanced prompt for currency conversion with historical data, with a stronger emphasis on a strict JSON format."""
    
    date_prompt_part = ""
    if lookup_date:
        date_prompt_part = f"""
        Provide the exchange rate and converted amount for the specific historical date: {lookup_date.strftime('%Y-%m-%d')}. This should be in a JSON object with the key 'historical_rate'.
        """
    
    return f"""
    You are an expert currency and financial data analyst. Your primary task is to provide currency data in a specific, strict JSON format.

    - **Task 1: Real-Time Conversion.** Given the current exchange rate from {from_currency} to {to_currency} is {real_time_rate}, calculate the total for {amount} {from_currency}.
    - **Task 2: Historical Trend.** Provide a list of the daily exchange rates for {from_currency} to {to_currency} for the last 30 days (ending yesterday). Each item in the list must be an object with 'date' and 'rate' keys.
    - **Task 3: Specific Date (if requested).** {date_prompt_part}

    Your ENTIRE response MUST be a single, clean JSON object with NO additional text or markdown outside of the JSON block. Do not include any explanatory text before or after the JSON.

    The JSON must contain the following keys, and their values must match the specified structure:
    - "real_time": {{ "rate": <number>, "converted_amount": <number>, "explanation": "<string>" }}
    - "historical_trend": [ {{ "date": "<YYYY-MM-DD>", "rate": <number> }}, ... ]
    - "historical_rate": {{ "date": "<YYYY-MM-DD>", "rate": <number>, "converted_amount": <number>, "explanation": "<string>" }} (this key is only required if a specific historical date was requested).

    Here is a detailed example of the expected format:
    ```json
    {{
      "real_time": {{
        "rate": 1.2345,
        "converted_amount": 123.45,
        "explanation": "The real-time conversion from USD to EUR."
      }},
      "historical_trend": [
        {{ "date": "2023-01-01", "rate": 1.2500 }},
        {{ "date": "2023-01-02", "rate": 1.2480 }}
        // ... more data
      ],
      "historical_rate": {{
        "date": "2023-01-01",
        "rate": 1.2500,
        "converted_amount": 125.00,
        "explanation": "The historical conversion from USD to EUR on 2023-01-01."
      }}
    }}
    ```
    
    Generate the JSON for this request: From {from_currency}, To {to_currency}, Amount {amount}.
    JSON Output:
    """

def build_budget_summary_prompt(income: float, expenses: dict, currency: str) -> str:
    """Builds a prompt for a budget summary."""
    expense_details = "\n".join([f"- {category.capitalize()}: {currency}{amount}" for category, amount in expenses.items()])
    total_expenses = sum(expenses.values())
    net_income = income - total_expenses
    
    return f"""
    You are LefiBot, a professional financial assistant. Analyze the budget and provide a concise summary.
    Budget:
    - Monthly Income: {currency}{income:,.2f}
    - Expenses:
    {expense_details}
    - Total Monthly Expenses: {currency}{total_expenses:,.2f}
    - Net Income: {currency}{net_income:,.2f}

    Respond in a clean JSON format with two keys: "summary_text" and "top_categories".
    - "summary_text": A markdown-formatted string with a heading "### AI Summary & Tips" containing:
        1. A sentence on overall financial health.
        2. One practical tip for improvement.
    - "top_categories": A list of the top 2-3 spending categories as strings.
    
    JSON Output:
    """

def build_chatbot_prompt(user_query: str) -> str:
    """Builds a prompt for the general finance chatbot."""
    return f"""
    You are LefiBot, a helpful and professional financial assistant. Answer the user's personal finance question clearly, concisely, and in a friendly manner.
    User's Question: "{user_query}"
    """
    
def build_nlu_prompt(text: str) -> str:
    """Builds an advanced prompt for NLU analysis."""
    return f"""
    Analyze the following text for advanced Natural Language Understanding insights.
    Provide the output in a clean JSON format with the following keys:
    - 'sentiment': A string ('positive', 'negative', or 'neutral').
    - 'sentiment_score': A float between -1.0 (very negative) and 1.0 (very positive).
    - 'emotion': A single dominant emotion detected in the text (e.g., 'stress', 'joy', 'concern', 'optimism').
    - 'intent': The user's primary goal (e.g., 'seeking advice', 'expressing frustration', 'querying data', 'budget_analysis', 'investment_planning').
    - 'summary': A concise, one-sentence summary of the text.
    - 'keywords': A list of up to 5 most important keywords.
    - 'entities': A list of named entities.

    Text to analyze: "{text}"
    JSON Output:
    """

def build_expense_extraction_prompt(text: str) -> str:
    """Builds a prompt to extract key-value pairs for expenses from a text."""
    return f"""
    Extract financial expense data from the following text and return it as a JSON object.
    The keys should be the expense categories (e.g., "rent", "groceries", "transport") and the values should be the numerical amounts.
    If multiple amounts are found for the same category, sum them up.
    
    Example:
    Text: "My rent is 15000, and I spend 8000 on groceries."
    Output: {{ "Rent": 15000, "Groceries": 8000 }}

    Text: "{text}"
    JSON Output:
    """

def build_spending_insight_prompt(income: float, expenses: dict, goals: list, currency: str) -> str:
    """Builds a prompt for deep spending insights."""
    expense_details = "\n".join([f"- {category.capitalize()}: {currency}{amount}" for category, amount in expenses.items()])
    goal_details = "\n".join([f"- {goal['name']}: {currency}{goal['cost']} (Deadline: {goal['deadline_months']} months)" for goal in goals]) if goals else "No specific goals provided."
    total_expenses = sum(expenses.values())
    surplus = income - total_expenses
    
    return f"""
    Perform a deep financial analysis based on the data below. Provide structured, actionable insights.

    User Financial Profile:
    - Monthly Income: {currency}{income}
    - Monthly Expenses:
    {expense_details}
    - Future Goals:
    {goal_details}
    - Calculated Monthly Surplus (after expenses): {currency}{surplus}

    Generate a detailed report in a clean JSON format with the following keys:
    - "executive_summary": A concise markdown paragraph summarizing their financial health.
    - "spending_breakdown": A markdown string categorizing expenses into Fixed vs. Variable.
    - "needs_vs_wants": A markdown string classifying expenses into Needs vs. Wants.
    - "red_flags": A markdown string identifying potential budgetary risks.
    - "goal_feasibility": A markdown string analyzing if goals are on track.
    - "recommendations": A markdown string with the top 3 actionable recommendations.
    
    JSON Output:
    """

def build_investment_prompt(current_savings: float, monthly_investment: float, years_to_goal: int, risk_tolerance: str, currency: str) -> str:
    """Builds a detailed prompt for an investment plan."""
    return f"""
    You are a Certified Financial Planner (CFP) AI. Based on the user's data, generate a comprehensive investment plan.
    User's Financial Profile:
    - Current Savings: {currency}{current_savings:,.2f}
    - Monthly Investment: {currency}{monthly_investment:,.2f}
    - Years to Investment Goal: {years_to_goal} years
    - Risk Tolerance: {risk_tolerance}

    Provide the response in a single, structured JSON format with the following keys:
    - "summary": A markdown-formatted paragraph providing a high-level overview of the plan.
    - "portfolio_breakdown": A list of JSON objects, each with 'asset' (e.g., "Stocks", "Bonds", "Crypto") and 'percentage'.
    - "projected_growth": A list of JSON objects representing a hypothetical growth path, each with 'year' and 'value'. The projection should be conservative, assuming a realistic average annual return for the given risk tolerance. Include a comment in your JSON about the assumed annual return rate.
    - "action_plan": A markdown-formatted list of 3-5 actionable steps the user should take.
    
    JSON Output:
    """

# --- 3. UI RENDERING FUNCTIONS ---

def apply_styles():
    """Applies custom CSS for a professional dark mode look with attractive colors."""
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');
            
            :root {{
                --primary-color: #009688; /* Teal */
                --secondary-color: #80CBC4; /* Light Teal */
                --background-color: #0B1F33; /* Dark Navy */
                --card-color: #1A334A; /* Dark Teal */
                --text-color: #E0E0E0; /* Light Gray */
                --border-color: #3A536B; /* Muted Blue */
                --bubble-bot: #2B4C69; /* Muted Dark Blue */
                --bubble-user: #1A334A;
                --hover-color: #25455E;
            }}

            html, body, [data-testid="stAppViewContainer"] {{
                background-color: var(--background-color);
                color: var(--text-color);
                font-family: 'Poppins', sans-serif;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: var(--secondary-color);
            }}

            /* Sidebar */
            [data-testid="stSidebar"] {{
                background-color: var(--card-color);
                border-right: 1px solid var(--border-color);
            }}
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
                color: var(--text-color) !important;
            }}
            
            /* Main Content Area */
            .content-card {{
                background-color: var(--card-color);
                padding: 25px;
                border-radius: 10px;
                border: 1px solid var(--border-color);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }}
            
            .header {{
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: #FFFFFF;
                padding: 20px 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid var(--primary-color);
                box-shadow: 0 4px 20px rgba(0, 150, 136, 0.4);
            }}
            .header .title-block {{ display: flex; align-items: center; }}
            .header .title-block h1 {{ 
                font-size: 2.5rem; 
                margin: 0; 
                padding: 0 0 0 15px; 
                color: #FFFFFF; 
                font-weight: 600;
            }}
            .header .time-block {{ text-align: right; }}
            .header .time-block #greeting {{ font-size: 1.1rem; font-weight: 500; margin: 0; color: #B0BEC5;}}
            .header .time-block #clock {{ font-size: 1.5rem; font-weight: 600; margin: 0; color: #FFFFFF; letter-spacing: 1px;}}
            
            /* Chat Bubbles */
            [data-testid="stChatMessage"] {{ 
                background-color: var(--bubble-user);
                border-radius: 18px 18px 0 18px;
                margin-bottom: 1rem;
            }}
            [data-testid="stChatMessageContent"] p {{ color: var(--text-color) !important; }}
            [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {{ padding: 10px; }}

            .stChatMessage.st-chat-message-assistant div[data-testid="stMarkdownContainer"] {{ 
                background-color: var(--bubble-bot); 
                color: white; 
                border-radius: 18px 18px 18px 0; 
                margin-right: 20px;
                padding: 15px;
            }}
            .stChatMessage.st-chat-message-user div[data-testid="stMarkdownContainer"] {{ 
                background-color: var(--bubble-user); 
                border-radius: 18px 18px 0 18px; 
                margin-left: 20px;
                padding: 15px;
            }}
            .stChatMessage .avatar-img {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }}
            
            /* Buttons and Inputs */
            .stButton>button {{ 
                background-color: var(--primary-color); 
                color: white; 
                border: none;
                border-radius: 8px; 
                padding: 12px 20px;
                font-size: 1rem;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .stButton>button:hover {{ 
                background-color: var(--secondary-color); 
                transform: scale(1.01); /* Reduced scale */
                box-shadow: 0 0 8px rgba(128, 203, 196, 0.6); /* Reduced brightness */
            }}
            
            .stTextInput>div>div>input {{
                background-color: var(--card-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
            }}

            /* Option Menu Tabs */
            .st-emotion-cache-1h9usn1 summary {{ font-weight: bold; }}
            .st-emotion-cache-121rnhd, .st-emotion-cache-1k4w167 {{
                background-color: var(--background-color) !important;
                border-bottom: 2px solid var(--primary-color) !important;
            }}
            .st-emotion-cache-1k4w167 a {{
                color: var(--text-color);
                font-size: 1rem;
                transition: transform 0.3s, color 0.3s;
            }}
            .st-emotion-cache-1k4w167 a:hover {{
                transform: scale(1.02); /* Reduced scale */
                color: var(--secondary-color);
            }}
            .st-emotion-cache-1k4w167 a.selected {{
                background-color: var(--primary-color);
                color: white;
                transform: scale(1.02); /* Reduced scale */
                box-shadow: 0 0 8px rgba(0, 150, 136, 0.6); /* Reduced brightness */
                border-radius: 8px;
            }}

            /* Tags */
            .tag {{
                display: inline-block;
                padding: 0.25em 0.6em;
                font-size: 0.85em;
                font-weight: 700;
                line-height: 1;
                text-align: center;
                white-space: nowrap;
                vertical-align: baseline;
                border-radius: 0.25rem;
                color: #fff;
                background-color: var(--primary-color);
                margin: 0.1rem;
            }}
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Renders the advanced, dynamic application header."""
    st.markdown("""
        <div class='header'>
            <div class='title-block'>
                <span style='font-size: 2.5rem; margin: 0; animation: pulse 2s infinite; border-radius: 50%;'>✨</span>
                <h1>LefiBot</h1>
            </div>
            <div class='time-block'>
                <p id='greeting'></p>
                <p id='clock'></p>
            </div>
        </div>

        <script>
            function updateClock() {
                const now = new Date();
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');
                document.getElementById('clock').textContent = `${hours}:${minutes}:${seconds}`;

                const hour = now.getHours();
                let greeting = 'Good Evening!';
                if (hour < 12) {
                    greeting = 'Good Morning!';
                } else if (hour < 18) {
                    greeting = 'Good Afternoon!';
                }
                document.getElementById('greeting').textContent = greeting;
            }
            setInterval(updateClock, 1000);
            updateClock(); 
        </script>
    """, unsafe_allow_html=True)

def render_footer():
    """Renders the application footer."""
    st.markdown("<hr style='border-color:var(--border-color)'><p style='text-align: center; color: #495057;'>LefiBot</p>", unsafe_allow_html=True)

def display_currency_results(data, from_currency, to_currency, amount, is_historical, lookup_date):
    """Renders the results of a currency conversion."""
    if not isinstance(data, dict) or "real_time" not in data:
        st.warning("The AI response did not contain the expected structure. Please try again.")
        return

    st.success("Data retrieved successfully! ✅")
    
    # Display Real-time conversion safely
    st.subheader("Real-Time Conversion 🟢")
    rt_data = data.get('real_time', {})
    explanation = rt_data.get('explanation', 'Explanation not available.')
    converted_amount = rt_data.get('converted_amount')

    if converted_amount is not None:
        st.markdown(f"<div style='background-color: var(--bubble-bot); padding: 20px; border-radius: 10px; border: 1px solid var(--border-color);'><h3 style='text-align: center; color: var(--text-color);'>{explanation}</h3><h2 style='text-align: center; color: var(--text-color);'>{amount:,.2f} {from_currency.upper()} = <span style='color: var(--secondary-color);'>{converted_amount:,.2f} {to_currency.upper()}</span></h2></div>", unsafe_allow_html=True)
    else:
        st.warning("The AI's response for the real-time conversion was incomplete. Please try again or adjust your query.")

    # Display Historical conversion safely
    if is_historical and lookup_date and data.get("historical_rate"):
        st.subheader(f"Historical Rate for {lookup_date.strftime('%B %d, %Y')} 🕰️")
        hist_data = data['historical_rate']
        hist_explanation = hist_data.get('explanation', 'Explanation not available.')
        hist_converted_amount = hist_data.get('converted_amount')
        
        if hist_converted_amount is not None:
            st.markdown(f"<div style='background-color: var(--bubble-bot); padding: 20px; border-radius: 10px; border: 1px solid var(--border-color);'><h3 style='text-align: center; color: var(--text-color);'>{hist_explanation}</h3><h2 style='text-align: center; color: var(--text-color);'>{amount:,.2f} {from_currency.upper()} = <span style='color: var(--secondary-color);'>{hist_converted_amount:,.2f} {to_currency.upper()}</span></h2></div>", unsafe_allow_html=True)
        else:
            st.warning("Historical conversion data was incomplete in the AI response.")

    # Display 30-day trend chart safely
    trend_data = data.get("historical_trend")
    if trend_data:
        st.subheader("30-Day Exchange Rate Trend 📈")
        try:
            if isinstance(trend_data, list) and all(isinstance(i, dict) for i in trend_data):
                df = pd.DataFrame(trend_data)
                if 'date' in df.columns and 'rate' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df.dropna(subset=['date'], inplace=True)
                    df.set_index('date', inplace=True)
                    st.line_chart(df['rate'], use_container_width=True)
                else:
                    st.warning("Trend data was missing 'date' or 'rate' columns.")
            else:
                st.warning("Trend data is not in the expected list format.")
        except Exception as chart_error:
            st.warning(f"Could not display trend chart: {chart_error}")

def render_currency_converter():
    st.header("💸 Advanced Currency Converter")
    with st.container(border=True):
        
        session_inputs = {
            'from_currency': 'USD', 'to_currency': 'INR', 'amount': 100.0,
            'is_historical': False, 'lookup_date': date.today() - timedelta(days=1)
        }
        active_session_outputs = None
        current_id = st.session_state.get('current_tool_id')
        if current_id and current_id in st.session_state.tool_sessions:
            session = st.session_state.tool_sessions[current_id]
            if session.get('tool_type') == '💸 Currency Converter':
                session_inputs = session['inputs']
                active_session_outputs = session['outputs']
        
        currency_list = list(CURRENCIES.keys())
        def format_currency(code):
            return f"{code} - {CURRENCIES.get(code, 'Unknown Currency')}"

        col1, col2, col3 = st.columns(3)
        with col1:
            from_currency = st.selectbox("From Currency", options=currency_list, 
                                         index=currency_list.index(session_inputs['from_currency']),
                                         format_func=format_currency)
        with col2:
            to_currency = st.selectbox("To Currency", options=currency_list,
                                         index=currency_list.index(session_inputs['to_currency']),
                                         format_func=format_currency)
        with col3:
            amount = st.number_input("Amount", min_value=0.01, value=session_inputs['amount'], step=1.0)

        is_historical = st.toggle("Look up historical rate?", value=session_inputs['is_historical'])
        lookup_date = None
        if is_historical:
            lookup_date = st.date_input("Select a date", value=session_inputs['lookup_date'], 
                                         max_value=date.today() - timedelta(days=1))

        if st.button("➤ Convert", use_container_width=True):
            if not from_currency or not to_currency or not amount:
                st.warning("Please fill in all currency fields.")
            else:
                # Use the new function to get the real-time rate
                real_time_rate = get_real_time_exchange_rate(from_currency, to_currency)
                if real_time_rate is None:
                    # If real-time rate couldn't be fetched, display an error and stop
                    st.error("Could not retrieve real-time exchange rate. Please check your internet connection and try again.")
                    return

                with st.spinner("Fetching financial data... This may take a moment."):
                    try:
                        # Pass the real-time rate to the AI for analysis
                        prompt = build_advanced_currency_prompt(from_currency, to_currency, amount, real_time_rate, lookup_date if is_historical else None)
                        response = safe_generate_content(llm, prompt)
                        if response:
                            raw_text = response.text
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
                            if not json_match:
                                raise json.JSONDecodeError("No valid JSON found in the AI response.", raw_text, 0)
                            
                            json_str = json_match.group(1)
                            data = json.loads(json_str)

                            tool_id = f"tool_{time.time()}"
                            title = f"Conv: {amount} {from_currency}→{to_currency}"
                            st.session_state.tool_sessions[tool_id] = {
                                "title": title,
                                "tool_type": "💸 Currency Converter", # Fixed inconsistency
                                "inputs": {'from_currency': from_currency, 'to_currency': to_currency, 'amount': amount,
                                           'is_historical': is_historical, 'lookup_date': lookup_date},
                                "outputs": data
                            }
                            st.session_state.current_tool_id = tool_id
                            
                            display_currency_results(data, from_currency, to_currency, amount, is_historical, lookup_date)
                        
                    except json.JSONDecodeError:
                        st.error("Error: The AI response was not in a valid JSON format. Please try again.")
                        st.code(raw_text, language="text")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
        
        elif active_session_outputs:
            display_currency_results(active_session_outputs, **session_inputs)

def render_budget_summarizer():
    st.header("📈 Budget Analyzer")
    with st.container(border=True):
        income = st.number_input("Your Monthly Income (e.g., 50000)", min_value=0.0, value=st.session_state.get('prefill_income', 50000.0), step=1000.0)
        expenses_input = st.text_area("Your Monthly Expenses (e.g., Rent: 15000, Groceries: 8000)", st.session_state.get('prefill_expenses', "Rent: 15000, Groceries: 8000, Transport: 3000, Entertainment: 4000"), height=150)
        currency_symbol = st.text_input("Currency Symbol", "₹")

        # Clear pre-fill data after it's used
        if 'prefill_expenses' in st.session_state:
            del st.session_state.prefill_expenses
        if 'prefill_income' in st.session_state:
            del st.session_state.prefill_income

        if st.button("➤ Analyze Budget", use_container_width=True):
            if not income or not expenses_input:
                st.warning("Please provide both income and expenses.")
            else:
                with st.spinner("Analyzing your budget..."):
                    try:
                        expenses = {key.strip(): float(value.strip()) for item in expenses_input.split(',') if ':' in item for key, value in [item.split(':', 1)]}
                        prompt = build_budget_summary_prompt(income, expenses, currency_symbol)
                        response = safe_generate_content(llm, prompt)
                        if response:
                            raw_text = response.text
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
                            json_str = json_match.group(1) if json_match else raw_text
                            data = json.loads(json_str)

                            tool_id = f"tool_{time.time()}"
                            title = "Budget Analysis"
                            st.session_state.tool_sessions[tool_id] = {
                                "title": title,
                                "tool_type": "📈 Budget Analyzer", # Fixed inconsistency
                                "inputs": {'income': income, 'expenses': expenses, 'currency': currency_symbol},
                                "outputs": data
                            }
                            st.session_state.current_tool_id = tool_id

                            st.success("Budget Analysis Complete! 🎉")
                            
                            total_expenses = sum(expenses.values())
                            net_income = income - total_expenses

                            col1, col2, col3 = st.columns(3)
                            col1.metric("Total Income", f"{currency_symbol}{income:,.2f}")
                            col2.metric("Total Expenses", f"{currency_symbol}{total_expenses:,.2f}")
                            col3.metric("Net Savings", f"{currency_symbol}{net_income:,.2f}", delta=f"{net_income/income:.1%}" if income > 0 else "N/A")

                            st.markdown("---")

                            col1, col2 = st.columns([2,1])
                            with col1:
                                if expenses:
                                    fig = px.pie(values=expenses.values(), names=expenses.keys(), title="Expense Breakdown", hole=0.3)
                                    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='var(--text-color)', font_family='Poppins')
                                    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(colors=px.colors.sequential.Tealgrn))
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            with col2:
                                    st.markdown(data.get("summary_text", "AI summary could not be generated."))
                                
                    except Exception as e:
                        st.error(f"An error occurred while analyzing the budget: {e}")

def render_nlu_analysis():
    st.header("🧠 Advanced NLU Analysis")
    with st.container(border=True):
        text_input = st.text_area("Enter text for analysis:", "I'm feeling stressed about my high spending on groceries this month and need to find a way to save more money for my vacation.", height=150)
        if st.button("➤ Analyze Text", use_container_width=True):
            with st.spinner("Analyzing..."):
                try:
                    prompt = build_nlu_prompt(text_input)
                    response = safe_generate_content(llm, prompt)
                    if response:
                        raw_text = response.text
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
                        json_str = json_match.group(1) if json_match else raw_text
                        data = json.loads(json_str)

                        tool_id = f"tool_{time.time()}"
                        title = "NLU Analysis"
                        st.session_state.tool_sessions[tool_id] = {
                            "title": title,
                            "tool_type": "🧠 NLU Analysis", # Added session tracking for NLU
                            "inputs": {'text_input': text_input},
                            "outputs": data
                        }
                        st.session_state.current_tool_id = tool_id
                        
                        st.success("Analysis Complete! 🔬")

                        st.markdown(f"**Summary:** *{data.get('summary', 'N/A')}*")
                        st.markdown("---")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Sentiment")
                            sentiment = data.get('sentiment', 'N/A').capitalize()
                            sentiment_score = data.get('sentiment_score', 0.0)
                            
                            progress_value = int((sentiment_score + 1) * 50)
                            st.progress(progress_value)
                            st.markdown(f"**{sentiment}** (Score: {sentiment_score:.2f})")

                        with col2:
                            st.subheader("Emotion & Intent")
                            st.metric("Detected Emotion", data.get('emotion', 'N/A').capitalize())
                            st.metric("User Intent", data.get('intent', 'N/A').capitalize())
                        
                        st.markdown("---")

                        if data.get('keywords'):
                            st.subheader("Keywords 🔑")
                            keywords_html = "".join([f"<span class='tag'>{kw}</span>" for kw in data['keywords']])
                            st.markdown(keywords_html, unsafe_allow_html=True)
                        
                        if data.get('entities'):
                            st.subheader("Entities 👤")
                            entities_html = "".join([f"<span class='tag'>{ent}</span>" for ent in data['entities']])
                            st.markdown(entities_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"An error occurred: {e}")

def render_spending_insights():
    st.header("🔮 Advanced Spending Insights")
    with st.container(border=True):
        income = st.number_input("Monthly Income", min_value=0.0, value=60000.0, step=1000.0)
        expenses_input = st.text_area("Monthly Expenses (e.g., Rent: 20000, Groceries: 10000)", "Rent: 20000, Groceries: 10000, Transport: 5000, Entertainment: 5000", height=150)
        goals_input = st.text_area("Future Goals (e.g., Vacation: 50000 (6 months))", "Vacation: 50000 (6 months), New Phone: 80000 (12 months)", height=100)
        currency = st.text_input("Currency Symbol", "₹")

        if st.button("➤ Get Insights", use_container_width=True):
            with st.spinner("Generating deep insights..."):
                try:
                    expenses = {key.strip(): float(value.strip()) for item in expenses_input.split(',') if ':' in item for key, value in [item.split(':', 1)]}
                    
                    goals = []
                    malformed_goals = []
                    if goals_input.strip():
                        for item in goals_input.split(','):
                            if ':' in item and '(' in item and ')' in item:
                                try:
                                    name_part, rest_part = item.split(':', 1)
                                    cost_part, deadline_part = rest_part.split('(', 1)
                                    deadline_match = re.search(r'(\d+)', deadline_part)
                                    if deadline_match:
                                        goals.append({
                                            "name": name_part.strip(),
                                            "cost": float(cost_part.strip()),
                                            "deadline_months": int(deadline_match.group(1))
                                        })
                                    else:
                                        malformed_goals.append(item.strip())
                                except (ValueError, IndexError):
                                    malformed_goals.append(item.strip())
                            else:
                                if item.strip():
                                    malformed_goals.append(item.strip())

                    if malformed_goals:
                        st.warning(f"The following goals were ignored due to incorrect formatting: `{', '.join(malformed_goals)}`")
                        st.info("Please use the format: `Goal Name: Cost (Deadline months)`")

                    prompt = build_spending_insight_prompt(income, expenses, goals, currency)
                    response = safe_generate_content(llm, prompt)
                    if response:
                        raw_text = response.text
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
                        json_str = json_match.group(1) if json_match else raw_text
                        data = json.loads(json_str)

                        tool_id = f"tool_{time.time()}"
                        title = "Spending Insights"
                        st.session_state.tool_sessions[tool_id] = {
                            "title": title,
                            "tool_type": "🔮 Spending Insights", # Fixed inconsistency
                            "inputs": {'income': income, 'expenses': expenses, 'goals': goals, 'currency': currency},
                            "outputs": data
                        }
                        st.session_state.current_tool_id = tool_id
                        
                        st.success("Insights Generated! 🚀")

                        total_expenses = sum(expenses.values())
                        surplus = income - total_expenses

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Income", f"{currency}{income:,.2f}")
                        col2.metric("Total Expenses", f"{currency}{total_expenses:,.2f}")
                        col3.metric("Monthly Surplus", f"{currency}{surplus:,.2f}")

                        st.markdown(data.get("executive_summary", ""))

                        if goals:
                            st.subheader("Goal Tracking 🎯")
                            for goal in goals:
                                months_needed = (goal['cost'] / surplus) if surplus > 0 else float('inf')
                                progress = min(100, (goal['deadline_months'] / months_needed * 100) if months_needed > 0 else 100)
                                st.markdown(f"**{goal['name']}**")
                                st.progress(int(progress))
                                if months_needed > goal['deadline_months']:
                                    st.error(f"At risk: Needs {months_needed:.1f} months, but deadline is {goal['deadline_months']} months.")
                                else:
                                    st.success(f"On track: Needs {months_needed:.1f} months for a {goal['deadline_months']}-month goal.")
                        
                        st.subheader("Detailed Analysis 📊")
                        with st.expander("Spending Breakdown (Fixed vs. Variable)", expanded=True):
                            st.markdown(data.get("spending_breakdown", "N/A"))
                        with st.expander("Needs vs. Wants Analysis", expanded=True):
                            st.markdown(data.get("needs_vs_wants", "N/A"))
                        with st.expander("Budgetary Red Flags", expanded=True):
                            st.markdown(data.get("red_flags", "N/A"))
                        with st.expander("Goal Feasibility Details", expanded=True):
                            st.markdown(data.get("goal_feasibility", "N/A"))
                        with st.expander("Top 3 Recommendations", expanded=True):
                            st.markdown(data.get("recommendations", "N/A"))

                except Exception as e:
                    st.error(f"An error occurred while generating insights: {e}")

def render_investment_planner():
    st.header("✨ AI Investment Planner")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            current_savings = st.number_input("Current Savings", min_value=0.0, value=25000.0, step=1000.0)
            monthly_investment = st.number_input("Monthly Investment", min_value=0.0, value=5000.0, step=500.0)
        with col2:
            years_to_goal = st.slider("Years to Goal", min_value=1, max_value=40, value=10)
            risk_tolerance = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"])
        
        currency = st.text_input("Currency Symbol", "₹")

        if st.button("➤ Generate Plan", use_container_width=True):
            if not current_savings and not monthly_investment:
                st.warning("Please enter your current savings or a monthly investment amount.")
                return

            with st.spinner("Generating personalized investment plan..."):
                try:
                    prompt = build_investment_prompt(current_savings, monthly_investment, years_to_goal, risk_tolerance, currency)
                    response = safe_generate_content(llm, prompt)
                    if response:
                        raw_text = response.text
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
                        json_str = json_match.group(1) if json_match else raw_text
                        data = json.loads(json_str)

                        tool_id = f"tool_{time.time()}"
                        title = "Investment Plan"
                        st.session_state.tool_sessions[tool_id] = {
                            "title": title,
                            "tool_type": "✨ Investment Planner", # Fixed inconsistency
                            "inputs": {'current_savings': current_savings, 'monthly_investment': monthly_investment, 'years_to_goal': years_to_goal, 'risk_tolerance': risk_tolerance, 'currency': currency},
                            "outputs": data
                        }
                        st.session_state.current_tool_id = tool_id
                        
                        st.success("Plan Generated! 💰")
                        
                        st.subheader("Executive Summary")
                        st.markdown(data.get("summary", "N/A"))

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Recommended Portfolio Breakdown")
                            portfolio_data = data.get("portfolio_breakdown")
                            if portfolio_data:
                                portfolio_df = pd.DataFrame(portfolio_data)
                                fig = px.pie(portfolio_df, values='percentage', names='asset', title="Asset Allocation", hole=0.4)
                                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='var(--text-color)', font_family='Poppins')
                                fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(colors=px.colors.sequential.Tealgrn))
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Portfolio breakdown data is missing.")

                        with col2:
                            st.subheader("Projected Growth Over Time")
                            growth_data = data.get("projected_growth")
                            if growth_data:
                                growth_df = pd.DataFrame(growth_data)
                                fig = px.line(growth_df, x='year', y='value', title="Hypothetical Account Value", markers=True)
                                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='var(--text-color)', font_family='Poppins')
                                # Fixed the color reference to a hardcoded value that matches the app's theme.
                                fig.update_traces(line=dict(color='#80CBC4'), marker=dict(color='#80CBC4'))
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Projected growth data is missing.")
                        
                        st.markdown("---")
                        st.subheader("Action Plan")
                        st.markdown(data.get("action_plan", "N/A"))
                        
                except Exception as e:
                    st.error(f"An error occurred while generating the investment plan: {e}")
                    st.code(raw_text, language="text")


def render_chatbot():
    st.header("🗨️ Chat with LefiBot")
    chat_container = st.container()
    with chat_container:
        # Check if the current chat session exists, if not, re-initialize it
        if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chat_sessions:
            new_chat_id = f"chat_{time.time()}"
            st.session_state.current_chat_id = new_chat_id
            st.session_state.chat_sessions[new_chat_id] = {
                "title": "New Chat",
                "messages": [{"role": "assistant", "content": "Hello! I'm LefiBot. How can I help with your finances today?"}]
            }
        
        current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
        
        for message in current_chat["messages"]:
            if message["role"] == "assistant":
                with st.chat_message(message["role"], avatar="https://image.similarpng.com/file/similarpng/very-thumbnail/2021/08/Business-and-financial-logo-design-template-isolated-on-transparent-background-PNG.png"):
                    st.markdown(message["content"])
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    prompt = st.chat_input("Ask a finance question...")
    
    if prompt:
        current_chat["messages"].append({"role": "user", "content": prompt})
        
        if current_chat["title"] == "New Chat":
            current_chat["title"] = prompt[:40] + "..." if len(prompt) > 40 else prompt

        # Perform NLU to check for redirection
        with st.spinner("Analyzing your request..."):
            try:
                nlu_response = safe_generate_content(llm, build_nlu_prompt(prompt))
                if nlu_response:
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', nlu_response.text, re.DOTALL)
                    nlu_data = json.loads(json_match.group(1)) if json_match else {}
                    
                    intent = nlu_data.get('intent')
                    emotion = nlu_data.get('emotion')
                    
                    if intent == 'budget_analysis' and emotion in ['stress', 'concern']:
                        with st.chat_message("assistant", avatar="https://image.similarpng.com/file/similarpng/very-thumbnail/2021/08/Business-and-financial-logo-design-template-isolated-on-transparent-background-PNG.png"):
                            st.markdown("It sounds like you're concerned about your finances. I can help with that!")
                            
                            # Extract expenses to pre-fill the tool
                            try:
                                expense_response = safe_generate_content(llm, build_expense_extraction_prompt(prompt))
                                if expense_response:
                                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', expense_response.text, re.DOTALL)
                                    expenses = json.loads(json_match.group(1)) if json_match else {}
                                    prefilled_expenses_str = ", ".join([f"{key}: {value}" for key, value in expenses.items()])
                                    st.session_state.prefill_expenses = prefilled_expenses_str
                            except (json.JSONDecodeError, AttributeError):
                                st.warning("Could not extract specific numbers, but I can still redirect you.")
                                st.session_state.prefill_expenses = "Rent: 0, Groceries: 0" # Fallback

                            st.markdown("Would you like to analyze your spending with our **Budget Analyzer** tool? We can get started right away.")
                            if st.button("Go to Budget Analyzer"):
                                st.session_state.active_tool_selection = "📈 Budget Analyzer"
                                st.session_state.current_tool_id = None
                                st.session_state.selected = "Financial Tools"
                                st.rerun()
                            
                            # Return to stop further chat processing
                            return

                    elif intent == 'investment_planning':
                        with st.chat_message("assistant", avatar="https://image.similarpng.com/file/similarpng/very-thumbnail/2021/08/Business-and-financial-logo-design-template-isolated-on-transparent-background-PNG.png"):
                            st.markdown("That's a great question! I can help you with investment planning.")
                            st.markdown("Would you like to use our **AI Investment Planner** tool?")
                            if st.button("Go to Investment Planner"):
                                st.session_state.active_tool_selection = "✨ Investment Planner"
                                st.session_state.current_tool_id = None
                                st.session_state.selected = "Financial Tools"
                                st.rerun()
                            return
            
            except (json.JSONDecodeError, AttributeError):
                pass # Continue to regular chat if NLU fails
        
        # If no redirection, proceed with normal chatbot response
        with st.spinner("LefiBot is thinking..."):
            try:
                response = safe_generate_content(llm, build_chatbot_prompt(prompt))
                if response:
                    assistant_response = response.text
                    current_chat["messages"].append({"role": "assistant", "content": assistant_response})
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {e}"
                current_chat["messages"].append({"role": "assistant", "content": error_message})
        st.rerun()

# --- 4. MAIN APPLICATION LOGIC ---

def main():
    st.set_page_config(page_title="LefiBot Finance Tools", layout="wide")
    apply_styles()
    
    # Initialize session state for all history
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
        new_chat_id = f"chat_{time.time()}"
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_sessions[new_chat_id] = {
            "title": "New Chat",
            "messages": [{"role": "assistant", "content": "Hello! I'm LefiBot. How can I help with your finances today? I can help you with anything from budgeting to investment planning."}]
        }
    if "tool_sessions" not in st.session_state:
        st.session_state.tool_sessions = {}
    if "current_tool_id" not in st.session_state:
        st.session_state.current_tool_id = None
    
    if "selected" not in st.session_state:
        st.session_state.selected = "Chat with LefiBot"
    if "active_tool_selection" not in st.session_state:
        st.session_state.active_tool_selection = "💸 Currency Converter"

    # Sidebar Navigation
    with st.sidebar:
        st.image("https://marketplace.canva.com/EAGQZhT83lg/1/0/1600w/canva-dark-green-modern-illustrative-finance-service-logo-GTKa2Yxea4Y.jpg", width=80) 
        st.markdown("<h1 style='font-size: 1.8rem; text-align: center;'>LefiBot</h1>", unsafe_allow_html=True)
        
        with st.container():
            selected = option_menu(
                menu_title=None,
                options=["Chat with LefiBot", "Financial Tools"],
                icons=['chat-dots-fill', 'tools'],
                menu_icon="cast",
                default_index=["Chat with LefiBot", "Financial Tools"].index(st.session_state.selected),
                styles={
                    "container": {"padding": "0!important", "background-color": "#1E1E1E"},
                    "icon": {"color": "#E0E0E0", "font-size": "20px"},
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#2C3E50"},
                    "nav-link-selected": {"background-color": "#00796B"},
                }
            )
        
        st.markdown("---")

        if selected == "Chat with LefiBot":
            # Clear Chat History button
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_sessions = {}
                new_chat_id = f"chat_{time.time()}"
                st.session_state.current_chat_id = new_chat_id
                st.session_state.chat_sessions[new_chat_id] = {
                    "title": "New Chat",
                    "messages": [{"role": "assistant", "content": "Hello! I'm LefiBot. How can I assist you with your finances?"}]
                }
                st.rerun()

            st.markdown("##### Recent Chats")
            chat_ids = list(st.session_state.chat_sessions.keys())
            # Show only the last 5 chats
            for chat_id in chat_ids[-5:]:
                chat_title = st.session_state.chat_sessions[chat_id]["title"]
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    if st.button(chat_title, key=f"select_{chat_id}", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        st.session_state.selected = "Chat with LefiBot"
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{chat_id}", use_container_width=True):
                        del st.session_state.chat_sessions[chat_id]
                        # If the deleted chat was the current one, switch to a new chat
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[-1] if st.session_state.chat_sessions else f"chat_{time.time()}"
                        st.rerun()
        
        tool_selection = None
        if selected == "Financial Tools":
            with st.expander("Financial Toolkit", expanded=True):
                tool_selection = st.radio(
                    "Select a Tool",
                    ["💸 Currency Converter", "📈 Budget Analyzer", "🧠 NLU Analysis", "🔮 Spending Insights", "✨ Investment Planner"],
                    key="tool_selector",
                    index=["💸 Currency Converter", "📈 Budget Analyzer", "🧠 NLU Analysis", "🔮 Spending Insights", "✨ Investment Planner"].index(st.session_state.active_tool_selection),
                    label_visibility="collapsed"
                )
            st.markdown("---")
            # Clear Tool History button
            if st.button("🗑️ Clear Tool History", use_container_width=True):
                st.session_state.tool_sessions = {}
                st.session_state.current_tool_id = None
                st.rerun()

            st.markdown("##### Recent Searches")
            if not st.session_state.tool_sessions:
                st.caption("No recent tool usage.")
            for tool_id in reversed(list(st.session_state.tool_sessions.keys())):
                session = st.session_state.tool_sessions[tool_id]
                if st.button(session['title'], key=f"history_{tool_id}", use_container_width=True):
                    st.session_state.current_tool_id = tool_id
                    st.session_state.selected = "Financial Tools"
                    st.session_state.active_tool_selection = session['tool_type']
                    st.rerun()

        st.info("This app uses AI for financial insights.")
        st.markdown("<p style='font-size: 0.8rem; text-align: center;'>LefiBot v9.0</p>", unsafe_allow_html=True)

    # Main content rendering
    render_header()

    if selected == "Financial Tools":
        if tool_selection:
            st.session_state.active_tool_selection = tool_selection
            st.session_state.selected = "Financial Tools"

            if "Converter" in tool_selection:
                render_currency_converter()
            elif "Analyzer" in tool_selection:
                render_budget_summarizer()
            elif "NLU" in tool_selection:
                render_nlu_analysis()
            elif "Insights" in tool_selection:
                render_spending_insights()
            elif "Planner" in tool_selection:
                render_investment_planner()
            render_footer()
    else: # Default to chatbot
        render_chatbot()

if __name__ == "__main__":
    main()
