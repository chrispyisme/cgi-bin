

# Set up your API key
export GEMINI_API_KEY="AIzaSyBT__Cloqy0Isd1qglB9_Y0g8ZEBQhT2SQ"

# Add to ~/.bashrc to persist
echo 'export GEMINI_API_KEY="AIzaSyBT__Cloqy0Isd1qglB9_Y0g8ZEBQhT2SQ"' >> ~/.bashrc
source ~/.bashrc

# Test it
python3 -c "import google.generativeai as genai; genai.configure(api_key='$GEMINI_API_KEY'); print('OK')"
