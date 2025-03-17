# Bahá'í Life Coach Application Architecture

TODO: hamburger menu not working. Remove all memory and fact processing. Excessive input tokens. Use ChatGPT for facts and commands and similar. Track difference in impacts.

This document provides a comprehensive overview of the Bahá'í Life Coach application's architecture, control flow, and logic. It details the application's key components, their interactions, and the flow of data throughout the system.

## 1. System Overview

The Bahá'í Life Coach is an ADHD-informed spiritual guide that provides coaching based on Bahá'í principles. It leverages large language models (LLMs) to generate personalized coaching responses, track conversation history, and maintain memory of important facts.

```
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│   Web UI     │◄────────►│   Flask API   │◄────────►│  Coach Agent  │
└──────────────┘           └──────────────┘           └──────────────┘
                                                              │
                                                              ▼
                                           ┌─────────────────────────────────┐
                                           │                                 │
                                      ┌────┴────┐                     ┌──────┴──────┐
                                      │ LLM API │                     │ Memory System│
                                      └─────────┘                     └──────────────┘
```

## 2. Core Components

### 2.1 LifeCoachAgent (`app/agents/life_coach_agent.py`)

The central component of the application, responsible for processing user input and generating coaching responses.

**Key Responsibilities:**
- Maintaining conversation state and history
- Processing user input and generating coaching responses
- Extracting and storing facts in memory
- Generating reflection questions
- Handling Google integration for calendar events and tasks

**Key Methods:**
- `provide_coaching(user_input)`: Processes user input and generates a coaching response
- `start_new_conversation()`: Initializes a new conversation with context from previous sessions
- `_generate_reflection_questions(user_input, coach_response)`: Generates personalized reflection questions
- `_process_memory_after_conversation()`: Extracts and stores facts from the conversation
- `get_memories(query)`: Retrieves relevant memories based on the query
- `add_explicit_memory(content)`: Adds an explicitly requested memory
- `_update_google_data()`: Updates calendar events and tasks from Google APIs
- `_try_create_task(user_message)`: Attempts to create a task based on the user message

### 2.2 Memory Manager (`app/utils/memory.py`)

Handles the extraction, storage, and retrieval of facts from conversations.

**Key Responsibilities:**
- Extracting facts from conversation history
- Storing facts in JSON files
- Retrieving relevant memories based on queries
- Managing explicit memory requests
- Providing conversation summaries for new sessions

**Key Methods:**
- `extract_facts(conversation_history)`: Extracts key facts from conversation history
- `store_facts(facts)`: Stores facts in memory
- `get_relevant_memories(query, limit)`: Retrieves memories relevant to a query
- `add_explicit_memory(content)`: Adds an explicitly requested memory
- `get_summary_for_new_conversation()`: Provides a summary of important memories for a new conversation

### 2.3 Web Routes (`app/web/routes.py`)

Handles HTTP requests and responses, serving as the interface between the frontend and the coach agent.

**Key Endpoints:**
- `/`: Renders the main chat interface
- `/api/chat`: Processes chat messages and returns responses
- `/api/reset`: Resets the conversation and starts a new one
- `/api/memories`: Gets or adds memories for the current conversation
- `/api/integration_status`: Gets the status of integrations
- `/api/google/auth_url`: Gets Google OAuth URL for authorization
- `/api/google/check_auth`: Checks if Google authorization is complete

### 2.4 LLM Integration (`app/models/llm.py`)

Manages communication with large language models (e.g., OpenAI, Ollama, Hugging Face).

**Key Responsibilities:**
- Creating and configuring LLM instances based on application settings
- Handling API calls to different LLM providers
- Managing model parameters (temperature, max tokens)

### 2.5 Configuration (`app/config/settings.py`)

Centralizes application configuration, loading settings from environment variables.

**Key Settings:**
- `LLM_MODEL`: The LLM provider to use (openai, ollama, huggingface)
- `MODEL_NAME`: The name of the model to use
- `TEMPERATURE`: The temperature parameter for the LLM
- `ENABLE_GOOGLE_INTEGRATION`: Whether Google integration is enabled
- `ENABLE_SPEECH`: Whether speech functionality is enabled
- `MEMORY_DIR`: Directory for storing memories

## 3. Control Flow

### 3.1 Conversation Flow

```
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌─────────────┐
│ Web Browser │───►│ Flask Routes  │───►│ LifeCoach   │───►│ LLM API       │───►│ Web Browser │
└─────────────┘    └───────────────┘    └───────────────┘    └───────────────┘    └─────────────┘
                                              │
                                              ▼
                                      ┌────────────────┐
                                      │ Memory Manager │
                                      └────────────────┘
```

1. User inputs a message through the web interface
2. The frontend sends a POST request to `/api/chat` with the message and conversation ID
3. The server routes the request to the appropriate handler in `routes.py`
4. The handler initializes or retrieves the LifeCoachAgent instance
5. The agent processes the message:
   - Checks for explicit memory requests
   - Checks for integration keywords (calendar, tasks)
   - Retrieves relevant memories and context
   - Prepares messages for the LLM
   - Calls the LLM to generate a response
   - Extracts and stores facts from the conversation
   - Generates reflection questions
6. The agent returns the response, insights, and any integration data
7. The server formats the response as JSON and sends it back to the frontend
8. The frontend displays the response to the user

### 3.2 Memory Extraction and Retrieval

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ User Input    │───►│ Extract Facts │───►│ Filter Facts  │───►│  Store Facts  │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
                                                                       │
                             ┌───────────────────────────────────────┐ │
                             │                                       │ │
                             ▼                                       │ ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Query Request │───►│ Score Memories│───►│  Sort Results │───►│ Return Results│
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

1. During conversation, the LifeCoachAgent extracts facts using `_process_memory_after_conversation()`
2. The MemoryManager processes the conversation history with `extract_facts()`
   - Extracts explicit memory requests
   - Identifies patterns for goals, challenges, preferences
   - Filters out similar or duplicate facts
3. New facts are stored in JSON files with `store_facts()`
4. When memories are requested, the MemoryManager:
   - Loads memories from the JSON file
   - If a query is provided, scores memories based on relevance
   - Returns the most relevant memories up to the limit

### 3.3 Speech Integration Flow

```
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ User Speech │───►│ Browser SpeechAPI │───►│ Speech Manager │───►│ Chat Interface │
└─────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Audio Output│◄───│ Speech Synthesis │◄──│ Speech Manager │◄──│ Agent Response│
└─────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

1. User speaks into the microphone
2. The SpeechManager captures the speech using the browser's SpeechRecognition API
3. The SpeechManager transcribes the speech to text
4. The transcript is sent to the chat interface for processing
5. The agent's response is sent back to the SpeechManager
6. The SpeechManager uses SpeechSynthesis to convert the text to speech
7. The speech is played back to the user

### 3.4 Google Integration Flow

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ User Request  │───►│ LifeCoach   │───►│ Google API    │───►│ Update State  │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

1. User mentions calendar events or tasks in their message
2. The LifeCoachAgent detects integration keywords
3. For calendar requests:
   - The agent calls `_update_google_data()` to retrieve events
   - Calendar events are included in the context for the LLM
4. For task creation:
   - The agent calls `_try_create_task()` to extract the task title
   - A new task is created via the Google Tasks API
   - The task is added to the agent's state

## 4. Data Flow

### 4.1 Conversation Data

- **User Input**: Text entered by the user through the web interface
- **Agent Messages**: History of user and assistant messages
- **Conversation ID**: Unique identifier for the conversation
- **Session State**: Current stage, turn count, quoted principles

### 4.2 Memory Data

- **Facts**: Key information extracted from conversations
- **Timestamps**: When each fact was stored
- **Sources**: Whether explicitly requested or extracted from conversation
- **Memory File**: JSON file with all memories for a conversation

### 4.3 Integration Data

- **Calendar Events**: User's upcoming events from Google Calendar
- **Tasks**: User's to-do items from Google Tasks
- **Integration Status**: Whether integrations are enabled and in use

## 5. Performance Considerations

### 5.1 Memory Optimization

- Facts are filtered for similarity to prevent redundant storage
- Memory retrieval is limited to prevent excessive processing
- Timeout mechanisms are used for memory operations
- Error handling prevents failures from disrupting the application

### 5.2 LLM Integration

- Direct communication with the LLM reduces latency
- System prompt provides comprehensive guidance in a single message
- Relevant context is included to improve response quality while minimizing token usage

### 5.3 Web Interface Optimizations

- Asynchronous operations prevent UI blocking
- Error handling with graceful degradation
- Resource-intensive operations run in background threads

## 6. Security Considerations

- User data is stored locally in JSON files
- No personal data is transmitted beyond necessary API calls
- Google integration requires explicit user authorization
- Error logging avoids exposing sensitive information

## 7. Future Enhancements

- Vector database for semantic memory search
- More sophisticated fact extraction using NLP
- Enhanced integration with Google and other services
- Offline mode with local LLM support
- Voice customization for speech synthesis

---

This architecture document provides a comprehensive overview of the Bahá'í Life Coach application's design and functionality. For specific implementation details, please refer to the corresponding source files. 