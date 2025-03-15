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
- Support for OpenAI, local Ollama, and Hugging Face models
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

## API Options

### Using OpenAI API
Set your OpenAI API key in the `.env` file:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4.5-preview
```

### Using Free Local LLM with Ollama
To use Ollama's local LLM:

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model: `ollama pull llama3.2` (or any other model)
3. Configure your `.env` file:
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### Using Hugging Face Models
To use Hugging Face models:

1. Create a free account at [huggingface.co](https://huggingface.co/) and get an API key
2. Configure your `.env` file:
```
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.1
```
You can specify any model available on Hugging Face that supports text generation.

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
python app/web_server.py
```

Then open your browser and navigate to:
```
http://localhost:5555
```

### Simplified Web Server

If you encounter compatibility issues with the main web server, you can use the simplified version:

```bash
python simple_web_server.py
```

This simplified version provides the same functionality but with fewer dependencies and better compatibility with Ollama and Hugging Face.

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
├── simple_web_server.py # Simplified web server
├── test_ollama_direct.py # Test script for Ollama
├── test_huggingface.py  # Test script for Hugging Face
├── test_google_integration.py # Test script for Google integration
├── credentials.json    # Google API credentials (download from Google Cloud Console)
├── token.json          # Google API tokens (auto-generated on first use)
├── .env                # Environment variables (git-ignored)
├── .env.example        # Example environment file
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## Troubleshooting

### Compatibility Issues
If you encounter compatibility issues with the main web server, try:

1. Using the simplified web server: `python simple_web_server.py`
2. Ensuring you have the correct versions of dependencies in `requirements.txt`
3. For Ollama: Check that Ollama is running (`curl http://localhost:11434/api/version`)
4. For Hugging Face: Check your API key and model selection

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

## Testing Your Integration

### Testing Hugging Face Integration
Run the Hugging Face test script to verify your setup:
```bash
python test_huggingface.py
```

### Testing Ollama Integration
Test the Ollama connection with:
```bash
python test_ollama_direct.py
```

## Development

To add new features or modify the agent:

1. Update prompt templates in `app/prompts/`
2. Modify chains in `app/chains/`
3. Extend agent capabilities in `app/agents/`
4. Enhance the web interface in `app/web/`

## License

MIT 