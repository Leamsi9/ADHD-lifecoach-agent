# Google Calendar and Tasks Integration

This document provides information about the Google Calendar and Tasks integration for the Bahai Life Coach agent.

## Overview

The Bahai Life Coach agent now supports integration with Google Calendar and Google Tasks to enhance the coaching experience. This integration allows the coach to:

1. View upcoming calendar events
2. View and manage tasks
3. Create new tasks based on coaching conversations

## Setup Instructions

### 1. Enable the Integration

To enable Google integration, set the `ENABLE_GOOGLE_INTEGRATION` environment variable to `True` in your `.env` file:

```
ENABLE_GOOGLE_INTEGRATION=True
```

### 2. Set up Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API and Google Tasks API
4. Configure the OAuth consent screen
5. Create OAuth 2.0 credentials (Desktop application)
6. Download the credentials as `credentials.json`
7. Place the `credentials.json` file in the root directory of the project (or specify a custom path in the `.env` file)

### 3. Configure API Scopes and Timezone

In your `.env` file, configure the following variables:

```
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_API_SCOPES=https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/tasks
GOOGLE_TIMEZONE=America/Los_Angeles
```

Adjust the timezone to match your location.

## Usage

Once integrated, the Bahai Life Coach agent will:

- Automatically check for calendar events when the user mentions calendar-related terms
- Retrieve task information when the user asks about tasks
- Create new tasks when the user makes a request like "add task to read scripture daily"

The web interface will display:

- An integration status badge showing whether Google integration is active
- Calendar events and tasks relevant to the conversation

## Troubleshooting

If you encounter issues with the Google integration:

1. Check that the credentials file exists and is correctly formatted
2. Verify that the API scopes are properly configured
3. Make sure you've completed the OAuth authorization flow
4. Check the application logs for specific error messages

## Privacy and Security

The Google integration accesses your Calendar and Tasks data only within the context of your coaching session. No data is stored on external servers. All processing happens locally within the application. 