# Bahai Life Coach Agent

A life coaching agent built with LangChain, incorporating Bahai principles and teachings to provide guidance and support.

## Features

- Personalized life coaching based on Bahai principles
- Goal setting and tracking
- Reflection prompts and guidance
- Personalized advice based on user inputs
- Conversation history for contextual responses
- Web-based chat interface for easy interaction
- Voice interaction mode using browser's Speech API
- Support for multiple LLM models including OpenAI, Google Gemini, and Deepseek
- Google Calendar and Tasks integration for time management

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and model configuration
   ```

## LLM Model Options

The application uses a model-centric approach, allowing you to specify which exact model you want to use without needing to know which provider it belongs to. Each model requires its corresponding API key to be set.

### Available Models

#### OpenAI Models
- `gpt-3.5-turbo` - Fast and cost-effective
- `gpt-4o` - Balanced performance and capability (default OpenAI model)
- `gpt-4-turbo` - More extensive and powerful

#### Google Gemini Models
- `gemini-pro` - Original Gemini model
- `gemini-1.5-pro` - Improved Gemini model with extended context
- `gemini-2.0-flash` - Latest fast Gemini model (default model)

#### Deepseek Models
- `deepseek-chat` - General purpose chat model
- `deepseek-coder` - Specialized for code generation
- `deepseek-reasoner` - Enhanced reasoning capabilities

### Configuration

Set your preferred model and corresponding API key in the `.env` file:

```
# Default model to use (will be used if not overridden by --model flag)
LLM_MODEL=gemini-2.0-flash

# You only need to set the API key for the model's provider that you plan to use
GEMINI_API_KEY=your_gemini_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here  
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

You can also specify the model when running the application:

```bash
python run_flask.py --model gpt-4o
```

### Setting Up Google Integration

The Bahai Life Coach agent can integrate with Google Calendar and Google Tasks to help manage your commitments:

1. Create a Google Cloud Project:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API and Google Tasks API

2. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Create an OAuth client ID (Application type: Desktop app)
   - Download the credentials as JSON
   - Rename the downloaded file to `credentials.json` and place it in the project root

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. On first use, the application will open a browser window asking you to authorize access to your Google account.

## Running the Application

### Web Interface (Recommended)

Run the web-based chat interface:

```bash
python run_flask.py
```

Then open your browser and navigate to:
```
http://localhost:5555
```

You can specify a different model:
```bash
python run_flask.py --model gpt-4o
```

Or a different port:
```bash
python run_flask.py --port 8080
```

### Console Interface (Alternative)

If you prefer a command-line interface:

```bash
python app/main.py
```

## Voice Interface

The web interface includes a voice interaction mode:

1. Click the microphone icon in the header to toggle voice mode
2. When active, you can speak your messages instead of typing
3. The agent's responses will be read aloud
4. The voice input will automatically timeout after 20 seconds of silence
5. Click the microphone icon again to disable voice mode

Note: Voice functionality requires a modern browser with Speech Recognition API support (Chrome, Edge, etc.).

## Google Integration Features

The Google integration allows the Bahai Life Coach agent to:

### Google Calendar
- Create events with specific date/time information
- Set up reminders for important tasks
- View upcoming events on your calendar
- Parse natural language time references (e.g., "tomorrow at 3pm")

### Google Tasks
- Create tasks with due dates
- View your existing tasks
- Mark tasks as completed
- Organize to-do items with priorities

### Using Google Integrations

During coaching sessions, you can:

1. Ask the agent to create calendar events:
   - "Schedule a meditation session for tomorrow at 6am"
   - "Add an event called 'Community Service' for Saturday at 10am"
   - "Remind me to call my friend Sarah on Friday"

2. Ask the agent about your schedule:
   - "What's on my calendar for today?"
   - "Do I have any events this weekend?"
   - "Show me my appointments for next week"

3. Create and manage tasks:
   - "Add a task to read Bahai writings before bed"
   - "Create a to-do item for grocery shopping by Sunday"
   - "What tasks do I have pending?"

The agent will detect these requests and automatically interface with Google's services to help manage your time and commitments.

### Testing Google Integration

To test the Google integration functionality:

```bash
python test_google_integration.py
```

This script will test the connection to Google services and verify that calendar events and tasks can be created and viewed.

## Project Structure

```
bahai-life-coach-agent/
├── app/
│   ├── agents/         # Agent definitions
│   ├── chains/         # LangChain chains
│   ├── config/         # Configuration files
│   ├── integrations/   # External service integrations
│   │   └── google/     # Google API integrations
│   ├── models/         # Model definitions
│   ├── prompts/        # Prompt templates
│   ├── utils/          # Utility functions
│   ├── web/            # Web interface files
│   │   ├── static/     # Static files (CSS, JS)
│   │   └── templates/  # HTML templates
│   ├── main.py         # Console application entry point
│   └── web_server.py   # Web server entry point
├── run_flask.py        # Flask server runner
├── test_google_integration.py # Test script for Google integration
├── credentials.json    # Google API credentials (download from Google Cloud Console)
├── token.json          # Google API tokens (auto-generated on first use)
├── .env                # Environment variables (git-ignored)
├── .env.example        # Example environment file
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## Troubleshooting

### Model Selection Issues
If you encounter issues with model selection:

1. Ensure you have set the correct API key for your selected model in `.env`
2. Try a different model with `--model` flag (e.g., `--model gemini-pro`)
3. Check that you have installed the required package for your model:
   - OpenAI models: `pip install langchain-openai`
   - Gemini models: `pip install langchain-google-genai`
   - Deepseek models: `pip install langchain-deepseek`

### HTTPS and Microphone Access
For microphone access in browsers, you may need to:

1. Access the app via HTTPS or localhost
2. Allow microphone permissions in your browser settings
3. Use a modern browser that supports the Web Speech API

### Google Integration Issues
If you encounter issues with the Google integration:

1. Make sure your `credentials.json` file is correctly placed in the project root
2. Check that you've enabled the required APIs in your Google Cloud Project
3. Try deleting the `token.json` file to reset authentication
4. Ensure you have the correct permissions on your Google account
5. Check your internet connection

## License

MIT 