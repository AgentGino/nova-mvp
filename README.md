# Real-Time Voice Conversation with AWS Bedrock Nova Sonic [MVP]

This project demonstrates a real-time, bidirectional voice conversation with an AI assistant powered by the AWS Bedrock `amazon.nova-sonic-v1:0` model. It captures microphone audio, streams it to Bedrock, receives the transcribed text and generated audio response, and plays the audio back.

## Prerequisites

*   **Python:** Version 3.7 or higher.
*   **AWS Account:** An active AWS account.
*   **AWS CLI:** Installed and configured. ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
*   **PortAudio:** Required by the `PyAudio` library for audio I/O. Installation varies by OS:
    *   **macOS (using Homebrew):** `brew install portaudio`
    *   **Debian/Ubuntu:** `sudo apt-get install portaudio19-dev python3-pyaudio`
    *   **Windows:** Download binaries or use a package manager like Chocolatey (`choco install portaudio`). See [PyAudio documentation](https://people.csail.mit.edu/hubert/pyaudio/) for details.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/AgentGino/nova-mvp.git
    cd nova-mcp
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## AWS Configuration

### 1. Request Bedrock Model Access

*   Log in to the AWS Management Console.
*   Navigate to the **Amazon Bedrock** service.
*   In the bottom left corner, click on **Model access**.
*   Click the **Manage model access** button (top right).
*   Find **Nova models** -> **Sonic** in the list.
*   Select the checkbox next to `amazon.nova-sonic-v1:0`.
*   Click **Save changes** at the bottom.
*   Approval might take a few minutes.

### 2. Configure AWS CLI Profile

If you haven't already, configure an AWS CLI profile with credentials that have permissions to access Bedrock.

```bash
aws configure --profile <your-profile-name> 
# Example: aws configure --profile bedrock-user
```
Enter your AWS Access Key ID, Secret Access Key, default region (e.g., `us-east-1`), and default output format (e.g., `json`) when prompted.

## Application Configuration

1.  **Create `.env` File:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit `.env` File:**
    Open the `.env` file and modify the variables as needed:

    *   `AWS_PROFILE`: Set this to the AWS CLI profile name you configured (e.g., `bedrock-user`). If commented out or left as `default`, the default profile will be used.
    *   `AWS_DEFAULT_REGION`: (Optional) Your default AWS region.
    *   `BEDROCK_MODEL_ID`: Keep as `amazon.nova-sonic-v1:0` unless you intend to use a different (compatible) model.
    *   `BEDROCK_REGION`: The AWS region where you have Bedrock model access and want to run the inference (e.g., `us-east-1`).
    *   `BEDROCK_SYSTEM_PROMPT`: Customize the initial instruction given to the AI model.
    *   `BEDROCK_VOICE_ID`: Choose the desired voice for the AI's responses (e.g., `matthew`, `amy`, `tiffany` - refer to Bedrock documentation for available voices).
    *   `AWS_ACCESS_KEY_ID`: Access key are required for Bedrock service 
    *   `AWS_SECRET_ACCESS_KEY`: Secret key are required for Bedrock service

## Running the Application

1.  **Ensure your virtual environment is active:**
    ```bash
    source venv/bin/activate 
    ```

2.  **Run the main script:**
    ```bash
    python main.py
    ```

3.  **For detailed logging, use the debug flag:**
    ```bash
    python main.py --debug
    ```

4.  **Interact:**
    *   The application will initialize the audio streams and connect to Bedrock.
    *   Speak into your microphone.
    *   The AI will respond with generated audio.
    *   Press `Enter` in the terminal where the script is running to stop the application gracefully.

## License 
MIT